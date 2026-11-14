# 工具链配置

项目的工具链分三层：

```text
toolchain.toml   数据和参数：路径、工具、lint flags、测试参数
Makefile         常用命令：make lint / make test / make prog ...
mycup            实际执行：生成文件清单、调用工具
```

改路径或工具参数时，先看 `toolchain.toml`；通常不需要改 Python。

---

## `toolchain.toml`

### `[paths]`

所有路径都相对于项目根目录。

| 字段 | 默认值 | 用途 |
| :-- | :-- | :-- |
| `rtl` | `rtl` | RTL 源文件目录 |
| `build` | `build` | cocotb / Verilator 构建产物 |
| `waves` | `waves` | 波形 |
| `logs` | `logs` | 测试和 lint 日志 |
| `verilator_dir` | `.verilator` | Verilator 文件清单（生成，不提交） |
| `slang_dir` | `.slang` | slang-server 配置和文件清单 |
| `programs` | `programs` | 测试程序 hex |
| `tests` | `tests` | pytest / cocotb 测试 |

### `[sources]`

| 字段 | 用途 |
| :-- | :-- |
| `package` | SystemVerilog package 文件，必须排在编译文件列表最前面 |
| `glob` | 格式化时匹配的 RTL 文件 |

### `[[codegen]]`

每一项描述一个代码生成器：

| 字段 | 用途 |
| :-- | :-- |
| `name` | 生成器名称，用于日志 |
| `source` | 生成来源文件 |
| `script` | 生成脚本 |
| `target` | 生成目标文件 |

`mycup code-gen` 会执行：

```bash
python <script> --source <source> --output <target>
```

`mycup code-gen --check` 会额外传 `--check`，只检查目标是否最新。

### `[lint]`

| 字段 | 用途 |
| :-- | :-- |
| `tool` | lint 工具，当前为 `verilator` |
| `args` | 写入文件清单的 Verilator flags |
| `filelist` | 生成的文件清单路径 |
| `log` | lint 日志路径 |

### `[slang]`

`filelist` 是 slang-server 读取的纯文件列表，不带 flags。

### `[test]`

`args` 会传给 `python -m pytest`。`mycup prog` 也复用这些参数。

### `[prog]`

`target` 是 `mycup prog` 运行的 pytest 测试节点。

### `[format]`

| 字段 | 用途 |
| :-- | :-- |
| `tool` | 格式化工具，当前为 `verible-verilog-format` |
| `args` | 格式化参数 |
| `glob` | 要格式化的文件 |

`mycup fmt` 会额外追加 `--inplace`，原地修改文件。

### `[doctor]`

`required` 缺失时 `make doctor` 返回非零；`optional` 只警告。
默认检查 `uv`、`iverilog`、`verilator`、`verible-verilog-format`、`llvm-mc`，
并提示可选的 `slang-server`。`llvm-mc` 用于把测试里的汇编文本编码成机器码。

---

## Makefile

| 命令 | 作用 |
| :-- | :-- |
| `make init` | 生成 `.verilator/verilator.f` 和 `.slang/slang.f` |
| `make code-gen` | 按 `toolchain.toml` 运行代码生成器 |
| `make code-gen-check` | 检查生成文件是否最新 |
| `make lint` | 生成文件清单并运行 Verilator |
| `make test` | 运行全部 cocotb + pytest |
| `make check` | `lint` + `test` |
| `make fmt` | 格式化 RTL（原地修改） |
| `make prog FILE=...` | 运行指定 hex 程序 |
| `make doctor` | 检查配置和工具 |
| `make clean` | 清理生成物 |

`prog` 示例：

```bash
make prog FILE=programs/demo.hex
make prog FILE=programs/demo.hex DATA=programs/data.hex CYCLES=8
```

---

## 和编辑器的关系

- `.vscode/settings.json` 仍然负责 VS Code 的 slang 配置；
- `.slang/server.json` 负责 slang-server 的索引和构建文件；
- `.slang/slang.f` 由 `make init` / `make lint` 生成并提交，保证 clone 后 LSP 能直接工作；
- `.verilator/verilator.f` 是本地生成物，已在 `.gitignore` 中忽略。

编辑器侧不内嵌 Verilator lint；命令行 `make lint` 是唯一 lint 入口。
