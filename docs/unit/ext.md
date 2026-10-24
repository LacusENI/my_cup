version: 0.2

date: 2026/10/24

## 描述

立即数扩展单元。当前把 16 位立即数扩展成 32 位，支持零扩展和符号扩展。

## 端口

input
- `imm16(16)`：16 位立即数
- `ext_type(ext_type_t)`：扩展类型

output
- `imm32(32)`：扩展后的 32 位立即数

## 扩展类型

| `ext_type` | 行为 |
| :-- | :-- |
| `EXT_TYPE_ZERO_EXT` | 零扩展 |
| `EXT_TYPE_SIGN_EXT` | 符号扩展 |

## 说明

- 当前对应 MIPS I 型 16 位立即数；
- 切 RV32I 时需要扩展为 I/S/B/U/J 五种立即数生成。
