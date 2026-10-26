# RTL描述

> 关于

version: v0.4

## add rd, rs1, rs2
```
R[rd] = R[rs1] + R[rs2]
```

## addi rd, rs1, imm
```
imm: i12
R[rd] = R[rs1] + imm as i32
```

## beq rs1, rs2, offset
```
offset: i13
if R[rs1] == R[rs2]:
    PC = PC + offset as i32
else:
    PC = PC + 4
```

## lw rd, offset(rs1)
```
offset: i12
R[rd] = M[R[rs1] + offset as i32]
```

## sw rs2, offset(rs1)
```
offset: i12
M[R[rs1] + offset as i32] = R[rs2]
```

## jal rd, offset
```
offset: i21
R[rd] = PC + 4
PC = PC + offset as i32
```

## jalr rd, offset(rs1)
```
offset: i12
R[rd] = PC + 4
PC = (R[rs1] + offset) & ~1
```

## lui rd, imm
```
imm: u20
R[rd] = imm << 12
```
