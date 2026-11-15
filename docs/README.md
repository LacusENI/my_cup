# 文档索引

当前基线：**`v0.3-rv32i`**（RV32I 最小集，单周期）；当前工作区已实现 12 条指令。
当前目标：**`v0.4.0`**（完整 RV32I 基础指令集，单周期）。
历史版本放在 [`archive/`](archive/README.md)，不作为当前实现契约。

---

## 1. 当前设计与计划

| 文档 | 内容 | 状态 |
| :-- | :-- | :-- |
| [roadmap.md](roadmap.md) | 阶段划分、当前目标与长期方向 | ✅ 当前 |
| [version/v0.4.0/plan.md](version/v0.4.0/plan.md) | `v0.4.0` 批次、任务、风险与完成标准 | 📋 进行中 |
| [arch/architecture.md](arch/architecture.md) | 整体框架、单周期数据通路、模块职责、已知限制 | ✅ 当前 |
| [ctrl/ctrl.md](ctrl/ctrl.md) | 当前控制信号真值表 | ✅ 当前 |
| [toolchain.md](toolchain.md) | `toolchain.toml`、Makefile 与 `mycup` 的分工 | ✅ 当前 |

---

## 2. 当前功能单元

| 文档 | 单元 | 状态 |
| :-- | :-- | :-- |
| [units/pc.md](units/pc.md) | `pc` | ✅ |
| [units/npc.md](units/npc.md) | `npc` | ✅ |
| [units/instm.md](units/instm.md) | `instm` | ✅ |
| [units/regfile.md](units/regfile.md) | `regfile` | ✅ |
| [units/alu.md](units/alu.md) | `alu` | ✅ |
| [units/datam.md](units/datam.md) | `datam` | ✅ 整字访问；子字访存待 `v0.4.0` M5 |
| [units/halt_unit.md](units/halt_unit.md) | `halt_unit` | ✅ 已接入 `cpu_top` |

---

## 3. 当前 RV32I 参考

| 文档 | 内容 |
| :-- | :-- |
| [isa/format.md](isa/format.md) | RV32I 指令格式与立即数拼接 |
| [isa/inst-list.md](isa/inst-list.md) | RV32I 指令清单 |

---

## 4. 历史归档

| 目录 | 内容 |
| :-- | :-- |
| [archive/v0.3-rv32i/](archive/v0.3-rv32i/) | RV32I 最小集单周期基线；仅作历史参考 |

> `v0.3-rv32i` 的详细文档已移入 `docs/archive/`，不再参与当前实现契约。

---

## 维护约定

- `docs/units/` 对应当前 RTL；修改接口时同步更新。
- `docs/version/v0.4.0/` 只保存当前目标版本的计划和设计快照。
- 历史版本只追加到 `docs/archive/`，不再回写当前文档。
- 修改 RTL 时至少同步 `docs/units/`、`docs/ctrl/ctrl.md` 和对应版本计划。
