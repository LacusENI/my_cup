`ifndef INSTR_VH
`define INSTR_VH

`define OP_ADDI
`define OP_ADDIU   6'b00_1001
`define OP_ANDI
`define OP_BEQ     6'b00_0100
`define OP_BGEZ
`define OP_BGTZ
`define OP_BLEZ
`define OP_BLTZ
`define OP_BNE
`define OP_J       6'b00_0010
`define OP_JAL     6'b00_0011
`define OP_LB
`define OP_LBU
`define OP_LH
`define OP_LHU
`define OP_LUI
`define OP_LW      6'b10_0011
`define OP_ORI
`define OP_SB      6'b10_1000
`define OP_SH      6'b10_1001
`define OP_SLTI
`define OP_SLTIU
`define OP_SW      6'b10_1011
`define OP_XORI

`define OP_R       6'b00_0000

`define FUNCT_ADD
`define FUNCT_ADDU 6'b10_0001
`define FUNCT_AND
`define FUNCT_JALR
`define FUNCT_JR   6'b00_1000
`define FUNCT_NOR
`define FUNCT_OR
`define FUNCT_SLL
`define FUNCT_SLLV
`define FUNCT_SLT
`define FUNCT_SLTU
`define FUNCT_SRA
`define FUNCT_SRAV
`define FUNCT_SRL
`define FUNCT_SRLV
`define FUNCT_SUB
`define FUNCT_SUBU
`define FUNCT_XOR

`endif
