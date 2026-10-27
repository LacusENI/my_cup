# v0.3-rv32i 单指令数据流

> 本文只画每条指令的**数据流**，控制信号（`ctrl`）省略，避免图太乱。
> 整体结构见 [datapath.drawio](datapath.drawio)，模块接口见 [units.md](units.md)。

## add

```mermaid
flowchart LR
    I[inst] --> DEC[decoder]
    DEC -->|rd / rs1 / rs2| RF[regfile]
    RF -->|rs1_data| ALU[ALU: ADD]
    RF -->|rs2_data| ALU
    ALU -->|alu_out| WB[wb mux]
    WB -->|wb_data| RF
```

## addi

```mermaid
flowchart LR
    I[inst] --> DEC[decoder]
    DEC -->|rd / rs1| RF[regfile]
    DEC -->|imm I| IMM[imm_gen]
    RF -->|rs1_data| ALU[ALU: ADD]
    IMM -->|imm32| ALU
    ALU -->|alu_out| WB[wb mux]
    WB -->|wb_data| RF
```

## beq

```mermaid
flowchart LR
    I[inst] --> DEC[decoder]
    DEC -->|rs1 / rs2| RF[regfile]
    DEC -->|imm B| IMM[imm_gen]
    RF -->|rs1_data| ALU[ALU: EQ]
    RF -->|rs2_data| ALU
    ALU -->|cmp_result| NPC[npc]
    IMM -->|pc_offset| NPC
    PC[pc] -->|inst_pc| NPC
    NPC -->|next_pc| PC
```

## lw

```mermaid
flowchart LR
    I[inst] --> DEC[decoder]
    DEC -->|rd / rs1| RF[regfile]
    DEC -->|imm I| IMM[imm_gen]
    RF -->|rs1_data| ALU[ALU: ADD]
    IMM -->|imm32| ALU
    ALU -->|addr| DM[datam]
    DM -->|r_data| WB[wb mux]
    WB -->|wb_data| RF
```

## sw

```mermaid
flowchart LR
    I[inst] --> DEC[decoder]
    DEC -->|rs1 / rs2| RF[regfile]
    DEC -->|imm S| IMM[imm_gen]
    RF -->|rs1_data| ALU[ALU: ADD]
    IMM -->|imm32| ALU
    ALU -->|addr| DM[datam]
    RF -->|rs2_data| DM
```

## jal

```mermaid
flowchart LR
    I[inst] --> DEC[decoder]
    DEC -->|rd| RF[regfile]
    DEC -->|imm J| IMM[imm_gen]
    IMM -->|pc_offset| NPC[npc]
    PC[pc] -->|inst_pc| NPC
    NPC -->|pc_plus4| WB[wb mux]
    WB -->|wb_data| RF
    NPC -->|next_pc| PC
```

## jalr

```mermaid
flowchart LR
    I[inst] --> DEC[decoder]
    DEC -->|rd / rs1| RF[regfile]
    DEC -->|imm I| IMM[imm_gen]
    RF -->|rs1_data| ALU[ALU: ADD]
    IMM -->|imm32| ALU
    ALU -->|jalr_target| NPC[npc]
    PC[pc] -->|inst_pc| NPC
    NPC -->|pc_plus4| WB[wb mux]
    WB -->|wb_data| RF
    NPC -->|next_pc| PC
```

## 非法指令

```mermaid
flowchart LR
    I[inst] --> DEC[decoder]
    DEC --> CTRL[ctrl]
    CTRL -->|inst_illegal| NPC[npc]
    NPC -->|next_pc = inst_pc| PC[pc]
```

非法时 `ctrl` 同时关闭 `reg_write`、`mem_read`、`mem_write`，所以不会写寄存器或内存。

---

## 备注

- `add/addi` 的 ALU 结果是写回数据；
- `lw/sw/jalr` 的 ALU ADD 结果是地址/target；
- `beq` 的 ALU 只产生 `cmp_result`；
- `jal` 不经过 ALU，ALU 保持 `ALU_NOP`；
- `pc_plus4` 始终由 NPC 从 `inst_pc` 计算，用于 `jal/jalr` 的 link；
- 分支目标使用本条指令的 `inst_pc + pc_offset`，不是 IF 级最新 PC。
