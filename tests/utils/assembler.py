"""用 LLVM MC 把 RISC-V 汇编文本编码成机器码。

这里只服务测试：一次只接受一条 32 位指令，避免伪指令被展开成多条后
悄悄改变测试语义。实现依赖 ``llvm-mc`` 的 ``# encoding: [...]`` 输出；
不同 LLVM 版本可能调整显示格式，因此这里只解析这一小段。
"""

from __future__ import annotations

import re
import shutil
import subprocess
from functools import lru_cache

_LLVM_MC = "llvm-mc"
_ENCODING_RE = re.compile(r"# encoding: \[([^\]]+)\]")


@lru_cache(maxsize=None)
def assemble(text: str) -> int:
    """把单条 RISC-V 汇编指令编码成 32 位机器码。

    例如::

        assemble("add x3, x1, x2")
        assemble("lw x2, -4(x1)")
    """
    text = text.strip()
    if not text:
        raise ValueError("汇编文本不能为空")

    if shutil.which(_LLVM_MC) is None:
        raise RuntimeError(
            "找不到 llvm-mc；请安装 LLVM，并把 llvm-mc 加入 PATH"
        )

    proc = subprocess.run(
        [_LLVM_MC, "-triple=riscv32", "-show-encoding"],
        input=text + "\n",
        text=True,
        capture_output=True,
    )
    if proc.returncode != 0:
        message = proc.stderr.strip() or proc.stdout.strip()
        raise ValueError(f"无法汇编 {text!r}: {message}")

    encodings = _ENCODING_RE.findall(proc.stdout)
    if len(encodings) != 1:
        raise ValueError(
            f"{text!r} 不是单条 32 位指令"
            f"（llvm-mc 输出 {len(encodings)} 条编码）"
        )

    data = bytes(int(item.strip(), 16) for item in encodings[0].split(","))
    if len(data) != 4:
        raise ValueError(f"{text!r} 编码长度是 {len(data)} 字节，不是 4 字节")

    return int.from_bytes(data, "little")
