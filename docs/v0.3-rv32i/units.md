# v0.3-rv32i 模块设计

> 本文是 [design.md](design.md) 的模块级展开：接口、职责、控制表和实现注意点。
> 单指令数据流见 [instruction-paths.md](instruction-paths.md)，整体图见
> [datapath.drawio](datapath.drawio)。

## 模块概览

| 模块 | 职责 |
| :-- | :-- |
| `cpu_pkg` | 类型、枚举、`instr_t`、`ctrl_t`、流水线 struct |
| `decoder` | RV32I 字段切分、`valid_encoding`、封装 `imm_gen` |
| `imm_gen` | I/S/B/J 立即数拼接与扩展 |
| `ctrl` | 控制信号、`inst_illegal`、非法时安全控制 |
| `alu` | ADD / EQ / NOP、分支比较结果 |
| `npc` | PLUS4 / BRANCH / JAL / JALR / illegal hold |
| `regfile` | 32x32 寄存器堆，x0 恒 0 |
| `datam` | 整字数据存储器，字节地址模型 |
| `instrm` | 指令存储器（收尾阶段改名 `instm`） |
| `cpu_top` | 顶层实例化与连线，输出 `inst_illegal` |

## 1. 模块设计

### 1.1 `cpu_pkg.sv`

新增/调整类型：

```systemverilog
typedef logic [4:0] reg_t;

typedef enum logic [2:0] {
    IMM_NONE,
    IMM_I,
    IMM_S,
    IMM_B,
    IMM_J
} imm_type_t;

typedef enum logic [3:0] {
    ALU_ADD,
    ALU_EQ,
    ALU_NOP
} alu_op_t;

typedef enum logic [1:0] {
    NPC_PLUS4,
    NPC_BRANCH,
    NPC_JAL,
    NPC_JALR
} npc_op_t;

typedef enum logic [1:0] {
    WB_SEL_ALU_OUT,
    WB_SEL_R_DATA,
    WB_SEL_PC_PLUS4
} wb_sel_t;

typedef enum logic {
    SRC2_SEL_RS2,
    SRC2_SEL_IMM
} src2_sel_t;
```

删除：

```text
cond_type_t
ext_type_t
rd_sel_t
MIPS 的 op/funct 常量
s_ext_16_32 / z_ext_16_32（如无其他使用者）
```

`instr_t` 按 RV32I 字段重排：

```systemverilog
typedef struct packed {
    logic [6:0] funct7;
    logic [4:0] rs2;
    logic [4:0] rs1;
    logic [2:0] funct3;
    logic [4:0] rd;
    logic [6:0] opcode;
} instr_t;
```

`ctrl_t`：

```systemverilog
typedef struct packed {
    npc_op_t   npc_op;
    logic      reg_write;
    alu_op_t   alu_op;
    logic      mem_read;
    logic      mem_write;
    wb_sel_t   wb_sel;
    src2_sel_t src2_sel;
    logic      inst_illegal;
} ctrl_t;
```

`is_branch` 不单独放进 `ctrl_t`，由 `npc_op == NPC_BRANCH` 派生。
`inst_illegal` 放在 `ctrl_t` 里，方便以后随流水线一起打拍。

流水线 struct 同步更新 `instr_t` / `ctrl_t` 字段和宽度。

### 1.2 `decoder.sv`

对外接口：

```systemverilog
module decoder
    import cpu_pkg::*;
(
    input  word_t inst,
    output instr_t decoded,
    output word_t  imm,
    output logic   valid_encoding
);
```

职责：

- 按 RV32I 切分 `opcode/rd/funct3/rs1/rs2/funct7`；
- 实例化 `imm_gen`，对外隐藏 `imm_type`；
- 输出 `valid_encoding`；
- 删除 `instr_index`、`opcode_illegal`。

`valid_encoding` 的当前定义：

> 该 32 位编码是否属于本批接受的 7 条指令，且 `funct3/funct7` 组合合法。

后续扩展完整 RV32I 时，再把它扩展为标准合法性，并在 `ctrl` 里区分“合法但未实现”。

`decoder` 内部：

```systemverilog
imm_type_t imm_type;
assign imm_type = decode_imm_type(inst[6:0]);

imm_gen u_imm_gen (
    .inst(inst),
    .imm_type(imm_type),
    .imm(imm)
);
```

`funct7` 仍然要单独输出：

```systemverilog
assign decoded.funct7 = inst[31:25];
```

因为 I 型移位指令的 `funct7` 包含在 `imm[11:5]` 里，但 `ctrl` 仍需要它来选择 `SLLI/SRLI/SRAI`。

### 1.3 `imm_gen.sv`

```systemverilog
module imm_gen
    import cpu_pkg::*;
(
    input  word_t     inst,
    input  imm_type_t imm_type,
    output word_t     imm
);
```

支持：

```text
IMM_I   -> sign_extend(inst[31:20])
IMM_S   -> sign_extend({inst[31:25], inst[11:7]})
IMM_B   -> sign_extend({inst[31], inst[7], inst[30:25], inst[11:8], 1'b0})
IMM_J   -> sign_extend({inst[31], inst[19:12], inst[20], inst[30:21], 1'b0})
IMM_NONE-> 0
```

规则：

- I/S/B/J 都做符号扩展；
- B/J 的 bit0 在 `imm_gen` 里补 0；
- NPC 里不再左移；
- 非法/未知格式输出 0。

本批不处理移位指令；后续移位立即数仍按 `IMM_I` 处理，`imm` 包含 `funct7`，ALU 只取低 5 位。

### 1.4 `ctrl.sv`

输入：

```systemverilog
input  logic [6:0] opcode,
input  logic [2:0] funct3,
input  logic [6:0] funct7,
input  logic       valid_encoding,
output ctrl_t      ctrl
```

`inst_illegal` 由 `ctrl` 产生：

```text
inst_illegal = !valid_encoding
```

因为本批所有未实现指令都算 illegal。

当前 7 条控制表：

| 指令 | `npc_op` | `reg_write` | `alu_op` | `src2_sel` | `wb_sel` | `mem_read` | `mem_write` |
| :-- | :-- | :-- | :-- | :-- | :-- | :-- | :-- |
| `add` | PLUS4 | 1 | ADD | RS2 | ALU_OUT | 0 | 0 |
| `addi` | PLUS4 | 1 | ADD | IMM | ALU_OUT | 0 | 0 |
| `beq` | BRANCH | 0 | EQ | RS2 | x | 0 | 0 |
| `lw` | PLUS4 | 1 | ADD | IMM | R_DATA | 1 | 0 |
| `sw` | PLUS4 | 0 | ADD | IMM | x | 0 | 1 |
| `jal` | JAL | 1 | NOP | x | PC_PLUS4 | 0 | 0 |
| `jalr` | JALR | 1 | ADD | IMM | PC_PLUS4 | 0 | 0 |
| illegal | PLUS4 | 0 | NOP | x | x | 0 | 0 |

非法时：

```text
inst_illegal = 1
reg_write    = 0
mem_read     = 0
mem_write    = 0
alu_op       = ALU_NOP
npc_op       = PLUS4   // 由 NPC 的 inst_illegal 覆盖为 hold
```

本批 `ctrl` 不拆 `alu_ctrl`，先保持单表；后续完整 RV32I 再考虑分层。

### 1.5 `alu.sv`

本批操作：

```text
ALU_ADD -> alu_out = alu_src1 + alu_src2
ALU_EQ  -> cmp_result = (alu_src1 == alu_src2); alu_out = 0
ALU_NOP -> alu_out = 0; cmp_result = 0
```

输出：

```systemverilog
output word_t alu_out,
output logic  cmp_result
```

- `cmp_result` 是 1 位；
- `ALU_EQ` 时有效；
- `ALU_ADD` / `ALU_NOP` 时必须为 0；
- 删除 `zero_f/neg_f/overflow_f/carry_f`，不再参与分支。

分支条件：

```text
is_branch    = (ctrl.npc_op == NPC_BRANCH)
branch_taken = alu.cmp_result & is_branch
```

`jalr` 的目标 `rs1 + imm` 走 ALU：

- `alu_op = ALU_ADD`
- `alu_src1 = rs1_data`
- `alu_src2 = imm`
- `alu_out -> jalr_target`

ALU 必须读本条指令执行前的 `rs1_data`；`rd == rs1` 不能先写回再算目标。

### 1.6 `npc.sv`

接口：

```systemverilog
module npc
    import cpu_pkg::*;
(
    input  word_t    inst_pc,
    input  npc_op_t  npc_op,
    input  logic     branch_taken,
    input  word_t    pc_offset,
    input  word_t    jalr_target,
    input  logic     inst_illegal,
    output word_t    pc_plus4,
    output word_t    next_pc
);
```

语义：

```text
inst_illegal -> next_pc = inst_pc
NPC_PLUS4    -> next_pc = inst_pc + 4
NPC_BRANCH   -> next_pc = branch_taken ? inst_pc + pc_offset : inst_pc + 4
NPC_JAL      -> next_pc = inst_pc + pc_offset
NPC_JALR     -> next_pc = jalr_target & 32'hFFFF_FFFE
```

说明：

- `inst_pc` 是“正在解析的指令的 PC”；单周期就是当前 PC，流水线里是 ID/EX 的 PC。
- `pc_offset` 是 B/J 型字节偏移，已符号扩展，bit0=0；NPC 不再移位。
- `jalr_target` 是 ALU 的 `rs1 + imm` 原始结果；NPC 只清 bit0。
- `inst_illegal` 优先级最高。
- `pc_plus4 = inst_pc + 4`，供 jal/jalr 写 link。
- `NPC_PLUS4` 的命名与 `pc_plus4` 保持一致，不用 `NPC_PLUS_4`。

### 1.7 `regfile.sv`

- 端口统一命名：`rs1 / rs2 / rd`；
- 读：组合读，`x0` 恒 0；
- 写：上升沿，`reg_write=1 && rd != 0`；
- 删除 `rd_sel`，`rd` 直接来自 `inst[11:7]`；
- `jalr` 的 `rd == rs1` 必须读旧值；单周期“组合读 + 沿写”满足。

### 1.8 `datam.sv`

- 地址模型：**字节寻址**，字索引为 `addr[DMEM_ADDR_W+1:2]`；
- 本批只支持整字 `lw/sw`，不实现 `wstrb` / 子字访问；
- `mem_read=1` 时组合输出 `r_data`，否则 `r_data=0`；
- `mem_write=1` 时上升沿写入；
- 文档先约定 **小端序**，避免后续加 `lb/lh/sb/sh` 时返工；
- `addr[1:0] != 0` 只做仿真断言，行为后续再议。

### 1.9 `instrm.sv`

- 本批收尾阶段执行改名：`instrm -> instm`，`instr_addr -> inst_addr`；
- 同步 `cpu_top`、`tests/utils/cocotb_utils.py`、契约测试和文档；
- `inst_addr` 是字节地址，内部取字索引 `inst_addr[IMEM_ADDR_W+1:2]`；
- 没有压缩指令，取指固定 32 位；
- PC 4 字节对齐只做断言。

### 1.10 `cpu_top.sv`

顶层只做实例化和连线：

- 删除 `ext`、`cond`、`rd_sel` 及对应 MUX；
- 实例化 `decoder`，拿 `decoded / imm / valid_encoding`；
- 实例化 `ctrl`，拿 `ctrl_t`；
- `inst_illegal` 直接由 `ctrl.inst_illegal` 输出到顶层；
- `reg_dst = decoded.rd`；
- `branch_taken = alu.cmp_result & (ctrl.npc_op == NPC_BRANCH)`；
- `jalr_target = alu.alu_out`；
- `wb_data` MUX：`ALU_OUT / R_DATA / PC_PLUS4`；
- `npc` 接 `inst_pc / pc_offset / jalr_target / inst_illegal`。

不把合法/非法判断、安全控制、分支条件散落在 `cpu_top`。

---
