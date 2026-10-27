# 文档索引

本目录收录 `my_cup` 的设计文档。文档分三类：**整体设计**、**单元实现**、**指令实现**。

> 说明：本索引只做导航与时效性标注，**不修改**任何已有文档内容。
> 标注为「⚠️ 可能过时」的文档保留原样，供对照历史；后续如有需要可另起新版本补充。
>
> 当前发布线：**`v0.3-mips`**（MIPS32 子集，8 条指令，单周期）。
> 下一阶段：**`v0.3-rv32i`**（RV32I 最小子集设计已整理，尚未实现）。

---

## 1. 整体设计

| 文档 | 内容 | 时效性 |
| :-- | :-- | :-- |
| [arch/architecture.md](arch/architecture.md) | 整体框架、单周期数据通路、模块职责、信号连接、已知限制 | ✅ 已校对到 v0.3-mips |
| [roadmap.md](roadmap.md) | 演进方向与阶段规划，重点为流水线改造 | ✅ 已校对到 v0.3-mips |
| [ctrl/ctrl.md](ctrl/ctrl.md) | 控制信号真值表 | ✅ 与当前 8 条指令一致 |

## 2. 指令实现（按版本）

| 文档 | 覆盖指令 | 时效性 |
| :-- | :-- | :-- |
| [instr/instr_v0.1.md](instr/instr_v0.1.md) | `addu` `addiu` `lw` `sw` `beq` `j` | ✅ 与实现一致 |
| [instr/instr_v0.2.md](instr/instr_v0.2.md) | `jal` `jr` | ✅ 与实现一致 |
| [instr/instr_v0.3.md](instr/instr_v0.3.md) | `sb` `sh` + `lb/lbu/lh/lhu` | ⏸ 已延后（不在当前 ISA） |

## 3. 功能单元

| 文档 | 单元 | 时效性 |
| :-- | :-- | :-- |
| [unit/pc.md](unit/pc.md) | `pc` | ✅ |
| [unit/npc.md](unit/npc.md) | `npc` | ✅ 已更新为 `npc_op` + `jmp_reg` |
| [unit/instrm.md](unit/instrm.md) | `instrm` | ✅ |
| [unit/regfile.md](unit/regfile.md) | `regfile` | ✅ |
| [unit/ext.md](unit/ext.md) | `ext` | ✅ |
| [unit/alu.md](unit/alu.md) | `alu` | ✅ 当前仅 ADD/SUB |
| [unit/cond.md](unit/cond.md) | `cond` | ✅ 当前仅 EQ |
| [unit/datam.md](unit/datam.md) | `datam` | ✅ 字访问（子字访问延后） |

## 4. RV32I 专题

| 文档 | 内容 | 时效性 |
| :-- | :-- | :-- |
| [v0.3-rv32i/design.md](v0.3-rv32i/design.md) | v0.3-rv32i 当前批次设计落地、范围、非法策略、任务与验证 | 🚧 规划中 |
| [v0.3-rv32i/units.md](v0.3-rv32i/units.md) | 各模块接口、控制表和实现细节 | 🚧 规划中 |
| [v0.3-rv32i/instruction-paths.md](v0.3-rv32i/instruction-paths.md) | 每条指令的 Mermaid 数据流图 | 🚧 规划中 |
| [v0.3-rv32i/future.md](v0.3-rv32i/future.md) | 后续批次与待议设计 | 🚧 规划中 |
| [v0.3-rv32i/datapath.drawio](v0.3-rv32i/datapath.drawio) | 整个单周期 CPU 的 draw.io 设计图 | 🚧 规划中 |
| [rv32i/format.md](rv32i/format.md) | RV32I 六种指令格式与立即数拼接 | ✅ |
| [rv32i/asm.md](rv32i/asm.md) | RV32I 汇编语义（含 v0.4 的 `lui`） | ✅ |
| [rv32i/inst-list.md](rv32i/inst-list.md) | RV32I 指令清单 | ⚠️ `Save` 应为 `Store` |
| [`isa/rv32i.yaml`](../isa/rv32i.yaml) | 机器可读编码表（opcode/funct/imm），`implemented` 为本批 7 条 | ✅ |

---

## 已知的文档不一致

以下为整理过程中发现的问题，当前均已处理或明确延后：

1. ~~**`ctrl/ctrl.md`**：`sb/sh` 行 opcode 错误、缺少 `lb/lbu/lh/lhu` 行~~ ✅ 已重写为当前 8 条指令。
2. **`instr/instr_v0.3.md`**：`sb/sh` 的 opcode 写法有误；该文档已整体标记为**延后**，保留作为未来参考（不视为待修）。
3. ~~**`unit/npc.md`**：端口描述过时~~ ✅ 已更新为 `npc_op` + `jmp_reg`。
4. ~~**`unit/cond.md`**：比较类型描述与实现不一致~~ ✅ 已注明当前只实现 `COND_TYPE_EQ`。
5. ~~**`unit/alu.md`**：操作码表与实现不一致~~ ✅ 已注明当前只实现 `ADD`/`SUB`。
6. ~~**`unit/datam.md`**：未反映字节/半字能力~~ ✅ 已改为字访问描述。

> 处理建议：修订时**按版本新增**（如 `ctrl_v0.4.md`）或直接更新并在提交信息中说明，二选一即可，避免文档与实现长期漂移。
