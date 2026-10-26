1. 在 RV32I 中所有的立即数都在 ID 阶段解析并扩展成 32 位
2. 继 1，decoder 负责拼接立即数，输出 imm（32位）
3. 继 2，不再需要 imm16->imm32 的 ext 模块
4. 继 2，decode 不需要输出 instr_index，npc 的 jmp_target 直接接 imm
5. npc 的 jmp_offset 接 imm (32位) 
6. jalr 不再指定 $ra，删除 rd_sel 以及对应的 mux
7. 我觉得 jalr 的 target = R[rs1] + imm 应当走 ALU