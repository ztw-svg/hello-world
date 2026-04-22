# 企业版预算填报模板与校验规则（可直接执行）

## 1. 目标

本说明用于指导财务/经营团队统一填写预算与实际数据，确保可直接用于：

- 自动生成预算执行图表
- 自动生成管理层 PPT
- 自动输出偏差分析建议
- 自动执行勾稽校验

## 2. 模板文件

- 模板路径：`templates/budget_input_template.csv`
- 推荐实际使用：Excel（字段与此 CSV 一致），每月导出 CSV 给脚本处理。

## 3. 字段说明（按重要级）

## 3.1 必填字段（无此字段脚本无法运行）

| 字段 | 说明 | 示例 |
|---|---|---|
| period | 会计期间，建议 `YYYY-MM` | 2026-01 |
| module | 模块：收入/成本/费用 | 收入 |
| budget_amount | 预算金额 | 1200000 |
| actual_amount | 实际金额 | 1180000 |

## 3.2 强烈建议字段（用于钻取与归因）

| 字段 | 说明 |
|---|---|
| org_id/org_name | 组织维度 |
| account_code/account_name | 科目维度 |
| product_id/product_name | 产品维度 |
| customer_id/customer_name | 客户维度 |
| project_id | 项目维度 |
| qty/unit_price | 量价分析 |
| owner | 责任人 |

## 3.3 口径字段

| 字段 | 可选值 | 说明 |
|---|---|---|
| version | BUDGET / ACTUAL / FORECAST | 数据版本 |
| scenario | BASE / OPTIMISTIC / CONSERVATIVE | 预算情景 |
| currency | CNY / USD / ... | 币种 |
| amount_type | 含税 / 不含税 | 统一口径必须一致 |

## 4. 填报校验规则（Excel 可做数据验证）

1. `period` 必须符合正则：`^20\d{2}-(0[1-9]|1[0-2])$`
2. `module` 只能在：收入、成本、费用
3. `budget_amount`、`actual_amount` 必须为数值
4. `amount_type` 在同一报表中必须一致
5. `version=ACTUAL` 时 `actual_amount` 不应为空
6. `version=BUDGET` 时 `budget_amount` 不应为空

## 5. 从模板到图表/PPT的操作流程

1. 财务BP按模板填报并月结锁数。
2. 导出 CSV 放到仓库根目录（或指定路径）。
3. 运行生成命令（见 README）。
4. 检查输出图表、建议文件、PPT。
5. 管理会前补充备注（一次性事项/策略变化）并定稿。

## 6. 分析建议输出口径（用于会中结论）

- 超预算（>=10%）：价格、销量、结构、汇率、一次性因素拆解。
- 低于预算（<=-10%）：交付节奏、确认节奏、目标合理性复核。
- 可控区间（-10%~10%）：滚动预测与风险前瞻。

## 7. 建议的月度职责分工（RACI）

- 财务：口径定义、勾稽审核、结论合并
- 业务：偏差解释、行动计划、责任人确认
- 管理层：阈值确认、资源调配、复盘要求

