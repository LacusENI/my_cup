#!/usr/bin/env python3
"""veridian LSP 代理。

背景：veridian 内置的 slang/verible 诊断不接收 include/package 路径，
对多文件工程（例如 cpu_pkg.sv + 各模块）会产生误报；且 `didSave` 会触发一次全量
slang 编译，可能长时间阻塞。

本代理做三件事：
  1. 丢弃 client -> server 的 `textDocument/didSave`
  2. 丢弃 server -> client 的 `textDocument/publishDiagnostics`
  3. 修正 `documentSymbol` 响应里 `selectionRange` 不包含于 `range` 的 veridian
     bug（VSCode 客户端会拒绝这种响应，报
     "selectionRange must be contained in fullRange"）

导航（hover / definition / documentSymbol / completion / format）不受影响；
诊断统一由项目 Verilator（mycup lint / IDE lint）负责。

用法：把本脚本放到 PATH 中（如 ~/.local/bin/veridian-lsp），
并让真实 veridian 可执行文件以 `veridian-real` 的名字在 PATH 中
（或通过环境变量 VERIDIAN_BIN 指定）。
"""

import json
import os
import subprocess
import sys
import threading

REAL = os.environ.get("VERIDIAN_BIN", "veridian-real")
DEBUG = os.environ.get("VERIDIAN_LSP_DEBUG") == "1"


def dbg(*args):
    if DEBUG:
        print("veridian-lsp:", *args, file=sys.stderr, flush=True)


def read_message(stream):
    headers = {}
    while True:
        line = stream.readline()
        if not line:
            return None
        if line in (b"\r\n", b"\n"):
            break
        key, _, value = line.decode("ascii", "replace").partition(":")
        headers[key.strip().lower()] = value.strip()
    length = int(headers.get("content-length", 0))
    if length <= 0:
        return None
    body = stream.read(length)
    if not body:
        return None
    return headers, body


def write_message(stream, body):
    stream.write(b"Content-Length: %d\r\n\r\n" % len(body) + body)
    stream.flush()


def method_of(body):
    try:
        return json.loads(body).get("method")
    except Exception:
        return None


def _pos_key(pos):
    """LSP Position -> 可比较的元组；缺字段时按 0 处理。"""
    if not isinstance(pos, dict):
        return None
    return (int(pos.get("line", 0)), int(pos.get("character", 0)))


def _sanitize_ranges(node):
    """递归修正 DocumentSymbol 的 range / selectionRange 包含关系。

    veridian 对 enum/struct/typedef 生成的 range 有时会在声明最后一行提前结束，
    而 selectionRange 指向 typedef 名字，导致 selectionRange 超出 range。
    这里只做“扩大 range 以包住 selectionRange”，不改 symbol 的层级和名字。
    """
    changed = False
    if isinstance(node, list):
        for item in node:
            changed = _sanitize_ranges(item) or changed
        return changed

    if not isinstance(node, dict):
        return False

    rng = node.get("range")
    sel = node.get("selectionRange")
    if isinstance(rng, dict) and isinstance(sel, dict):
        rs, re = rng.get("start"), rng.get("end")
        ss, se = sel.get("start"), sel.get("end")
        rk, rek, ssk, sek = _pos_key(rs), _pos_key(re), _pos_key(ss), _pos_key(se)
        if rk is not None and rek is not None and ssk is not None and sek is not None:
            new_start = min(rk, ssk)
            new_end = max(rek, sek)
            if new_start != rk or new_end != rek:
                rng["start"] = {"line": new_start[0], "character": new_start[1]}
                rng["end"] = {"line": new_end[0], "character": new_end[1]}
                changed = True

    for key in ("children", "result", "contents"):
        if key in node:
            changed = _sanitize_ranges(node[key]) or changed
    return changed


def sanitize_body(body):
    """如果 JSON-RPC body 里含非法 DocumentSymbol range，就地修正后重新编码。"""
    try:
        obj = json.loads(body)
    except Exception:
        return body

    if not _sanitize_ranges(obj):
        return body

    dbg("sanitized documentSymbol ranges")
    return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def pump_client(proc):
    while True:
        msg = read_message(sys.stdin.buffer)
        if msg is None:
            break
        _, body = msg
        dbg("client ->", method_of(body) or body[:40])
        if method_of(body) == "textDocument/didSave":
            continue  # 丢弃：避免触发全量 slang 编译
        try:
            write_message(proc.stdin, body)
        except (BrokenPipeError, ValueError):
            break
    try:
        proc.stdin.close()
    except Exception:
        pass


def pump_server(proc):
    while True:
        msg = read_message(proc.stdout)
        if msg is None:
            break
        _, body = msg
        dbg("server ->", method_of(body) or body[:40])
        if method_of(body) == "textDocument/publishDiagnostics":
            continue  # 丢弃：veridian 的诊断不含 include 路径
        try:
            write_message(sys.stdout.buffer, sanitize_body(body))
        except (BrokenPipeError, ValueError):
            break


def main():
    try:
        proc = subprocess.Popen(
            [REAL],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=None,  # 继承，日志进入扩展的 Output 通道
        )
    except FileNotFoundError:
        sys.stderr.write(f"veridian-lsp: cannot find '{REAL}'\n")
        return 127

    server = threading.Thread(target=pump_server, args=(proc,), daemon=True)
    server.start()
    pump_client(proc)
    server.join(timeout=2)
    proc.terminate()
    try:
        proc.wait(timeout=2)
    except subprocess.TimeoutExpired:
        proc.kill()
    return 0


if __name__ == "__main__":
    sys.exit(main())
