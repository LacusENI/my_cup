# my_cup

一个用 **SystemVerilog** 从零手写的 **RISC-V RV32I 子集单周期 CPU**，
配有 cocotb + pytest 的统一验证流程。

> 设计目标：以"可读、可验证、可演进"的方式逐步从一个单周期内核走向流水线内核。
> 当前定位是 **教学 / 学习型实现**，重点在清晰的模块划分与可回归的测试。

---

## 当前状态

| 项 | 状态 |
| :-- | :-- |
| 当前基线 | `v0.4.0a2`（RV32I M2 SYSTEM / 停机语义） |
| 下一目标 | `v0.4.0`（完整 RV32I 单周期，见 [`docs/version/v0.4.0/plan.md`](docs/version/v0.4.0/plan.md)） |
| 微架构 | 单周期（组合数据通路 + 时序状态） |
| 指令集 | RV32I 子集（12 条） |
| 仿真器 | Icarus Verilog (`iverilog` + `vvp`) |
| 静态检查 | Verilator `--lint-only -Wall` |
| 测试 | 118 个 cocotb/pytest 用例 |
| CI | GitHub Actions：`code-gen-check` + `mycup lint` + `mycup test` |

### 已支持指令

| 类别 | 指令 |
| :-- | :-- |
| R 型 | `add` |
| 立即数 | `addi` |
| U 型 | `lui` `auipc` |
| 访存 | `lw` `sw` |
| 分支/跳转 | `beq` `jal` `jalr` |
| SYSTEM | `fence` `ecall` `ebreak` |

> `sub`、逻辑/移位/比较、子字访存 `lb/lh/sb/sh` 和其他分支
> 属于 `v0.4.0`，详见
> [`docs/version/v0.4.0/plan.md`](docs/version/v0.4.0/plan.md)。

> 伪指令由汇编器展开：`j -> jal x0`、`jr -> jalr x0`、`ret -> jalr x0, 0(ra)`、`nop -> addi x0, x0, 0`。

---

## 目录结构

```
my_cup/
├── mycup/                # Python 工具链
│   ├── cli.py                # mycup init / code-gen / build-programs / asm / lint / test / prog / fmt / doctor / clean
│   ├── config.py             # 读取 toolchain.toml
│   └── programs.py           # .S -> .o/.bin/.hex 与程序表
├── scripts/              # 代码生成与维护脚本
│   └── gen_pkg_consts.py     # 从 rtl/cpu_pkg.sv 生成测试常量
├── rtl/                  # 可综合的 RTL 源码
│   ├── cpu_top.sv            # 顶层：实例化各单元并连线
│   ├── cpu_pkg.sv            # package：参数、类型、控制编码
│   ├── control/              # 控制 / 取指 / 分支
│   │   ├── pc.sv
│   │   ├── npc.sv
│   │   ├── decoder.sv        # 字段 + imm_gen 函数 + opcode_err
│   │   ├── ctrl.sv
│   │   └── halt_unit.sv      # 停机原因仲裁
│   ├── datapath/             # 数据通路
│   │   ├── alu.sv
│   │   └── regfile.sv
│   └── memory/               # 存储器
│       ├── instm.sv
│       └── datam.sv
├── tests/                # 全部验证（cocotb + pytest）
│   ├── conftest.py            # session 级 build fixture
│   ├── utils/                 # cocotb_utils / assembler / cpu_pkg
│   ├── hdl/                   # test-only probes
│   ├── control/               # decoder / ctrl / npc
│   ├── datapath/              # alu / regfile
│   ├── memory/                # datam
│   └── cpu/                   # ISA / program 级测试
├── pyproject.toml        # uv 管理的 Python 依赖
├── uv.lock               # uv 的依赖锁定
├── docs/                 # 设计与文档（见 docs/README.md）
│   ├── roadmap.md            # 阶段路线
│   ├── version/v0.4.0/       # 当前目标版本计划
│   └── archive/              # 历史版本文档
├── .opencode/agents/     # OpenCode subagent 定义
├── .verilator/verilator.f # Verilator lint 文件清单（生成，不提交）
├── .slang/slang.f        # slang-server 文件清单（mycup init 生成）
├── .slang/server.json    # slang-server 工程配置
├── .vscode/settings.json # slang-server + verible 编辑器配置
├── programs/             # 汇编程序源文件 (*.S) 与用法说明
├── build/                # cocotb 构建产物；build/programs/ 保存 .o/.bin/.hex
├── waves/                # 生成的波形
└── logs/                 # lint 日志
```

---

## 快速开始

依赖：`iverilog` / `vvp` / `verilator` / `llvm-mc` / `llvm-objcopy` / `gtkwave`（可选，用于看波形）。

```bash
uv sync                              # 首次：创建 .venv

uv run mycup test                    # 先汇编程序，再运行全部测试
uv run mycup lint                    # Verilator 静态检查
uv run mycup prog programs/demo.S    # 汇编并运行 RV32I 程序
uv run mycup clean                   # 清理 build/ waves/ logs/ .verilator/ 等

make programs                        # 汇编 programs/**/*.S
make code-gen                        # 按 toolchain.toml 运行代码生成器

uv run pytest -v tests/cpu/test_inst.py               # 单个文件
uv run pytest -v tests/cpu/test_inst.py::test_add    # 单个用例
MYCUP_WAVES=1 uv run pytest -v tests/cpu/test_inst.py # 导出波形
```

> 直接运行 `pytest` 时，请先执行 `make programs` 或 `mycup build-programs`；
> `mycup test` 会自动完成这一步。

> 验证说明：
> - `tests/<category>/test_*.py` 同时包含 cocotb 测试和 pytest 入口；
>   `@cocotb_test` 装饰器负责把两者连接起来；
> - 目录按 RTL 职责划分：`control/`、`datapath/`、`memory/`、`cpu/`；
> - 通用工具在 `tests/utils/`；
> - 新增测试只要在对应 `test_*.py` 里写一个 async 函数，不需要注册；
> - 详见 [`tests/README.md`](tests/README.md)。

---

## Lint

若要进行项目 lint，运行：

```bash
uv run mycup lint
```

本项目的 lint 使用 Verilator，文件清单 `.verilator/verilator.f`，
由 `mycup init` / `mycup lint` 自动生成。

---

## 编辑器工具链（slang + verible）

项目推荐使用 SystemVerilog LSP：`slang-server` 和自动格式化工具：`verible`。

| 工具 | 用途 | 位置 |
| :-- | :-- | :-- |
| **slang-server** | 语义 LSP：hover / 定义 / 补全 / 符号 / 诊断 | `~/.local/bin/slang-server` |
| **Hudson-River-Trading.vscode-slang** | VS Code 的 slang 客户端 | VS Code 扩展 |
| **verible** | `verible-verilog-format` 格式化 | `~/.local/bin/verible-*` |
| **Verilator** | CLI lint | 系统包 |
| **Icarus Verilog** | cocotb 仿真 | 系统包 |

### 配置

- 编辑器：[`.vscode/settings.json`](.vscode/settings.json)
  - `slang.path`: 默认 `slang-server`，不在 `PATH` 时改成绝对路径；
  - `slang.formatters`: 调用 `verible-verilog-format`；
  - `files.associations`: `.sv` / `.svh` → `systemverilog`。
- 项目：[`.slang/server.json`](.slang/server.json)
  - 索引 `rtl`；
  - 构建文件清单为 [`.slang/slang.f`](.slang/slang.f)。
- 文件清单：`.slang/slang.f` 由 `mycup init` 同时生成，**不要手工维护**。
  ```bash
  uv run mycup init
  # 生成 .verilator/verilator.f + .slang/slang.f
  ```

### 用法

1. 重新加载 VS Code 窗口：
   ```text
   Ctrl+Shift+P -> Developer: Reload Window
   ```
2. 打开项目文件夹。
3. 打开 `rtl/cpu_top.sv`，执行：
   ```text
   slang: Set Top Level
   ```
   选择 `cpu_top`。
4. hover `word_t` / `ctrl_t`，F12 应该跳到 `rtl/cpu_pkg.sv`。
5. 手动格式化：
   ```text
   Shift+Alt+F
   ```

如果语言服务没启动：

- 查看 VS Code 输出面板的 `slang-server`；
- 执行 `slang: Restart Language Server`；
- 确认 `slang-server` 在 `PATH`，或在 `.vscode/settings.json` 里写绝对路径。

### 换机器时如何安装

```bash
# VS Code 扩展
code --install-extension Hudson-River-Trading.vscode-slang

# verible（GitHub release）
#   https://github.com/chipsalliance/verible/releases
#   解压后把 verible-verilog-format 放到 ~/.local/bin

# slang-server（GitHub release）
#   https://github.com/hudson-trading/slang-server/releases
#   下载 slang-server-linux-x64.tar.gz，解压后：
install -m 0755 slang-server ~/.local/bin/slang-server

# Python 工具
uv sync
```

> `slang-server` 和 VS Code 扩展缺一不可。只有扩展、没有 server 时，
> 编辑器看起来会“没有任何语言服务”。

---

## OpenCode subagents

项目在 `.opencode/agents/` 下定义了四个 subagent，用来把“设计”和“落地”分开：

| Agent | 用途 | 权限 |
| :-- | :-- | :-- |
| `implementer` | 按明确任务改 RTL/测试/文档，跑 lint/test | 可编辑，不能 commit/push |
| `rtl-reviewer` | 只读审查 RTL/测试/文档改动 | 只读 |
| `verifier` | 只跑 lint/test，报告失败 | 只读 |
| `doc-checker` | 检查文档链接、路径、命令、状态一致性 | 只读 |

建议工作流：

```text
主会话（架构/设计/文档）
  -> implementer 做局部编码
  -> rtl-reviewer / verifier / doc-checker 做独立检查
  -> 主会话决定是否合并/提交
```

`implementer` 不会替你做架构决策；如果任务需要改公共接口或 ISA 语义，它应该停下来报告。

---

## 文档导航

- **[docs/README.md](docs/README.md)** —— 文档总索引与各文档的时效性标注
- **[docs/arch/architecture.md](docs/arch/architecture.md)** —— 整体框架、数据通路、模块职责、已知限制
- **[docs/roadmap.md](docs/roadmap.md)** —— 阶段路线与当前目标
- **[docs/version/v0.4.0/plan.md](docs/version/v0.4.0/plan.md)** —— `v0.4.0` 批次、任务与完成标准
- `docs/units/` —— 当前 RV32I 单元接口说明
- `docs/archive/` —— 历史版本文档

---

## 设计约定

- **字节序**：当前只做整字访问；后续子字访存按小端序实现。
- **语言风格**：SystemVerilog。共享常量/函数放在 `cpu_pkg.sv`，模块用 `import cpu_pkg::*;`，不使用 `include` 头文件。
- **位宽/深度**：用 `cpu_pkg.sv` 的 `word_t` / `XLEN` / `IMEM_WORDS` / `DMEM_WORDS` 参数化，不写死 32 或 2048。
- **组合/时序**：单驱动信号用 `logic`；组合逻辑用 `always_comb`；时序逻辑用 `always_ff`；`case` 优先用 `unique case`，并显式给默认值（避免 `x`）。
- **隐式网络**：每个 RTL 文件用 `` `default_nettype none `` / `` `default_nettype wire `` 包住，拼错信号名会直接报错。
- **互联方式**：单元模块通过显式端口互联；顶层 `cpu_top` 也使用显式命名连接。
- **提交信息**：采用 `<type>(<scope>): <desc>` 形式（`feat` / `fix` / `refactor` / `test` / `doc` / `chore`）。
- **分支**：`master` 为主干，特性在主题分支上开发后合并。

---

## 下一步

短期目标是 **`v0.4.0` 完整 RV32I 单周期**；之后进入 **`v0.5.0` 简单流水线**，
再逐步增加 forwarding 和分支预测。

当前主线计划见 **[docs/roadmap.md](docs/roadmap.md)** 和
**[docs/version/v0.4.0/plan.md](docs/version/v0.4.0/plan.md)**；
`v0.5.0` 之后的流水线内容，完成 `v0.4.0` 后再议。
