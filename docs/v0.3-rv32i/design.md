# v0.3-rv32i 设计落地

> 状态：规划中，尚未开始 RTL 实现
> 前置版本：`v0.3-mips`（单周期 MIPS 子集，已打 tag）

> 相关文档：
> - 模块接口与实现细节：[units.md](units.md)
> - 单指令数据流：[instruction-paths.md](instruction-paths.md)
> - 整体数据通路图：[datapath.drawio](datapath.drawio)
> - 后续批次与待议：[future.md](future.md)

## 1. 本批范围

本批把单周期 CPU 从 MIPS 子集切换到 **RV32I 最小子集**，仍然保持单周期结构，不上流水线。

### 1.1 指令

本批实现 7 条：

```text
add
addi
beq
lw
sw
jal
jalr
```

伪指令由汇编器展开：

```text
j   -> jal x0, offset
jr  -> jalr x0, 0(rs1)
ret -> jalr x0, 0(ra)
nop -> addi x0, x0, 0
```

### 1.2 不在本批范围

```text
lui / auipc
sub、逻辑、移位、slt/sltu
lb/lh/lbu/lhu、sb/sh
bne/blt/bge/bltu/bgeu
fence / ecall / ebreak
trap / CSR / 异常
流水线
```

这些统一下沉到 [future.md](future.md)。

---

## 2. 总体决策

- **保持单周期**：本批只换 ISA，不引入流水线和冒险处理。
- **干净切换**：不做 MIPS/RV32I 双模，不保留旧控制路径。
- **顶层保持薄**：`cpu_top` 只做实例化和连线；合法/非法判断和安全控制由 `ctrl` 负责。
- **所有未实现指令一律 illegal**：本批不区分“合法但未实现”，统一 stop。
- **不做通用 `err` 端口**：断言失败用 `$fatal` 或 test-only checker；`inst_illegal` 只表示架构非法指令。
- **地址对齐只做仿真断言**：不做 trap，不作为 `inst_illegal`；行为后续再议。
- **x0 恒 0**：读写路径都保护；写 x0 丢弃。
- **32 位运算回绕**：add/addi 不产生溢出异常。
- **编码数据源**：`isa/rv32i.yaml` 是机器可读编码表；`implemented` 只列本批 7 条。

---

## 3. 数据通路总览

整体框图见 [datapath.drawio](datapath.drawio)；每条指令的数据流见
[instruction-paths.md](instruction-paths.md)。模块接口和内部细节统一放在
[units.md](units.md)，本文不重复。

## 4. 指令行为

| 指令 | 行为 |
| :-- | :-- |
| `add rd, rs1, rs2` | `R[rd] = R[rs1] + R[rs2]`，32 位回绕 |
| `addi rd, rs1, imm` | `R[rd] = R[rs1] + sext(imm12)`，32 位回绕 |
| `beq rs1, rs2, offset` | `R[rs1] == R[rs2]` 时 `PC = PC + sext(offset13)`，否则 `PC + 4` |
| `lw rd, offset(rs1)` | `R[rd] = M[R[rs1] + sext(offset12)]` |
| `sw rs2, offset(rs1)` | `M[R[rs1] + sext(offset12)] = R[rs2]` |
| `jal rd, offset` | `R[rd] = PC + 4`，`PC = PC + sext(offset21)` |
| `jalr rd, offset(rs1)` | `target = (R[rs1] + sext(offset12)) & ~1`，`R[rd] = PC + 4`，`PC = target` |

共同规则：

- `x0` 恒 0，写 x0 丢弃；
- 32 位运算回绕，不产生溢出异常；
- 分支/jal 的 offset 是字节偏移，bit0=0；
- `rd == rs1` 时读旧值；
- `jal/jalr` 的 link 是旧 PC+4。

---

## 5. 非法指令、断言与对齐

### 5.1 非法指令

```text
valid_encoding=1 且属于当前 7 条 -> 正常
其他情况 -> inst_illegal=1，stop
```

`stop` 行为：

```text
next_pc = inst_pc          // PC 保持
reg_write = 0
mem_read = 0
mem_write = 0
```

- 不写寄存器、不访存；
- 不继续取后续指令；
- `inst_illegal` 输出到顶层，供 testbench 断言；
- 本批不做 trap/CSR；后续再改成异常。

`fence/ecall/ebreak` 本批未实现，因此都按 illegal/stop 处理。
后续 `fence` 可以作为合法 NOP，`ecall/ebreak` 应进入 trap。

### 5.2 断言

- 不加通用 `err` 端口；
- 地址对齐、`jalr_target[1]`、`inst_addr[1:0]` 等只做仿真断言；
- 断言失败用 `$fatal` 或 test-only checker；
- 断言不作为 `inst_illegal`，也不驱动 CPU 行为。

### 5.3 对齐

本批只断言，不定行为：

- `lw/sw` 地址 4 字节对齐；
- `beq/jal` 目标 4 字节对齐（无 C 扩展）；
- `jalr_target[1] == 0`；
- `inst_addr[1:0] == 0`。

后续是否 trap 或支持非对齐，留到后续批次。

---

## 6. 落地任务

### 6.1 RTL

- `cpu_pkg.sv`：类型、枚举、`instr_t`、`ctrl_t`、流水线 struct 更新；
- `decoder.sv`：RV32I 字段、`valid_encoding`、隐藏 `imm_gen`；
- 新增 `imm_gen.sv`；
- `ctrl.sv`：7 条控制表、`inst_illegal`、安全控制；
- `alu.sv`：ADD / EQ / NOP、`cmp_result`、删 flags；
- `npc.sv`：新接口、JAL/JALR、非法 hold；
- `regfile.sv`：端口改名、删 `rd_sel`；
- `datam.sv`：字节地址模型、边界断言；
- `instrm.sv`：收尾改名（可选）；
- `cpu_top.sv`：删旧模块、接新接口、输出 `inst_illegal`；
- 删除 `ext.sv`、`cond.sv`。

### 6.2 测试

- 新增 `tests/control/tb_imm_gen.py` / `test_imm_gen.py`；
- 新增 `tests/control/tb_decoder.py` / `test_decoder.py`；
- 更新 `tb_alu`：ADD/EQ/NOP、`cmp_result`、无 flags；
- 更新 `tb_npc`：新端口/opcode、illegal hold、B/J 偏移；
- 更新 `tb_ctrl` + `ctrl_probe`：新 `ctrl_t` 字段、`inst_illegal`；
- 更新 `tb_regfile`：端口改名；
- 更新 `tb_datam`：字节地址模型/对齐断言；
- 更新 `tb_instr`：7 条指令、`jalr rd==rs1`、`rd=x0`、非法 stop；
- 更新 `tb_prog` 和 `programs/demo.hex`：RV32I 程序；
- `mips_asm.py` -> `riscv_asm.py`，更新 `test_asm`；
- 更新 `tests/utils/cocotb_utils.py`（如 `u_instrm` 改名）；
- 更新 `tests/README` 覆盖表和契约字段。

### 6.3 文档/数据

- `isa/rv32i.yaml` 的 `implemented` 保持 7 条；
- `docs/rv32i/asm.md`、`inst-list.md`、`format.md` 与本设计对齐；
- `docs/README.md` 加入本文件索引；
- 更新 `docs/arch/architecture.md` / `roadmap.md` 中的测试结构和当前状态；
- `programs/README.md` 更新 `mycup prog` 目标路径。

---

## 7. 验证标准

- 7 条指令的单指令 ISA 测试全部通过；
- `addi` 负立即数、`lw/sw` 负偏移、`beq/jal` 前后跳、`jalr` 目标正确；
- `jalr rd==rs1` 用旧值计算 target；
- `jal/jalr` 的 `rd=x0` 不写寄存器；
- 非法 opcode / 非法 funct3/funct7 进入 stop，PC 不动、寄存器/内存不变；
- `mycup test` 全绿；
- `mycup lint` 0 warning；
- `mycup prog programs/demo.hex` 通过。

---
