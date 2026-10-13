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

### 已支持指令

| 类别 | 指令 |
| :-- | :-- |
| R 型 | `addu` `jr` |
| 立即数 | `addiu` |
| 访存 | `lw` `sw` `sb` `sh` |
| 分支/跳转 | `beq` `j` `jal` |

> `lb/lbu/lh/lhu` 目前**只有数据存储器侧就绪、控制通路尚未接通**，详见
> [架构说明中的"已知限制"](docs/arch/architecture.md#已知限制与已有技术债) 与 [路线图](docs/roadmap.md)。

---

## 目录结构

```
my_cup/
├── Makefile              # 构建 / 仿真 / lint 入口
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
│   └── tb/               # 测试平台
│       ├── unit/              # 单元级 testbench
│       └── instr/             # 指令级 testbench（驱动整个 cpu_top）
├── lib/                  # 通用库
│   └── vtest.vh               # 统一测试框架（宏：TEST / EXPECT / ...）
├── docs/                 # 设计与文档（见 docs/README.md）
├── chore/                # 辅助脚本
│   └── gen_tb_dep.sh          # 扫描 tb 生成 .f 清单与 .d 依赖
├── programs/             # 仿真用机器码程序 (*.hex) 与用法说明
├── build/                # 生成物：filelists / deps / 可执行目标 (gitignore)
├── waves/                # 生成的 VCD 波形 (gitignore)
└── logs/                 # 构建与 lint 日志 (gitignore)
```

---

## 快速开始

依赖：`iverilog` / `vvp` / `verilator` / `gtkwave`（可选，用于看波形）。

```bash
make init            # 扫描 sim/tb 下的 tb_*.v，生成 build/filelists 与 build/deps
make list            # 列出所有可运行的测试任务
make all             # 运行全部测试

make run-tb_alu      # 构建并运行单个测试
make wave-tb_alu     # 用 gtkwave 打开对应波形
make lint            # 对全部 RTL 运行 Verilator 静态检查
make clean           # 清理 build/ waves/ logs/

# 仿真期装载程序（+instr= / +data=），细节见 programs/README.md
make run-tb_prog PROG=programs/demo.hex
```

> 工作流：**新增 testbench 后需要先重新执行 `make init`**，让脚本重新生成清单文件。
> 详见 [`chore/gen_tb_dep.sh`](chore/gen_tb_dep.sh) 与 [架构说明](docs/arch/architecture.md#构建与测试流程)。

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
