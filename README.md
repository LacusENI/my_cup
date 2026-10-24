# my_cup

一个用 Verilog (IEEE 1364-2012) 从零手写的 **MIPS32 指令集子集单周期 CPU**，
配有统一的仿真测试框架与可自动生成的构建流程。

> 设计目标：以"可读、可验证、可演进"的方式逐步从一个单周期内核走向流水线内核。
> 当前定位是 **教学 / 学习型实现**，重点在清晰的模块划分与可回归的测试。

---

## 当前状态

| 项 | 状态 |
| :-- | :-- |
| 版本 | `v0.3`（见 `docs/instr/`） |
| 微架构 | 单周期（组合数据通路 + 时序状态） |
| 指令集 | MIPS32 子集 |
| 仿真器 | Icarus Verilog (`iverilog` + `vvp`) |
| 静态检查 | Verilator `--lint-only -Wall` |
| 测试 | 14 个 testbench（单元 + 指令级），当前全部通过 |

### 已支持指令（最小集，已冻结）

| 类别 | 指令 |
| :-- | :-- |
| R 型 | `addu` `jr` |
| 立即数 | `addiu` |
| 访存 | `lw` `sw` |
| 分支/跳转 | `beq` `j` `jal` |

> 当前 ISA 已冻结为最小集。`sb/sh` 与 `lb/lbu/lh/lhu` 作为**子字访问整体延后**
> （涉及端序、字节掩码 `wstrb`、DM 控制器），详见 [路线图](docs/roadmap.md#明确延后deferred)。

---

## 目录结构

```
my_cup/
├── mycup/                # Python 工具链（`uv run mycup ...`）
│   └── cli.py
├── scripts/
│   └── veridian-lsp.py   # veridian LSP 代理
├── rtl/                  # 可综合的 RTL 源码
│   └── core/
│       ├── cpu_top.v          # 顶层：实例化各单元并连线
│       ├── include/           # 宏与函数定义
│       │   ├── defines.vh         # 控制信号编码、opcode/funct
│       │   ├── instr.vh           # 指令 opcode 占位声明
│       │   └── ext.vh             # 位宽扩展函数
│       └── units/             # 各功能单元
│           ├── pc.v / npc.v       # 程序计数器 / 下一 PC 逻辑
│           ├── instrm.v           # 指令存储器 (IMEM)
│           ├── decoder.v          # 指令字段拆分
│           ├── ctrl.v             # 控制器（产生全部控制信号）
│           ├── regfile.v          # 通用寄存器堆
│           ├── ext.v              # 立即数扩展
│           ├── alu.v              # 算术逻辑单元
│           ├── cond.v             # 条件判断（分支）
│           └── datam.v            # 数据存储器 (DMEM)
├── sim/
│   └── tb/               # 测试平台（旧 HDL 流程）
│       ├── unit/              # 单元级 testbench
│       └── instr/             # 指令级 testbench（驱动整个 cpu_top）
├── tests/                # Python 验证 PoC（cocotb + pytest，与旧流程并存）
│   ├── conftest.py            # session 级 build fixture
│   ├── tb_*.py                # cocotb 测试模块
│   └── test_*.py              # pytest 包装
├── pyproject.toml        # uv 管理的 Python 依赖（cocotb / pytest）
├── uv.lock               # 依赖锁定
├── lib/                  # 通用库
│   └── vtest.vh               # 旧 HDL 测试框架（宏：TEST / EXPECT / ...）
├── docs/                 # 设计与文档（见 docs/README.md）
├── verilator.f           # Verilator lint 文件清单（mycup lint 与 IDE 共用）
├── .vscode/settings.json # IDE lint 配置（与项目 lint 对齐）
├── programs/             # 仿真用机器码程序 (*.hex) 与用法说明
├── build/                # 生成物：filelists / targets / cocotb (gitignore)
├── waves/                # 生成的 VCD 波形 (gitignore)
└── logs/                 # 构建与 lint 日志 (gitignore)
```

---

## 快速开始

依赖：`iverilog` / `vvp` / `verilator` / `gtkwave`（可选，用于看波形）。

```bash
uv sync                                  # 首次：创建 .venv

uv run mycup init      # 生成文件清单（可选）
uv run mycup list      # 列出所有 testbench
uv run mycup all       # 运行全部 HDL TB

uv run mycup run tb_alu     # 编译并运行单个
uv run mycup wave tb_alu    # 用 gtkwave 打开波形
uv run mycup lint           # Verilator 静态检查
uv run mycup test           # cocotb + pytest
uv run mycup clean          # 清理 build/ waves/ logs/

# 仿真期装载程序（+instr= / +data=），细节见 programs/README.md
uv run mycup run tb_prog --prog programs/demo.hex
```

> 工作流：`build` / `run` / `all` 会**自动发现** `sim/tb/**/tb_*.v` 并生成所需清单，
> 新增 testbench 不需要手动注册。`init` 只是提前批量生成清单，可选。

### Python 验证流程（cocotb + pytest，PoC）

与上面的 HDL TB 流程**并存**，不影响 `sim/tb`：

```bash
uv sync                 # 创建 .venv，安装 cocotb / pytest
uv run pytest -v        # 运行全部 Python 用例
uv run pytest -v tests/test_lw_sw.py::test_lw_sw

MYCUP_WAVES=1 uv run pytest -v tests/test_lw_sw.py   # 导出波形
```

说明见 [`tests/README.md`](tests/README.md)。目前移植了 `tb_alu` 与 `tb_lw_sw` 两个用例作为 PoC，
后续是否全面迁移由你决定。

---

## IDE lint 配置（VS Code）

目标：让编辑器里看到的告警/错误与命令行 `mycup lint` **完全一致**。

项目 lint 的「文件清单 + 参数」统一由 [`mycup/cli.py`](mycup/cli.py) 生成到
[`verilator.f`](verilator.f)，作为**单一事实来源**：

- `mycup lint` 直接 `verilator -f verilator.f`；
- IDE（[`mshr-h.veriloghdl`](https://marketplace.visualstudio.com/items?itemName=mshr-h.veriloghdl) 扩展）
  通过 [`.vscode/settings.json`](.vscode/settings.json) 复用同一个 `-f verilator.f`。

```jsonc
// .vscode/settings.json
{
  "verilog.linting.linter": "verilator",
  "verilog.linting.verilator.runAtFileLocation": false,
  "verilog.linting.verilator.arguments": "-f verilator.f -Wno-MODDUP -Wno-TIMESCALEMOD -Wno-MULTITOP"
}
```

几点说明：

- 扩展是**针对“当前打开的文件”**单独调用 verilator 的，且会把该文件**额外追加一次**
  （清单里已有它 → 重复）。用 `-f verilator.f` 让它同时载入整个工程，再用 `-Wno-MODDUP`
  容忍这次重复，从而使输出与项目 lint 对齐。
- `-Wno-TIMESCALEMOD` / `-Wno-MULTITOP` 只在**打开 testbench** 时才会出现（此时会把 tb 与全部 RTL
  一起 lint），项目 lint 仅针对 RTL，不会产生这些告警。
- **新增/删除 RTL 文件后**执行 `mycup init`（或直接 `mycup lint`）刷新 `verilator.f`。
- 若 `verilator` 不在 `PATH` 中，可在 `verilog.linting.path` 指定其安装目录。

---

## SV 工具链（LSP / format）

在保留 Verilator lint 不变的前提下，补充了编辑器智能提示与格式化能力：

| 工具 | 用途 | 版本 | 安装位置 |
| :-- | :-- | :-- | :-- |
| **veridian** | Language Server：hover / 跳转定义 / 文档符号 / 补全 / 格式化 | 0.1.0 (nightly) | `~/.local/bin/veridian-real` |
| **veridian-lsp** | 轻量 LSP 代理：丢弃 veridian 不可靠的诊断与 `didSave` | 本仓库脚本 | `~/.local/bin/veridian-lsp` |
| **verible** | `verible-verilog-format`（格式化）等 | v0.0-4296 | `~/.local/bin/verible-*` |

> 为什么是 veridian：`slang` 的 release 里没有附带 `slangd`；`svls` 只做 svlint 风格诊断、**不提供导航**；`verible-verilog-ls` 对初始化参数较敏感。veridian 的 LSP 能力完整，且能被 `mshr-h.veriloghdl` 接管。
>
> **为什么需要 `veridian-lsp` 代理**：veridian 内置诊断不接收 include 路径，会对 `vtest.vh` / `instr.h` 误报。代理只丢弃 `textDocument/publishDiagnostics` 与 `textDocument/didSave`，导航/补全/格式化原样转发；诊断统一交给 Verilator。

### 配置

- 编辑器：[`.vscode/settings.json`](.vscode/settings.json)
  - `verilog.languageServer.veridian.enabled: true`
  - `verilog.languageServer.veridian.path: "veridian-lsp"`（代理）
  - `files.associations`: 把 `*.v` / `*.vh` 识别为 `systemverilog`（veridian 客户端只绑定该语言；代码本身兼容 SV2012）
- 项目：[`veridian.yml`](veridian.yml)
  - `include_dirs`: `rtl/core/include`、`lib`
  - `source_dirs`: `rtl`、`sim/tb`
  - `auto_search_workdir: false`（避免递归扫到 `.venv` / `build`）
  - 诊断交给项目 `mycup lint`，LSP 侧诊断关闭
- 代理：[`scripts/veridian-lsp.py`](scripts/veridian-lsp.py)

### 用法

```bash
# 编辑器：重新加载窗口后生效
#   Ctrl+Shift+P -> Developer: Reload Window
#   悬停 / F12 跳转 / Ctrl+Shift+O 文档符号
#   手动格式化：Shift+Alt+F（verible-verilog-format）

# 格式化（默认不自动保存格式化，避免大面积 diff）
verible-verilog-format rtl/core/units/alu.v
```

### slang（可选，当前未接入）

`slang` 12.0 已安装在 `~/.local/bin/slang`，但**没有接入项目流程**。当前规模下
Verilator + cocotb 已经足够；如果以后需要更严格的语义检查，可手动运行：

```bash
slang --lint-only --timescale 1ns/1ps \
  -Irtl/core/include -Ilib $(find rtl sim/tb -name '*.v')
```

### 换机器时如何安装

工具都在 `~/.local/bin`，扩展通过 `PATH` 查找：

```bash
# verible（GitHub release）
#   https://github.com/chipsalliance/verible/releases -> *-linux-static-x86_64.tar.gz

# veridian（GitHub nightly）
#   https://github.com/vivekmalneedi/veridian/releases/tag/nightly -> veridian-ubuntu-22.04.tar.gz
#   解压后：ln -sf /path/to/veridian ~/.local/bin/veridian-real

# LSP 代理（本仓库）
cp scripts/veridian-lsp.py ~/.local/bin/veridian-lsp
chmod +x ~/.local/bin/veridian-lsp
```

> 注意：`.vscode/settings.json` 依赖 `veridian-lsp` / `verible-verilog-format` 在 `PATH` 中；
> 若不在，可分别用 `verilog.languageServer.veridian.path` 和
> `verilog.formatting.veribleVerilogFormatter.path` 指定绝对路径。

---

## 文档导航

- **[docs/README.md](docs/README.md)** —— 文档总索引与各文档的时效性标注
- **[docs/arch/architecture.md](docs/arch/architecture.md)** —— 整体框架、数据通路、模块职责、已知限制
- **[docs/roadmap.md](docs/roadmap.md)** —— 下一步演进方向（重点：单周期 → 流水线）
- `docs/unit/` —— 各功能单元的端口与行为
- `docs/instr/` —— 分版本的指令实现说明
- `docs/ctrl/ctrl.md` —— 控制信号真值表

---

## 设计约定

- **字节序**：大端（见指令级 testbench 中的机器码注释）。
- **编码风格**：单元模块通过显式端口互联；顶层 `cpu_top` 用 `.*` 隐式连接同名信号。
- **提交信息**：采用 `<type>(<scope>): <desc>` 形式（`feat` / `fix` / `refactor` / `test` / `doc` / `chore`）。
- **分支**：`master` 为主干，特性在主题分支上开发后合并。

---

## 下一步

短期聚焦单周期内核的补全，中期主线是 **单周期 → 5 级流水线** 的重构。
完整的分阶段计划、改造步骤与风险点见 **[docs/roadmap.md](docs/roadmap.md)**。
