# 文档索引

本目录收录 `my_cup` 的设计文档。文档分三类：**整体设计**、**单元实现**、**指令实现**。

> 说明：本索引负责导航与时效性标注；文档内容随对应 RTL 版本同步更新。
> 历史版本文档如需保留，应明确标注版本，不混入当前实现契约。
>
> 当前实现线：**`v0.3-rv32i`**（RV32I 最小子集，7 条指令，单周期）。
> 历史基线：**`v0.3-mips`**（MIPS32 子集，8 条指令，已打 tag）。
> 源码树中的单元文档均为当前 RV32I 版本；MIPS 文档已归档。

---

## 1. 整体设计

| 文档 | 内容 | 时效性 |
| :-- | :-- | :-- |
| [arch/architecture.md](arch/architecture.md) | 整体框架、单周期数据通路、模块职责、信号连接、已知限制 | ✅ 已更新到 v0.3-rv32i |
| [roadmap.md](roadmap.md) | 演进方向与阶段规划，重点为流水线改造 | ✅ 已更新到 v0.3-rv32i |
| [ctrl/ctrl.md](ctrl/ctrl.md) | 控制信号真值表 | ✅ 已更新到 v0.3-rv32i |
| [toolchain.md](toolchain.md) | `toolchain.toml`、Makefile 与 `mycup` 的分工 | ✅ |

## 2. 指令实现（按版本）

MIPS 逐版本指令文档已随 `v0.3-mips` 归档，当前源码树不再保留。
当前 RV32I 的汇编语义和编码参考见 §4 的 `rv32i/asm.md`、`rv32i/format.md` 和 `isa/rv32i.yaml`。

## 3. 功能单元

| 文档 | 单元 | 时效性 |
| :-- | :-- | :-- |
| [units/pc.md](units/pc.md) | `pc` | ✅ |
| [units/npc.md](units/npc.md) | `npc` | ✅ |
| [units/instm.md](units/instm.md) | `instm` | ✅ |
| [units/regfile.md](units/regfile.md) | `regfile` | ✅ |
| [units/alu.md](units/alu.md) | `alu` | ✅ |
| [units/datam.md](units/datam.md) | `datam` | ✅ 字访问（子字访问延后） |

> `ext` 和 `cond` 已从 RTL 删除：立即数生成并入 `decoder`，分支比较并入 `alu`。

## 4. RV32I 专题

| 文档 | 内容 | 时效性 |
| :-- | :-- | :-- |
| [version/v0.3-rv32i/design.md](version/v0.3-rv32i/design.md) | v0.3-rv32i 设计落地、范围、非法策略与验证标准 | ✅ 已实现 |
| [version/v0.3-rv32i/units.md](version/v0.3-rv32i/units.md) | 各模块接口、控制表和实现细节 | ✅ 已实现 |
| [version/v0.3-rv32i/instruction-paths.md](version/v0.3-rv32i/instruction-paths.md) | 每条指令的 Mermaid 数据流图 | ✅ 已实现 |
| [version/v0.3-rv32i/future.md](version/v0.3-rv32i/future.md) | 后续批次与待议设计 | 📋 规划中 |
| [arch/datapath.drawio](arch/datapath.drawio) | 整个单周期 CPU 的 draw.io 设计图 | ✅ 已实现 |
| [rv32i/format.md](rv32i/format.md) | RV32I 六种指令格式与立即数拼接 | ✅ |
| [rv32i/asm.md](rv32i/asm.md) | RV32I 汇编语义（含后续 `lui` 规划） | ✅ 当前 7 条 |
| [rv32i/inst-list.md](rv32i/inst-list.md) | RV32I 指令清单 | ✅ |
| [`isa/rv32i.yaml`](../isa/rv32i.yaml) | 机器可读编码表（opcode/funct/imm），`implemented` 为本批 7 条 | ✅ |

---

## 维护约定

- `docs/units/` 下的单元文档对应当前 RTL，修改接口时同步更新。
- `docs/version/v0.3-rv32i/` 是本批设计的版本快照；行为或验证标准变化时同步更新。
- MIPS 历史文档已随 `v0.3-mips` 归档，不再保留在源码树中。
- 修改 RTL 时至少同步 `docs/units/`、`docs/version/v0.3-rv32i/` 和 `docs/ctrl/ctrl.md` 中受影响的部分。
