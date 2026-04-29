| instr |   op    |  funct  | npc_op | src2_sel | reg_write | rd_sel |  wb_sel  | alu_op | cond_type | ext_type | mem_read | mem_write | mem_size |
| :---: | :-----: | :-----: | :----: | :------: | :-------: | :----: | :------: | :----: | :-------: | :------: | :------: | :-------: | :------: |
| addu  | 00 0000 | 10 0001 | plus4  |   rs2    |     1     |   rd   |  alu_out |  add   |     x     |    x     |    0     |     0     |    x     |
| addiu | 00 1001 |    x    | plus4  |   imm    |     1     |   rt   |  alu_out |  add   |     x     |  z_ext   |    0     |     0     |    x     |
|  beq  | 00 0100 |    x    | branch |   rs2    |     0     |    x   |     x    |  sub   |    eq     |    x     |    0     |     0     |    x     |
|  lw   | 10 0011 |    x    | plus4  |   imm    |     1     |   rt   |  r_data  |  add   |     x     |  s_ext   |    1     |     0     |   word   |
|  sw   | 10 1011 |    x    | plus4  |   imm    |     0     |    x   |     x    |  add   |     x     |  s_ext   |    0     |     1     |   word   |
|  sh   | 10 1111 |    x    | plus4  |   imm    |     0     |    x   |     x    |  add   |     x     |  s_ext   |    0     |     1     |   half   |
|  sb   | 10 1111 |    x    | plus4  |   imm    |     0     |    x   |     x    |  add   |     x     |  s_ext   |    0     |     1     |   byte   |
|   j   | 00 0010 |    x    | direct |    x     |     0     |    x   |     x    |   x    |     x     |    x     |    0     |     0     |    x     |
|  jal  | 00 0011 |    x    | direct |    x     |     1     |   $ra  | pc_plus4 |   x    |     x     |    x     |    0     |     0     |    x     |
|  jr   | 00 0000 | 00 1000 |  $ra   |    x     |     0     |    x   |     x    |   x    |     x     |    x     |    0     |     0     |    x     |
