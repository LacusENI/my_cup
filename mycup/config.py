"""读取项目根目录的 ``toolchain.toml``。

原则：配置文件只描述“路径、工具、参数”，具体流程仍由 ``mycup`` 和
``Makefile`` 执行。这样改工具链时不需要翻 Python 代码。
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class ConfigError(Exception):
    """toolchain.toml 缺失或字段不合法。"""


@dataclass(frozen=True)
class Paths:
    root: Path
    rtl: Path
    build: Path
    waves: Path
    logs: Path
    verilator_dir: Path
    slang_dir: Path
    programs: Path
    tests: Path


@dataclass(frozen=True)
class Sources:
    package: Path
    glob: str


@dataclass(frozen=True)
class Lint:
    tool: str
    args: tuple[str, ...]
    filelist: Path
    log: Path


@dataclass(frozen=True)
class Slang:
    filelist: Path


@dataclass(frozen=True)
class Test:
    args: tuple[str, ...]


@dataclass(frozen=True)
class Prog:
    target: str


@dataclass(frozen=True)
class Format:
    tool: str
    args: tuple[str, ...]
    glob: str


@dataclass(frozen=True)
class Doctor:
    required: tuple[str, ...]
    optional: tuple[str, ...]


@dataclass(frozen=True)
class Toolchain:
    name: str
    paths: Paths
    sources: Sources
    lint: Lint
    slang: Slang
    test: Test
    prog: Prog
    format: Format
    doctor: Doctor


def _section(data: dict[str, Any], name: str) -> dict[str, Any]:
    value = data.get(name)
    if not isinstance(value, dict):
        raise ConfigError(f"toolchain.toml 缺少 [{name}] 表")
    return value


def _str(table: dict[str, Any], name: str, section: str) -> str:
    value = table.get(name)
    if not isinstance(value, str) or not value:
        raise ConfigError(f"toolchain.toml: [{section}] {name} 必须是非空字符串")
    return value


def _str_list(
    table: dict[str, Any], name: str, section: str, *, default: tuple[str, ...] = ()
) -> tuple[str, ...]:
    value = table.get(name, list(default))
    if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
        raise ConfigError(f"toolchain.toml: [{section}] {name} 必须是字符串数组")
    return tuple(value)


def _resolve(root: Path, value: str) -> Path:
    return root / value


def load(root: Path) -> Toolchain:
    """从 ``root/toolchain.toml`` 读取配置，路径全部转为绝对路径。"""
    config_path = root / "toolchain.toml"
    if not config_path.is_file():
        raise ConfigError(f"找不到 {config_path}")

    try:
        data = tomllib.loads(config_path.read_text(encoding="utf-8"))
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"toolchain.toml 解析失败: {exc}") from exc

    project = data.get("project", {})
    if not isinstance(project, dict):
        raise ConfigError("toolchain.toml: [project] 必须是表")
    name = project.get("name", root.name)
    if not isinstance(name, str) or not name:
        raise ConfigError("toolchain.toml: [project] name 必须是非空字符串")

    paths_table = _section(data, "paths")
    paths = Paths(
        root=root,
        rtl=_resolve(root, _str(paths_table, "rtl", "paths")),
        build=_resolve(root, _str(paths_table, "build", "paths")),
        waves=_resolve(root, _str(paths_table, "waves", "paths")),
        logs=_resolve(root, _str(paths_table, "logs", "paths")),
        verilator_dir=_resolve(root, _str(paths_table, "verilator_dir", "paths")),
        slang_dir=_resolve(root, _str(paths_table, "slang_dir", "paths")),
        programs=_resolve(root, _str(paths_table, "programs", "paths")),
        tests=_resolve(root, _str(paths_table, "tests", "paths")),
    )

    sources_table = _section(data, "sources")
    sources = Sources(
        package=_resolve(root, _str(sources_table, "package", "sources")),
        glob=_str(sources_table, "glob", "sources"),
    )

    lint_table = _section(data, "lint")
    lint = Lint(
        tool=_str(lint_table, "tool", "lint"),
        args=_str_list(lint_table, "args", "lint"),
        filelist=_resolve(root, _str(lint_table, "filelist", "lint")),
        log=_resolve(root, _str(lint_table, "log", "lint")),
    )

    slang_table = _section(data, "slang")
    slang = Slang(filelist=_resolve(root, _str(slang_table, "filelist", "slang")))

    test_table = _section(data, "test")
    test = Test(args=_str_list(test_table, "args", "test"))

    prog_table = _section(data, "prog")
    prog = Prog(target=_str(prog_table, "target", "prog"))

    format_table = _section(data, "format")
    format_cfg = Format(
        tool=_str(format_table, "tool", "format"),
        args=_str_list(format_table, "args", "format"),
        glob=_str(format_table, "glob", "format"),
    )

    doctor_table = _section(data, "doctor")
    doctor = Doctor(
        required=_str_list(doctor_table, "required", "doctor"),
        optional=_str_list(doctor_table, "optional", "doctor"),
    )

    return Toolchain(
        name=name,
        paths=paths,
        sources=sources,
        lint=lint,
        slang=slang,
        test=test,
        prog=prog,
        format=format_cfg,
        doctor=doctor,
    )
