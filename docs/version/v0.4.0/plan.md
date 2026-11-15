# v0.4.0 实施计划

> 阶段目标：完成 RV32I 基础指令集的单周期实现。
> 长期路线见 [`docs/roadmap.md`](../../roadmap.md)。
> 备注：设计决策在开发过程中可能有变更。

## 1. 范围

实现：

```text
lui / auipc
fence / ecall / ebreak
全部 op / op-imm
全部 branch
全部 load / store
```

---

## 2. 批次

### M1 · U 型指令 (版本号 `0.4.0a1`)

- [x] `lui`：增加 `WB_SEL_IMM`，立即数直接进入写回通路
- [x] `auipc`：`pc + imm` 走 npc 模块
- [x] npc 模块增加输出端口 `pc_plus_imm`
- [x] decoder：增加 U 型立即数
- [x] ctrl：增加 `lui` / `auipc` 控制项
- [x] 更新汇编器、单指令测试、`docs/units/`

### M2 · SYSTEM / 停机语义 (版本号 `0.4.0a2`)

- [x] `fence`：当前内存模型下等效 `nop`
- [x] `ecall` / `ebreak`：当前无特权架构下仅停机
- [x] `cpu_top` 将 `inst_illegal` 替换为 `halt` + `halt_cause`
- [x] `halt == 0` 表示未停机，`halt_cause` 只在 `halt == 1` 时有效
- [x] 不使用 `HALT_NONE`
- [x] `halt_cause` 异常码对齐 `mcause`：

  ```text
  HALT_INST_ADDR_ERR  = 4'd0
  HALT_ILLEGAL_INST   = 4'd2
  HALT_EBREAK         = 4'd3
  HALT_LOAD_ADDR_ERR  = 4'd4
  HALT_STORE_ADDR_ERR = 4'd6
  HALT_ECALL          = 4'd11
  ```

- [x] 严格 4 字节指令对齐，无 C 扩展
- [x] `halt` 优先级高于 `redirect`
- [x] 更新 `npc` / `ctrl` / `cpu_top` / 测试和探针

### M3 · OP / OP-IMM

- [ ] 增加 `alu_ctrl`，专门生成 `alu_op`
- [ ] R 型：`sub`、`and`、`or`、`xor`、`sll`、`srl`、`sra`、`slt`、`sltu`
- [ ] I 型：`andi`、`ori`、`xori`、`slti`、`sltiu`、`slli`、`srli`、`srai`
- [ ] 更新 ALU、decoder、ctrl、单指令测试（汇编文本由 `llvm-mc` 编码）
- [ ] 补充算术边界、移位量、符号/零扩展测试

### M4 · Branch / BRU

- [ ] 实现 `bne`、`blt`、`bge`、`bltu`、`bgeu`
- [ ] 新增 `bju`（branch/jump unit）
  - 输入：`jalr_target`、`cmp_result`、`pc_plus_imm`、`bru_op`
  - 输出：`redirect`、`redirect_target`
  - `jalr` 跳转目标（`R[rs1] + imm`）由 ALU 计算
  - `jal` / branch 跳转目标（`pc + imm`）由 `pcru` 计算
- [ ] `npc` 后续只负责 redirect：

  ```text
  pc_stall = halt
  next_pc  = redirect ? redirect_target : pc_plus4
  ```

- [ ] `jal` / `jalr` 的 link 保持 `pc_plus4 -> wb_data`
- [x] 检查 branch/jal/jalr 目标 4 字节对齐
- [ ] 更新 `test_bru`、`test_npc`、`test_inst`

### M5 · Load / Store / LSU

- [ ] 新增 `lsu`（load-store unit）
- [ ] `datam` 增加 `wstrb`
- [ ] 实现 `lb` / `lbu` / `lh` / `lhu` / `lw`
- [ ] 实现 `sb` / `sh` / `sw`
- [ ] 小端序
- [ ] `lb/lh` 符号扩展，`lbu/lhu` 零扩展
- [ ] `sb/sh` 只写目标字节/半字
- [x] `lw/sw` 4 字节对齐；load/store 未对齐分别进入 halt cause
- [ ] 更新 `datam` 单测、ISA 测试、汇编器和 program 测试

### M6 · 验证与基线

- [ ] 指令 trace：PC / 指令 / 写回 / 访存
- [ ] 汇编程序级测试
- [ ] 软件参考模型（Python ISS）+ 差分测试
- [ ] CPI 和关键路径测量方法
- [ ] 更新 `docs/units/`、`docs/ctrl/`、`docs/version/v0.4.0/`
- [ ] 发布前回归：`mycup lint` / `mycup test` / `mycup prog`

---

## 3. 关键约束

- `halt` 是 1 位有效信号；`halt_cause` 只在 `halt=1` 时解读。
- `mcause` 是未来的 CSR 寄存器，不是 `datam` 内存。
- 无 C 扩展：指令地址严格 4 字节对齐。
- `lw/sw` 地址 4 字节对齐；`lh/lhu/sh` 2 字节；`lb/lbu/sb` 任意字节。
- `jalr` 目标由 BRU 计算；link 使用 `pc_plus4`。
- 子字访存使用 word memory + `wstrb`。
- 中途不引入流水线；流水线从 `v0.5.0` 再议。

---

## 4. 风险

| 风险 | 应对 |
| :-- | :-- |
| `halt` 替换旧非法信号波及大量测试 | M2 单独提交，先迁移接口 |
| `wstrb` / 端序 / 符号扩展出错 | M5 单独分支，先做 datam 单测 |
| BRU 与 NPC 重构混淆 target/link | 先单指令验证，再接后续结构 |
| 分支集合扩大 | BRU 统一 target，ALU 负责比较 |
| 单指令正确但组合错误 | 增加 program 级和差分测试 |

---

## 5. 完成标准

- [ ] RV32I 基础指令集全部实现
- [ ] 单指令、边界、program 级测试通过
- [x] `halt` / `halt_cause` 行为稳定
- [ ] `mycup lint` 0 warning
- [ ] `mycup test` 全绿
- [ ] `mycup prog` 通过
- [ ] CPI / 关键路径基线完成
- [ ] 文档与测试覆盖表同步
- [ ] 打 `v0.4.0` tag
