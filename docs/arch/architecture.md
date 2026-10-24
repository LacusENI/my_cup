# 架构说明

本文描述 `my_cup` 的整体框架、数据通路与模块职责，作为阅读代码的入口。

- 顶层模块：[`rtl/cpu_top.sv`](../../rtl/cpu_top.sv)
- 控制信号编码：[`rtl/cpu_pkg.sv`](../../rtl/cpu_pkg.sv)

---

## 1. 设计风格

当前是**单周期（single-cycle）**处理器：

- 一条指令在**一个时钟周期内**完成取指、译码、执行、访存、写回；
- 数据通路是**纯组合逻辑**（`assign` / `always @(*)`），只有两类时序状态：
  - `pc.curr_pc`：在时钟上升沿更新为 `next_pc`；
  - `regfile` / `datam` 的写入：在时钟上升沿生效。
- 因此一个时钟沿推进一条指令，`pc` 的更新速率即为指令吞吐。

这种结构利于理解与验证，但没有流水线并行度，且关键路径过长，
是后续要演进的主要动因（见 [roadmap.md](roadmap.md)）。

---

## 2. 顶层框图

```
                          +-------------------------------------------------------+
   instr[31:26], [5:0]    |                     ctrl (控制器)                       |
      +------------------>| (op,funct) -> npc_op,reg_write,alu_op,mem_read/mem_write,|
      |                   |               cond_type,ext_type,rd_sel,wb_sel,src2_sel|
      |                   +---+----+----+----+----+----+----+----+-------------------+
      |                       |    |    |    |    |    |    |    |   (控制信号扇出)
      |                       v    v    v    v    v    v    v    v
  +---+------+  curr_pc  +----------+  instr  +---------+
  |    pc    |---------->|  instrm  |-------->| decoder |---- rs,rt,rd ----> regfile
  |          |           |  (IMEM)  |         |         |---- imm16 --------> ext
  +----+-----+           +----------+         +---------+---- instr_index --> npc
       ^  next_pc                                     | op,funct
       |                                              v
  +----+-----+  cond_jmp  +------+   flags   +---------+   src2   +-----------+
  |   npc    |<-----------| cond |<----------|   alu   |<---------| regfile   |
  +----------+            +------+           +----+----+  rs1,rs2 |  (32x32)  |
       ^ ra = rs1_data                          | alu_out          +-----+-----+
       |                                        v                        | rs2_data
       |                                   +----------+  M[addr] <= ------+
       +-----------------------------------|  datam   |
                                           |  (DMEM)  |--> r_data --+
                                           +----------+             |
                                                                    v
                                        wb mux: r_data / alu_out / pc_plus4  -> regfile.wb_data
```

> 注：为清晰起见，图中省略了 `cpu_top` 中若干**多路选择器**（`reg_dst`、`wb_data`、`alu_src2`），
> 它们由 `rd_sel / wb_sel / src2_sel` 控制，详见 §5。

---

## 3. 模块清单

| 模块 | 文件 | 职责 |
| :-- | :-- | :-- |
| `cpu_top` | `rtl/cpu_top.sv` | 顶层：实例化所有单元、显式连线、实现多路选择器 |
| `pc` | `control/pc.sv` | 程序计数器；`rst` 清零，否则每沿写入 `next_pc` |
| `npc` | `control/npc.sv` | 下一 PC 决策：`PLUS4` / `BRANCH`(条件偏移) / `DIRECT`(区域跳转) / `RA`(寄存器跳转)；同时输出 `pc_plus4` |
| `instrm` | `memory/instrm.sv` | 指令存储器（IMEM），默认 2048 字，组合读 |
| `decoder` | `control/decoder.sv` | 把 32 位指令拆成 `instr_t`（op/rs/rt/rd/shamt/funct）+ `imm16` / `instr_index` |
| `ctrl` | `control/ctrl.sv` | 控制器：由 `op/funct` 产生打包好的 `ctrl_t` |
| `regfile` | `datapath/regfile.sv` | 32×32 寄存器堆；`$0` 恒 0；上升沿写 |
| `ext` | `datapath/ext.sv` | 立即数 16→32 位扩展（符号/零扩展由 `ext_type` 选择） |
| `alu` | `datapath/alu.sv` | 算术逻辑运算，输出结果与标志 `zero_f/neg_f/overflow_f/carry_f` |
| `cond` | `control/cond.sv` | 依据 `cond_type` 将 ALU 标志折算为分支条件 `cond_jmp` |
| `datam` | `memory/datam.sv` | 数据存储器（DMEM），默认 2048 字，**仅整字访问**（子字访问延后） |

> **流水线寄存器（已就位，尚未接入）**：`rtl/pipe/` 下有
> `if_id_reg` / `id_ex_reg` / `ex_mem_reg` / `mem_wb_reg`，
> 使用 `cpu_pkg` 的 `if_id_t` / `id_ex_t` / `ex_mem_t` / `mem_wb_t`，支持 `rst/flush/stall`。
> 当前 `cpu_top` 仍是单周期，还没有把它们接进去。

---

## 4. 数据通路（一条指令的旅程）

以单周期视角，按概念上的 IF/ID/EX/MEM/WB 描述：

| 阶段 | 发生的动作 |
| :-- | :-- |
| **IF** | `instr_addr = curr_pc` → `instrm` 输出 `instr`；`npc` 依据 `npc_op/cond_jmp` 计算 `next_pc` |
| **ID** | `decoder` 拆字段；`ctrl` 产生控制信号；`regfile` 读出 `rs1_data/rs2_data`；`ext` 扩展 `imm16` |
| **EX** | `alu_src1 = rs1_data`，`alu_src2 = src2_sel ? imm32 : rs2_data`；`alu` 计算 `alu_out` 与标志 |
| **MEM** | `addr = alu_out`，`w_data = rs2_data`；`datam` 读/写（`mem_read/mem_write`） |
| **WB** | `wb_data` 多路选择（见 §5）写回 `regfile` |

### 关键连线（来自 `cpu_top`，均为 `assign`）

```verilog
assign instr_addr = curr_pc;
assign reg_src1   = rs;
assign reg_src2   = rt;
assign alu_src1   = rs1_data;
assign alu_src2   = src2_sel ? imm32 : rs2_data;
assign addr       = alu_out;
assign w_data     = rs2_data;
assign ra         = rs1_data;        // 供 npc 的寄存器跳转使用
assign jmp_target = instr_index;
assign jmp_offset = imm16;
```

---

## 5. 顶层多路选择器

三个 MUX 直接在 `cpu_top` 中用条件表达式实现：

**写回目标寄存器 `reg_dst`**（由 `rd_sel` 选择）：

| `rd_sel` | 目标 |
| :-- | :-- |
| `RD_SEL_RD` | `rd` |
| `RD_SEL_RT` | `rt` |
| `RD_SEL_REG_RA` | `5'd31`（`$ra`） |
| 其它 | `5'd0` |

**写回数据 `wb_data`**（由 `wb_sel` 选择）：

| `wb_sel` | 数据源 |
| :-- | :-- |
| `WB_SEL_ALU_OUT` | `alu_out` |
| `WB_SEL_R_DATA` | `r_data`（访存读回） |
| `WB_SEL_PC_P4` | `pc_plus4`（`jal` 保存返回地址） |

**ALU 第二操作数 `alu_src2`**（由 `src2_sel` 选择）：`SRC2_SEL_RS2` → `rs2_data`；`SRC2_SEL_IMM` → `imm32`。

完整的「指令 → 控制信号」对照见 [`ctrl/ctrl.md`](../ctrl/ctrl.md)。

---

## 6. 存储器模型

| | 指令存储器 `instrm` | 数据存储器 `datam` |
| :-- | :-- | :-- |
| 容量 | `IMEM_WORDS`（默认 2048 字 / 8 KiB） | `DMEM_WORDS`（默认 2048 字 / 8 KiB） |
| 地址解码 | `instr_addr[IMEM_ADDR_W+1:2]` | `addr[DMEM_ADDR_W+1:2]` |
| 访问 | 组合读 | 组合读 / 上升沿写 |
| 位宽访问 | 固定 32 位 | 固定 32 位（整字访问；子字访问延后） |

> 二者是**相互独立的存储体**（天然的哈佛结构），这一点对后续上流水线有利（无需再拆分存储）。
> 存储器已提供**仿真期装载入口**：`instrm`/`datam` 内含 `initial` + `$readmemh`，
> 通过 vvp 的 plusarg `+instr=` / `+data=` 传入 hex 文件，见 §7 与 [`programs/README.md`](../../programs/README.md)。
> 该入口**仅仿真有效、不参与综合**；纯 ASIC 流程后续仍需替换为 ROM / 总线加载方案。

---

## 7. 构建与测试流程

验证全部走 **cocotb + pytest**：

```
tests/tb_*.py   ──(cocotb runner)──►  iverilog 编译  ──►  vvp 仿真
tests/test_*.py ──(pytest)──────────►  收集 / 报告 / 参数化
```

- `mycup test`：运行全部 cocotb + pytest 用例；
- `mycup lint`：生成 `verilator.f`，再运行 `verilator -f verilator.f`；
- `mycup prog <hex>`：用 `+instr=` 装载程序，运行 `tests/test_instr.py::test_prog_demo`；
- `mycup clean`：清理 `build/`、`waves/`、`logs/` 等生成物。

`verilator.f` 由 [`mycup/cli.py`](../../mycup/cli.py) 生成（含 `-Wall --timing --bbox-sys`），
**IDE 的 Verilog lint 也复用同一清单**，从而与命令行保持一致（详见 [README](../README.md#ide-lint-配置vs-code)）。

### 程序装载（仿真）

```bash
uv run mycup prog programs/demo.hex
uv run mycup prog programs/demo.hex --data programs/data.hex --cycles 8
```

`hex` 通过 `+instr=`、`--data` 通过 `+data=` 传给 vvp；`instrm` / `datam` 中的 `initial` 据此调用 `$readmemh`。
`--cycles` 控制程序跑完后等待的周期数（默认 4）。

---

## 8. 已知限制与已有技术债

整理框架时发现的问题，按影响排序：

1. ~~**`lb/lbu/lh/lhu` 控制通路未接通（半成品）**~~ ✅ 已移除；子字访问整体延后
   （见 [roadmap.md](roadmap.md#明确延后deferred)）。`datam` 收敛为整字访问，
   `read_signed` / `mem_size` 已删除。

2. ~~**`ctrl.sv` 大量使用 `2'bx` / `1'bx` 作为默认值**~~ ✅ 已改为 `always_comb` + 显式默认值 + `unique case`。

3. ~~**`defines.vh` 与 `instr.vh` 职责重叠**~~ ✅ 已合并为 `cpu_pkg.sv`（package），用 `import` 使用。

4. **`alu.sv` 与 `cond.sv` 功能远未覆盖设计意图**
   ALU 仅实现 `ADD`/`SUB`，`neg_f/overflow_f/carry_f` 是常量 0（TODO）；`cond.sv` 仅实现相等比较。
   现有 `docs/unit/alu.md`、`docs/unit/cond.md` 描述的是**目标形态**，与实现存在差距。

5. **`npc` 的 `ra` 命名易误导**
   该输入实际接的是 `rs1_data`（`jr` 的通用寄存器源），并非专指 `$ra`。建议更名（如 `jmp_reg`）以免与 `jal` 的 `$ra` 混淆。

6. **分支跳转逻辑分散**
   分支偏移在 `npc` 计算（`imm16 << 2`）、条件在 `cond` 判定、控制信号在 `ctrl` 产生，跨三个模块；
   上流水线时这些信号需要被正确地随流水寄存器打拍，建议先在这里梳理清晰。

7. ~~**`develop` 分支已落后 `master`**~~ ✅ 已快进到 `master`。

8. **无 CI**
   `.gitignore` 忽略了 `.github/`，目前没有自动化回归。建议接入 CI 跑 `mycup test` + `mycup lint`。

9. **文档与实现漂移**
   部分 `docs/unit/*` 端口/编码已过时，登记详见 [docs/README.md](../README.md)。

10. ~~**`chore/gen_tb_dep.sh` 收尾消息引用未定义变量**~~ ✅ 已随 shell 脚本删除而移除。

---

## 9. 一句话总览

> 一个 **组合数据通路 + 少量时序状态** 的 MIPS32 子集单周期 CPU；
> 指令/数据存储已分离（哈佛）；控制集中在 `ctrl`，其余为纯功能单元；
> 主要待办是**清理控制逻辑默认值**、**补验证闭环**，并**向流水线重构**。
