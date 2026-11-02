# 架构说明

本文描述 `my_cup` 的整体框架、数据通路与模块职责，作为阅读代码的入口。

- 顶层模块：[`rtl/cpu_top.sv`](../../rtl/cpu_top.sv)
- 共享类型/控制编码：[`rtl/cpu_pkg.sv`](../../rtl/cpu_pkg.sv)
- 当前批次设计：[`docs/v0.3-rv32i/design.md`](../v0.3-rv32i/design.md)
- 模块接口：[`docs/v0.3-rv32i/units.md`](../v0.3-rv32i/units.md)

---

## 1. 设计风格

当前是**单周期（single-cycle）**处理器：

- 一条指令在一个时钟周期内完成取指、译码、执行、访存、写回；
- 数据通路是组合逻辑，只有两类时序状态：
  - `pc.curr_pc` 在时钟上升沿更新为 `next_pc`；
  - `regfile` / `datam` 的写入在时钟上升沿生效。
- 因此一个时钟沿推进一条指令，`pc` 的更新速率即为指令吞吐。

当前实现的是 **RV32I 最小子集 7 条指令**：

```text
add, addi, beq, lw, sw, jal, jalr
```

尚未实现 `lui/auipc`、逻辑/移位/比较、子字访存、其他分支、trap/CSR 和流水线。

---

## 2. 顶层结构


> 图中省略了 `wb_data`、`alu_src2` 等 MUX 的细节，完整连线见 `rtl/cpu_top.sv`。

---

## 3. 模块清单

| 模块      | 文件         | 职责 |
| :-------- | :----------- | :------------ |
| `cpu_top` | `cpu_top.sv` | 顶层：实例化、连线、写回 MUX，输出 `inst_illegal` |
| `pc`      | `pc.sv`      | 程序计数器；`rst` 清零，否则每沿写入 `next_pc` |
| `npc`     | `npc.sv`     | 计算 `next_pc`，处理分支跳转 |
| `instrm`  | `instrm.sv`  | 指令存储器（IMEM），组合读 |
| `decoder` | `decoder.sv` | RV32I 字段切分、内部 `imm_gen` 函数、`valid_encoding` |
| `ctrl`    | `ctrl.sv`    | 7 条指令控制表、`inst_illegal`、非法时安全控制 |
| `regfile` | `regfile.sv` | 32×32 寄存器堆；`x0` 恒 0；上升沿写 |
| `alu`     | `alu.sv`     | `ADD` / `EQ` / `NOP`，输出 `alu_out` 和 `cmp_result` |
| `datam`   | `datam.sv`   | 数据存储器（DMEM），整字访问，组合读/上升沿写 |

> `ext` 和 `cond` 已删除：立即数生成并入 `decoder`，分支比较并入 `alu`。
> 流水线寄存器仍在 `rtl/pipe/`，但当前 `cpu_top` 还没有接入。

---

## 4. 一条指令的数据流

| 阶段    | 动作 |
| :------ | :----------------------------- |
| **IF**  | `instrm` 输出指令              |
| **ID**  | `decoder` 译码；`ctrl` 产生控制信号；`regfile` 读 |
| **EX**  | ALU 计算地址/结果/比较         |
| **MEM** | `datam` 读或写                 |
| **WB**  | `wb_data` 选择，写回 `regfile` |

### 关键连线

```verilog
assign branch_taken = cmp_result && (ctrl.npc_op == NPC_BRANCH);
assign inst_illegal = ctrl.inst_illegal;
assign instr_addr   = curr_pc;
assign alu_src1     = rs1_data;
assign alu_src2     = (ctrl.src2_sel == SRC2_SEL_IMM) ? imm : rs2_data;
assign addr         = alu_out;
assign w_data       = rs2_data;
```

`npc` 使用：

```text
inst_pc / npc_op / branch_taken / pc_offset / jalr_target / inst_illegal
```

`pc_offset` 已经是字节偏移；`jalr_target` 由 ALU 计算，NPC 只清 bit0。

---

## 5. 控制信号

`ctrl_t` 字段：

| 字段 | 含义 |
| :-- | :-- |
| `npc_op`    | `PLUS4` / `BRANCH` / `JAL` / `JALR` |
| `reg_write` | 是否写寄存器        |
| `alu_op`    | `ADD` / `EQ` / `NOP` |
| `mem_read`  | 是否读数据存储器    |
| `mem_write` | 是否写数据存储器    |
| `wb_sel`    | ALU / 内存 / PC+4   |
| `src2_sel`  | `rs2` / `imm`       |
| `inst_illegal` | 当前编码是否非法 |

控制表见 [`docs/v0.3-rv32i/units.md`](../v0.3-rv32i/units.md#14-ctrlsv)。

---

## 6. 存储器模型

| | 指令存储器 `instrm` | 数据存储器 `datam` |
| :-- | :-- | :-- |
| 容量 | `IMEM_WORDS`（默认 2048 字 / 8 KiB） | `DMEM_WORDS`（默认 2048 字 / 8 KiB） |
| 地址解码 | `instr_addr[IMEM_ADDR_W+1:2]` | `addr[DMEM_ADDR_W+1:2]` |
| 访问 | 组合读 | 组合读 / 上升沿写 |
| 位宽访问 | 固定 32 位 | 固定 32 位（整字访问；子字访问延后） |

> 二者是相互独立的存储体（哈佛结构），对后续上流水线有利。
> 仿真期通过 plusarg `+instr=` / `+data=` 和 `$readmemh` 装载，
> 该入口仅仿真有效、不参与综合。

---

## 7. 构建与测试流程

验证全部走 **cocotb + pytest**：

```text
tests/<category>/tb_*.py   ──(cocotb runner)──► iverilog 编译 ──► vvp 仿真
tests/<category>/test_*.py ──(pytest)─────────► 收集 / 报告 / 参数化
```

常用命令：

```bash
uv run mycup test       # 全部 cocotb + pytest
uv run mycup lint       # Verilator 静态检查
uv run mycup prog programs/demo.hex
uv run mycup clean
```

也可以使用 `make test` / `make lint` / `make prog FILE=...`。
路径、工具和 flags 由 [`toolchain.toml`](../../toolchain.toml) 统一描述，
详见 [`docs/toolchain.md`](../toolchain.md)。

---

## 8. 当前限制

1. 仅实现 RV32I 最小 7 条指令；未实现指令统一 `inst_illegal` + stop。
2. 单周期关键路径较长；流水线寄存器已存在但未接入。
3. `datam` 只支持整字访问，没有字节掩码/子字访存。
4. 地址对齐用仿真断言检查（`datam` / `instrm` / `npc`），本批不 trap。
5. 文档中的 MIPS 单元/指令说明保留为 `v0.3-mips` 历史参考。

---

## 9. 一句话总览

> 一个组合数据通路 + 少量时序状态的 **RV32I 最小子集单周期 CPU**；
> 指令/数据存储分离；控制集中在 `ctrl`，立即数和译码在 `decoder`，
> 分支比较在 `alu`；下一步是在稳定的单周期基线上接流水线。
