# 文档索引

本目录收录 `my_cup` 的设计文档。文档分三类：**整体设计**、**单元实现**、**指令实现**。

> 说明：本索引只做导航与时效性标注，**不修改**任何已有文档内容。
> 标注为「⚠️ 可能过时」的文档保留原样，供对照历史；后续如有需要可另起新版本补充。

---

## 1. 整体设计

| 文档 | 内容 | 时效性 |
| :-- | :-- | :-- |
| [arch/architecture.md](arch/architecture.md) | 整体框架、单周期数据通路、模块职责、信号连接、已知限制 | ✅ 最新（本次新增） |
| [roadmap.md](roadmap.md) | 演进方向与阶段规划，重点为流水线改造 | ✅ 最新（本次新增） |
| [ctrl/ctrl.md](ctrl/ctrl.md) | 控制信号真值表 | ⚠️ 部分行缺失/编码有误，见下 |

## 2. 指令实现（按版本）

| 文档 | 覆盖指令 | 时效性 |
| :-- | :-- | :-- |
| [instr/instr_v0.1.md](instr/instr_v0.1.md) | `addu` `addiu` `lw` `sw` `beq` `j` | ✅ 与实现一致 |
| [instr/instr_v0.2.md](instr/instr_v0.2.md) | `jal` `jr` | ✅ 与实现一致 |
| [instr/instr_v0.3.md](instr/instr_v0.3.md) | `sb` `sh`（文档中另含 `lb/lbu/lh/lhu`，但控制通路未接通） | ⚠️ 见下 |

## 3. 功能单元

| 文档 | 单元 | 时效性 |
| :-- | :-- | :-- |
| [unit/pc.md](unit/pc.md) | `pc` | ✅ |
| [unit/npc.md](unit/npc.md) | `npc` | ⚠️ 端口描述与当前实现不符 |
| [unit/instrm.md](unit/instrm.md) | `instrm` | ✅ |
| [unit/regfile.md](unit/regfile.md) | `regfile` | ✅ |
| [unit/ext.md](unit/ext.md) | `ext` | ✅ |
| [unit/alu.md](unit/alu.md) | `alu` | ⚠️ 操作码表为规划项，当前仅实现 ADD/SUB |
| [unit/cond.md](unit/cond.md) | `cond` | ⚠️ 比较类型描述有误（见下） |
| [unit/datam.md](unit/datam.md) | `datam` | ⚠️ 未反映字节/半字支持与新端口 |

---

## 已知的文档不一致（供后续修订参考）

以下为整理框架时发现的问题，**本次未改动原文件**，仅在此登记：

1. **`ctrl/ctrl.md`**：`sb`/`sh` 行的 opcode 写成 `10 1111`（应为 `10 1000` / `10 1001`），且两行相同；缺 `lb/lbu/lh/lhu` 行。
2. **`instr/instr_v0.3.md`**：`sb`/`sh` 的 opcode 写成 `00 1010` / `00 1011`（应为 `10 1000` / `10 1001`）；标题只列了 `sb/sh`，正文却包含 `lb/lbu/lh/lhu`。
3. **`unit/npc.md`**：端口仍写作 `jmp/jmp_target/jmp_offset/...`，当前实现为 `npc_op` 枚举 + `ra` 输入。
4. **`unit/cond.md`**：比较类型把 `11` 描述为"大于(无符号)"，与 `defines.vh` 中的 `COND_TYPE_LTU`（小于无符号）不一致。
5. **`unit/alu.md`**：列出了 MUL/DIV/AND/... 等操作码，但当前 `alu.v` 只实现了 `ADD`/`SUB`。
6. **`unit/datam.md`**：仍写"目前支持字读写"，未反映 `mem_size` / `read_signed` 端口与字节/半字读写能力。

> 处理建议：修订时**按版本新增**（如 `ctrl_v0.4.md`）或直接更新并在提交信息中说明，二选一即可，避免文档与实现长期漂移。
