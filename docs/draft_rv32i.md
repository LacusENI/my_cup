# 关于 v0.3-rv32i 的设计初稿

>[!review]
> **本批范围**：add、addi、beq、lw、sw、jal、jalr。
> 下面的批注只针对这 7 条；lui/auipc、sub、逻辑/移位/比较、子字访存、其他分支、fence/ecall/ebreak 等留到后续批次，不在本批阻塞项内。
> 因此像 alu_op 扩到 5 位、src1_sel、wstrb 这些“完整 RV32I”才需要的东西，这里只标成后续项。

## 各模块

### ALU
1. 去掉 cond 模块
2. branch 类指令走 ALU，ALU 输出 `branch_taken`
3. `alu_op` 增加一个 NOP，输出保持零
4. `jalr` 的 `R[src1] + imm` 走 ALU

>[!review]
> 当前 7 条只需要 ADD、BEQ、NOP 三个操作，4 位 alu_op 够用；等补完整 RV32I 时再考虑扩到 5 位或拆 branch_op。
> `branch_taken` 在非分支指令上必须为 0（NOP 默认输出 0 即可），否则 lw/sw/jal 可能误触发 BRANCH。
> beq 用独立比较、不做“减法+flags”的方向是对的；比较的是 32 位全等，且不写 rd。
> jalr 的 `rs1 + imm` 走 ALU 可以，但 ALU 必须读到本条指令执行前的 `rs1_data`，即使 `rd == rs1`。
> `alu_op=NOP` 输出 0；当前 7 条没有 lui，所以不会出现“NOP + ALU_OUT 写 0”的问题；后续加 lui 时要单独处理。

### NPC
1. `npc_op`: `PLUS_4` | `BRANCH` | `DIRECT` | `RELATIVE`
2. `cond_jmp` 改名为 `branch_taken`
3. `jmp_target` 改为32位，用于接 `jalr` 的 `R[src1] + imm`
4. `jmp_target` 在 npc 模块内部将最低位置零
5. `jmp_offset` 改为32位，接 imm，删去 `jmp_reg`

>[!review]
> `DIRECT / RELATIVE` 语义容易歧义，建议直接改成 `NPC_PLUS4 / NPC_BRANCH / NPC_JAL / NPC_JALR`。
> 当前对应关系：普通指令=PLUS4，beq=BRANCH，jal=JAL，jalr=JALR。
> `jmp_offset` 已经是字节偏移（B 型 13 位、J 型 21 位，bit0 已为 0），NPC 里不要再 `<< 2`。
> `jmp_target` 只给 jalr 用，建议改名 `jalr_target`；`& ~1` 只清 bit0，bit1 的 4 字节对齐另做断言/后续 trap。
> BRANCH 不成立时必须是 `pc + 4`；非分支指令的 `branch_taken` 必须为 0。
> `pc_plus_4` 要用本条指令的 PC 计算；单周期没问题，上流水线时不能直接用 IF 级最新 PC。

### EXT
1. 不再需要 ext 模块，立即数统一32位，在译码时即完成扩展

>[!review]
> 当前 7 条需要 I（addi/lw/jalr）、S（sw）、B（beq）、J（jal）四种立即数；U 型（lui/auipc）后续再加。
> 建议保留一个 `imm_gen` 子模块（输入 inst + imm_type，输出 imm），方便单独测负立即数。
> I/S/B/J 都做符号扩展；B/J 的 bit0 在生成时补 0，NPC 不要再移位。
> `imm_type` 建议单独 typedef，不要复用指令类别名。

### REGFILE
1. regfile 模块基本不用改
2. 加一个类型名 `reg_t` 替代 `logic [4:0]`

>[!review]
> “基本不用改”成立；补两条：x0 恒 0，写 x0 丢弃；写地址直接来自 `inst[11:7]`，不再需要 `rd_sel`。
> `jalr` 在 `rd == rs1` 时要读旧值；单周期“组合读 + 沿写”满足，流水线时要防止把当前指令自己的 WB 结果前递给自己。
> `reg_t` 建议定义为 `logic [4:0]`；端口统一命名为 `rs1/rs2/rd`。

### DATAM
1. 关于小端序：

>[!review]
> 当前 7 条只有 lw/sw 整字访问，可以先不做 `wstrb`/子字读写；但地址模型要现在定：M 是字节寻址，字索引是 `addr[ADDR_W+1:2]`。
> 这里第 1 条还没写完，建议补上具体字节映射：`addr[1:0]=0 -> [7:0]`，`=1 -> [15:8]`，依次类推。
> lw/sw 要求 4 字节对齐；建议至少加仿真断言，后续再决定是否 trap。
> 整字访问下小端/大端不可见；但建议现在就在文档里标成小端，避免后面加 lb/lh/sb/sh 时返工。
> 子字访问（lb/lh/lbu/lhu/sb/sh）和 `wstrb` 属于后续批次，不在本批范围。

### INSTRM
1. RISC-V 中 instruction 的简写更常见 inst 而非 instr
2. 建议 `instrm`, `instr_addr` 改名为 `instm`, `inst_addr`

>[!review]
> `instm/inst_addr` 改名可以，但记得同步 `cpu_top` 和 `tests/cocotb_utils.py` 里的 `u_instrm` 等引用。
> `inst_addr` 是字节地址，内部仍用 `inst_addr[IMEM_ADDR_W+1:2]` 取字；PC 必须 4 字节对齐。
> 当前没有压缩指令，取指固定 32 位，不需要处理 16 位对齐。

### DECODER
1. decoder 输出：
    - `opcode_t opcode`
    - `funct3_t funct3, funct7_t funct7`
    - `reg_t rd, rs1, rs2`
    - `word_t imm`
2. decoder 内部可加一个专门负责立即数的模块
    - 输入 `inst` 和 `inst_type`
    - 输出 `imm`
3. 删除：`instr_index`，`jmp_target` 接 `imm`

>[!review]
> 输出字段没问题；当前批次里 `funct7` 只有 add 用得到（以后区分 add/sub），其他指令不要拿 `funct7` 当操作码。
> `imm_gen` 的输入建议叫 `imm_type`（I/S/B/J/U），不要叫 `inst_type`，避免和指令类别混淆。
> 当前 7 条需要 I/S/B/J 四种；U 型后续再加。
> 建议预留 `illegal` 输出；本批至少明确“未定义指令当前按 NOP 处理”，不要让行为悬空。
> 删除 `instr_index` 是对的；`jmp_target` 不再由 decoder 产生，改由 ALU 给 jalr。

### CTRL
1. 删除：`cond_type`, `ext_type`, `rd_sel`
2. 控制信号以 `opcode` 为一组，ctrl 分配各组的共同信号
3. 增加子模块以分配组间差异信号
4. 例如，`OP_IMM` 类指令的控制信号除了 `alu_op` 都相同
5. 增加 `alu_ctrl` 专项负责分配 `alu_op`
6. ctrl 完成除 `alu_op` 之外的信号分配

>[!review]
> 删除 `cond_type/ext_type/rd_sel` 是对的：RV 的 rd 永远是 `inst[11:7]`，立即数格式由 opcode 决定，分支条件由 ALU 的 `branch_taken` 给出。
> 当前 7 条不需要 `src1_sel`（没有 lui/auipc），ALU src1 固定 `rs1_data`；等后续加 U 型再补。
> 需要保留/明确的控制：`reg_write`、`mem_read`、`mem_write`、`wb_sel`（ALU/MEM/PC4）、`src2_sel`（rs2/imm）、`npc_op`、`alu_op`。
> `OP_IMM` 组内“除 alu_op 外都相同”对 addi 成立；后续加 slli/srli/srai 时移位量来自 `imm[4:0]`，ALU 内部取低 5 位即可。
> `LOAD/STORE` 当前只有 lw/sw，组内同构；后续加 lb/lh/sb/sh 时需要 `mem_size/load_type`。
> `alu_ctrl` 负责 `alu_op` 的分层很好；注意后续 6 种分支比较也要由它分配。

## 各指令(数据通路)

### add 
```
inst -> [decoder] -> rd, rs1, rs2

rs1, rs2 -> [regfile] -> rs1_data, rs2_data
    -> alu_src1, alu_src2 -> [alu] -> alu_out 
    -> wb_data

rd, wb_data -> [regfile]
```

>[!review]
> 数据通路正确。
> 当前只实现 add 时，ctrl 用 `opcode=OP、funct3=000、funct7=0000000` 选中 ADD；sub 后续再加。
> 32 位加法按模 2^32 回绕，不需要溢出异常；写 x0 由 regfile 丢弃。

### addi
```
inst -> [decoder] -> rd, rs1, imm

rs1 -> [regfile] -> rs1_data

rs1_data, imm -> alu_src1, alu_src2
    -> [alu] -> alu_out -> wb_data

rd, wb_data -> [regfile]
```

>[!review]
> 数据通路正确。
> `imm` 必须是 I 型 12 位符号扩展到 32 位；不要直接把 12 位信号参与 32 位加法（Verilog 会零扩展，负立即数会算错）。
> addi 不产生溢出异常；结果按 32 位回绕。
> `rd == rs1` 时 ALU 读旧值，写回在时钟沿，单周期没问题。

### beq
```
inst -> [decoder] -> rs1, rs2, imm

rs1, rs2 -> [regfile] -> rs1_data, rs2_data
    -> alu_src1, alu_src2 -> [alu] -> branch_taken

pc, imm, branch_taken -> [npc] -> next_pc
```

> branch 类指令的比较运算走 alu，使用独立比较操作，
> 不使用减法+flags的算法
> `pc + imm` 走 npc 模块的加法器

>[!review]
> 数据通路正确。
> 目标 = 本条指令 PC + `sext(imm13)`；imm13 是字节偏移且 bit0=0，NPC 不要再左移。
> 不成立时 `next_pc = pc + 4`；非分支指令的 `branch_taken` 必须为 0。
> 上流水线时，beq 的 PC 要用 ID/EX 里保存的指令 PC，不是 IF 级当前 PC。

### lw
```
inst -> [decoder] -> rd, rs1, imm

rs1 -> [regfile] -> rs1_data

rs1_data, imm -> [alu] -> alu_out
    -> addr -> [datam] -> r_data
    -> wb_data

rd, wb_data -> [regfile]
```

> Load-Store 指令的地址计算 `R[rs1] + imm` 走 alu

>[!review]
> 数据通路正确。
> 地址 = `rs1_data + sext(imm12)`，按字节地址送 datam，内部再取字索引；要求 4 字节对齐。
> 当前整字访问下不用考虑字节序；文档里先约定小端，为后续子字访问铺路。
> `wb_sel` 选 `r_data`；`rd == rs1` 时读旧值。

### sw
```
inst -> [decoder] -> rs1, rs2, imm

rs1, rs2 -> [regfile] -> rs1_data, rs2_data

rs1_data, imm -> [alu] -> alu_out -> addr

rs2_data, addr -> [datam]
```

>[!review]
> 数据通路正确。
> 地址 = `rs1_data + sext(imm12)`；写入数据是 `rs2_data`，不是 rd。
> sw 不写寄存器，`reg_write=0`；要求 4 字节对齐。
> 后续加 sb/sh 时才需要 `wstrb` 和 `mem_size`。

### jalr
```
inst -> [decoder] -> rd, rs1, imm

rs1, imm -> [alu] -> alu_out -> jmp_target

pc -> [npc] -> pc_plus_4 -> wb_data
wb_data, rd -> [regfile]

jmp_target -> [npc] -> next_pc
```

> 跳转目的地址 `R[rs1] + imm` 的计算走 alu,
> `alu_out` 接 npc 的 `jmp_target`
> npc 输出 `pc + 4` 的值，接 `wb_data`

>[!review]
> 数据通路正确，`asm.md` 里的同时赋值语义也是对的。
> 关键：target 必须用旧的 `rs1_data` 计算；`rd == rs1` 时不能先写回再算目标。
> target 只清 bit0；RV32I 还要求 4 字节对齐（bit1=0），建议加断言或后续 trap。
> link = 本条指令 PC + 4；上流水线时用指令 PC，不是 IF 级当前 PC。

### jal
```
inst -> [decoder] -> rd, imm

pc -> [npc] -> pc_plus_4 -> wb_data
rd, wb_data -> [regfile]

pc, imm -> pc, jmp_offset -> [npc] -> next_pc
```

> `pc + 4` 和 `pc + imm` 走 npc 的加法器，
> `imm` 接 `jmp_offset`，npc 执行 `pc = pc + imm`，
> npc 输出 `pc + 4` 的值，接 `wb_data`

>[!review]
> 数据通路正确。
> link 用旧 PC+4；target 用旧 PC + `sext(imm21)`；offset 是字节偏移且 bit0=0，NPC 不要再左移。
> jal 不经过 ALU，ALU 可以保持 NOP；`wb_sel` 选 `pc_plus_4`。
> rd 可以是 x0（伪指令 j），regfile 会丢弃写入；不要硬编码 x1 或 x31。
> `jal` 代码块里的 `pc, imm -> pc, jmp_offset` 建议改成 `pc, imm -> jmp_offset -> [npc]`，避免读成两个源。

>[!review]
> 文档层面：`asm.md` 里的 `> 0.3` / `> v0.4` 建议移到单独的“变更记录”；这份 draft 建议放到 `docs/rv32i/microarch.md` 并加入 `docs/README.md` 索引；`inst-list.md` 的 “Save” 建议改成 “Store”。
> 这些不影响本批 RTL，只是后面整理文档时一起处理。
