# 工具链配置

项目的工具链分三层：

```text
toolchain.toml   数据和参数：路径、工具、lint flags、测试参数
Makefile         常用命令：make lint / make test / make cov / make prog ...
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

### `[cov]`

| 字段 | 用途 |
| :-- | :-- |
| `dir` | 覆盖率输出目录，默认 `logs/coverage` |
| `min_version` | 最低 Verilator 版本，默认 `5.054` |
| `verilator` | 项目本地 Verilator 路径 |
| `verilator_coverage` | 项目本地 verilator_coverage 路径 |

`mycup cov` 会设置 `MYCUP_SIM=verilator` 和 `MYCUP_COVERAGE=1` 跑全部测试，
然后把每个测试的 `coverage.dat` 汇总成注释源码和 lcov `.info`。
它会优先使用 `[cov]` 指定的本地工具，并把对应目录加入子进程 `PATH`；
本地工具不存在时才回退到系统 `PATH`。

Ubuntu 24.04 自带的 Verilator 5.020 不能配合 cocotb 2.1 的 Verilator runner。
一次性安装项目本地版本：

```bash
make install-verilator
```

脚本默认构建 `5.054` 到 `.tools/verilator/5.054/`，不会覆盖系统 Verilator。

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
默认检查 `uv`、`iverilog`、`verilator`、`verible-verilog-format`，
并提示可选的 `slang-server`、`verilator_coverage`、`genhtml`。

---

## Makefile

| 命令 | 作用 |
| :-- | :-- |
| `make init` | 生成 `.verilator/verilator.f` 和 `.slang/slang.f` |
| `make lint` | 生成文件清单并运行 Verilator |
| `make test` | 运行全部 cocotb + pytest |
| `make check` | `lint` + `test` |
| `make fmt` | 格式化 RTL（原地修改） |
| `make cov` | 用 Verilator 跑测试并生成覆盖率 |
| `make install-verilator` | 构建项目本地 Verilator（覆盖率用） |
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
