# v0.3-rv32i 后续与待议

> 本文件只放未来批次和待议项，不属于 v0.3-rv32i 当前实现范围。
> 当前设计见 [design.md](design.md)，模块细节见 [units.md](units.md)。

## 1. 后续批次 / 待议

以下内容不影响本批实现，统一后置。

### 1.1 流水线

- `imm32`、`inst_illegal`、`inst_pc`、`pc_plus4` 随 ID/EX 打拍；
- 分支在 EX 解决时，目标使用 ID/EX 的 PC；
- `inst_illegal` 带到 commit/trap 阶段，并 drain/flush；
- 前递、load-use、分支冲刷、retire 接口；
- 是否把分支提前到 ID（需要独立比较器/更复杂前递）。

### 1.2 完整 RV32I

- `sub`、逻辑、移位、`slt/sltu`；
- `bne/blt/bge/bltu/bgeu`；
- `lui/auipc`；
- `lb/lh/lbu/lhu/sb/sh` + `wstrb` + 端序；
- `fence/ecall/ebreak`；
- trap/CSR/异常。

### 1.3 移位立即数

后续加移位时：

- `slli/srli/srai` 在 `imm_type` 上仍统一为 `I`；
- `imm` 包含 `funct7`，ALU 只取 `alu_src2[4:0]`；
- 汇编器/YAML 用 `shift_imm: true` 区分 `funct7+shamt` 与普通 `imm12`；
- 不需要 `IMM_SHAMT`；
- 当前 YAML 的 `SHIFT` / `kind: shamt` 需要同步改成 I 型 + `shift_imm`。

### 1.4 U 型 / LUI

- 增加 `IMM_U`；
- `lui` 需要 `WB_SEL_IMM`；
- `auipc` 需要 `src1_sel`（PC/rs1）。

### 1.5 微架构优化

- `ctrl` 分层、`alu_ctrl` 拆分；
- 独立 `bcmp`（如果分支要提前到 ID）；
- 专用地址通道 AGU；
- `cmp_result` 是否简化为 `alu_out[0]`；
- 分支预测。

### 1.6 其他待议

- `instm/inst_addr` 改名是否在本批收尾执行；
- `fence` 作为 NOP 还是 illegal；
- 非对齐地址是 trap、支持还是断言；
- 是否引入 `sim_err` / test-only checker；
- `docs/rv32i/asm.md` 的版本标记整理；
- `inst-list.md` 的 `Save` -> `Store`；
- `docs/README` 索引和 YAML 引用。
