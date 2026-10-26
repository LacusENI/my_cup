# RTL描述

version: v0.4

## add rd, rs1, rs2
```
R[rd] = R[rs1] + R[rs2]
```

## addi rd, rs1, imm
```
imm12: i12, imm = imm12 as i32
R[rd] = R[rs1] + immm
```

## beq rs1, rs2, offset
```
offset: i13, imm = offset as i32
if R[rs1] == R[rs2]:
    PC = PC + imm
else:
    PC = PC + 4
```

## lw rd, offset(rs1)
```
offset: i12, imm = offset as i32
R[rd] = M[R[rs1] + imm]
```

## sw rs2, offset(rs1)
```
offset: i12, imm = offset as i32
M[R[rs1] + imm] = R[rs2]
```

## jal rd, offset
```
offset: i21, imm = offset as i32
R[rd] = PC + 4
PC = PC + imm
```

## jalr rd, offset(rs1)
```
offset: i12, imm = offset as i32
target = (R[rs1] + imm) & 32'hFFFF_FFFE
R[rd]  = PC + 4
PC     = target      
```

## lui rd, hi
```
hi: u20, imm = hi << 12
R[rd] = imm
```
