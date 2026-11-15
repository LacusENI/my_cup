# 演进路线图

> 当前基线：**`v0.4.0a2`**（RV32I M2 SYSTEM / 停机语义，单周期）。
> 当前目标：**`v0.4.0`**（完整 RV32I 基础指令集，单周期）。
> `v0.5.0` 之后的流水线、forwarding、分支预测等内容，等 `v0.4.0` 完成后再议。

本文只保留长期方向和阶段划分。当前版本的具体任务、顺序、风险和完成标准见
[`version/v0.4.0/plan.md`](version/v0.4.0/plan.md)。

---

## 1. 当前阶段：v0.4.0 完整单周期

目标：

> 完成 RV32I 基础指令集的单周期实现，并建立可回归的功能与性能基线。

范围：

```text
RV32I 基础整数指令
lui / auipc
全部 OP / OP-IMM
全部 branch
lb / lbu / lh / lhu / lw
sb / sh / sw
fence
ecall / ebreak（当前按 halt 约定）
```

不包含：

```text
C 扩展
M / A / F / D
CSR / trap / 特权级
中断
流水线
```

### 批次概览

| 批次 | 主题 | 目标 |
| :-- | :-- | :-- |
| M1 | U 型指令 | `lui` / `auipc` |
| M2 | SYSTEM / 停机 | `fence` / `ecall` / `ebreak` / `halt` |
| M3 | OP / OP-IMM | 剩余算术、逻辑、移位、比较指令 |
| M4 | Branch / BRU | 全部 branch，跳转目标集中到 BRU |
| M5 | Load / Store / LSU | 子字访存、`wstrb`、端序、对齐 |
| M6 | 验证与基线 | trace、汇编程序、ISS 差分、CPI/关键路径 |

详细任务、依赖和验收标准见 [`version/v0.4.0/plan.md`](version/v0.4.0/plan.md)。

### 完成标准

- RV32I 基础指令集全部实现；
- 单指令、边界、program 级测试通过；
- `mycup lint` 0 warning，`mycup test` 全绿，`mycup prog` 通过；
- `halt` / `halt_cause` 行为稳定；
- 建立 CPI / 关键路径基线；
- 文档与测试覆盖表同步；
- 打 `v0.4.0` tag。

---

## 2. 后续阶段

以下内容只保留方向，不在当前计划内展开：

```text
v0.5.0  简单流水线（无 forwarding，仅 stall）
v0.6.0  forwarding
...
```

`v0.5.0` 的具体范围、冒险策略和验证方式，等 `v0.4.0` 完成后再重新规划。

---

## 3. 工程规则

- 当前实现版本和设计文档分离：`docs/version/v0.4.0/` 保存本版本计划和设计，`docs/units/` 保存当前 RTL 单元接口。
- 历史版本放入 `docs/archive/`，不参与当前实现契约。
- 每完成一个批次，更新测试、`docs/units/` 和版本计划状态。
- 发布 tag 只在阶段完成后打；中间批次用 commit / milestone 记录，不单独占 release 版本号。
