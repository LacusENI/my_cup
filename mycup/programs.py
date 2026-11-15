"""RISC-V 汇编程序构建工具。

程序源文件（``programs/**/*.S``）是接口；``.o`` / ``.bin`` / ``.hex``
都是 ``build/programs/`` 下的中间产物。

当前流程不依赖 linker，适用于单个 ``.text`` 段：
    llvm-mc -> .o -> llvm-objcopy -> .bin -> .hex
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path

from mycup.config import ConfigError, Toolchain, load

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class BuiltProgram:
    source: Path
    obj: Path
    bin: Path
    hex: Path


def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _source_relative(source: Path, root: Path) -> Path:
    programs_dir = root / "programs"
    try:
        return source.relative_to(programs_dir)
    except ValueError:
        return Path(source.name)


def _output_paths(
    cfg: Toolchain, source: Path, root: Path
) -> tuple[Path, Path, Path]:
    relative = _source_relative(source, root)
    base = cfg.assemble.output_dir / relative.with_suffix("")
    return (
        base.with_suffix(".o"),
        base.with_suffix(".bin"),
        base.with_suffix(".hex"),
    )


def _run(cmd: list[str], root: Path) -> None:
    proc = subprocess.run(
        cmd,
        cwd=root,
        capture_output=True,
        text=True,
    )
    if proc.returncode != 0:
        message = proc.stderr.strip() or proc.stdout.strip()
        raise RuntimeError(
            f"命令失败（退出码 {proc.returncode}）: {' '.join(cmd)}\n{message}"
        )


def bin_to_hex(data: bytes) -> str:
    """把 RISC-V 小端二进制转换成 $readmemh 使用的 32 位字。"""
    if len(data) % 4 != 0:
        raise ValueError(
            f"二进制长度 {len(data)} 不是 4 字节的倍数，无法生成 32 位 hex"
        )
    return "\n".join(
        f"{int.from_bytes(data[offset : offset + 4], 'little'):08x}"
        for offset in range(0, len(data), 4)
    ) + ("\n" if data else "")


def build_program(
    cfg: Toolchain,
    source: str | Path,
    *,
    root: Path = ROOT,
    output_hex: str | Path | None = None,
) -> BuiltProgram:
    """汇编一个 .S，返回生成文件路径。"""
    source_path = Path(source)
    if not source_path.is_absolute():
        source_path = root / source_path
    source_path = source_path.resolve()
    if not source_path.is_file():
        raise FileNotFoundError(f"程序源文件不存在: {source_path}")
    if source_path.suffix.lower() != ".s":
        raise ValueError(f"不是汇编源文件: {source_path}")

    obj_path, bin_path, default_hex = _output_paths(
        cfg, source_path, root
    )
    for path in (obj_path, bin_path, default_hex):
        path.parent.mkdir(parents=True, exist_ok=True)

    _run(
        [
            cfg.assemble.assembler,
            f"-triple={cfg.assemble.triple}",
            f"-mattr={cfg.assemble.mattr}",
            "-filetype=obj",
            "-o",
            str(obj_path),
            str(source_path),
        ],
        root,
    )
    _run(
        [
            cfg.assemble.objcopy,
            "-O",
            "binary",
            "--only-section=.text",
            str(obj_path),
            str(bin_path),
        ],
        root,
    )

    hex_path = Path(output_hex).resolve() if output_hex else default_hex
    hex_path.parent.mkdir(parents=True, exist_ok=True)
    hex_path.write_text(bin_to_hex(bin_path.read_bytes()), encoding="utf-8")
    return BuiltProgram(
        source=source_path,
        obj=obj_path,
        bin=bin_path,
        hex=hex_path,
    )


def build_all_programs(
    cfg: Toolchain,
    *,
    root: Path = ROOT,
) -> dict[str, dict[str, str]]:
    """构建 programs/**/*.S，并写入 programs.json。"""
    sources = sorted(root.glob(cfg.assemble.source_glob))
    table_path = cfg.assemble.table
    table_path.parent.mkdir(parents=True, exist_ok=True)
    table_path.unlink(missing_ok=True)

    table: dict[str, dict[str, str]] = {}
    for source in sources:
        if not source.is_file() or source.suffix.lower() != ".s":
            continue
        print(f"[asm] {_rel(source, root)}")
        built = build_program(cfg, source, root=root)
        key = _rel(built.source, root)
        table[key] = {
            "source": key,
            "obj": _rel(built.obj, root),
            "bin": _rel(built.bin, root),
            "hex": _rel(built.hex, root),
        }

    table_path.write_text(
        json.dumps(table, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"[asm] 生成 {_rel(table_path, root)}（{len(table)} 个程序）")
    return table


def resolve_program(
    program: str | Path,
    *,
    cfg: Toolchain | None = None,
    root: Path = ROOT,
) -> Path:
    """把 .hex 或 .S 解析成可直接交给仿真的 hex 路径。"""
    if cfg is None:
        cfg = load(root)

    requested = Path(program)
    path = requested if requested.is_absolute() else root / requested
    path = path.resolve()

    if path.suffix.lower() == ".hex":
        if not path.is_file():
            raise FileNotFoundError(f"hex 文件不存在: {path}")
        return path

    if path.suffix.lower() != ".s":
        raise ValueError(f"只支持 .S 或 .hex 程序: {path}")

    table_path = cfg.assemble.table
    if table_path.is_file():
        try:
            table = json.loads(table_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ConfigError(f"程序表解析失败: {table_path}: {exc}") from exc
        key = _rel(path, root)
        entry = table.get(key)
        if entry and isinstance(entry.get("hex"), str):
            hex_path = (root / entry["hex"]).resolve()
            if hex_path.is_file():
                return hex_path

    # 同名约定作为兜底。
    fallback = _output_paths(cfg, path, root)[2]
    if fallback.is_file():
        return fallback.resolve()

    raise FileNotFoundError(
        f"程序尚未构建: {path}\n先运行: make programs 或 mycup build-programs"
    )
