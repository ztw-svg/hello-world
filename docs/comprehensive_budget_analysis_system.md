# 全面预算分析系统设计方案（可生成图表与 PPT）

> 目标：搭建一个可落地的“预算-实际一体化分析系统”，覆盖资产负债表、利润表、所有者权益变动表、现金流量表，并支持收入、成本、费用等模块的明细/汇总分析，且保证全部勾稽关系自动校验。

## 1. 系统总体架构

## 1.1 分层架构

1. **数据层（ODS / DWD）**
   - 来源：ERP、总账、应收/应付、固定资产、资金系统、销售系统、采购系统、费用报销系统、人资薪酬系统。
   - 输出：统一会计科目、组织、项目、产品、客户、供应商、币种、期间、版本等标准维度。

2. **模型层（DWS）**
   - 明细事实表：预算明细、实际凭证明细、调整分摊明细。
   - 汇总事实表：按组织/科目/期间/版本/场景（月度、YTD、QTD）聚合。
   - 规则引擎：勾稽检查、口径映射、分摊规则、币种折算。

3. **分析层（ADS）**
   - 四大报表：资产负债表、利润表、所有者权益表、现金流量表。
   - 专题分析：收入、成本、费用、毛利、经营现金流、资本开支、营运资本。

4. **展现层（BI + 自动报告）**
   - 可视化：趋势图、瀑布图、结构图、桥图、热力图、散点图。
   - 自动 PPT：按管理层模板输出“执行摘要 + 各模块钻取页 + 异常说明页”。

## 1.2 版本与场景

- 版本（version）：`BUDGET`、`FORECAST`、`ACTUAL`。
- 场景（scenario）：`BASE`、`OPTIMISTIC`、`CONSERVATIVE`。
- 币种层级：本位币、集团汇报币。

---

## 2. 核心数据模型（表设计）

## 2.1 维度表

### 2.1.1 组织维度 `dim_org`

| 字段 | 类型 | 说明 |
|---|---|---|
| org_id | string | 组织编码 |
| org_name | string | 组织名称 |
| parent_org_id | string | 上级组织 |
| org_level | int | 组织层级 |
| legal_entity_flag | tinyint | 是否法人主体 |
| valid_from / valid_to | date | 生效区间 |

### 2.1.2 科目维度 `dim_account`

| 字段 | 类型 | 说明 |
|---|---|---|
| account_code | string | 科目编码 |
| account_name | string | 科目名称 |
| statement_type | string | BS/PL/EQ/CF |
| account_class | string | 资产/负债/权益/收入/成本/费用 |
| drcr_nature | string | 借增贷减/贷增借减 |
| is_leaf | tinyint | 是否末级科目 |
| cf_mapping_code | string | 现金流映射编码 |

### 2.1.3 期间维度 `dim_period`

| 字段 | 类型 | 说明 |
|---|---|---|
| period_key | string | YYYYMM |
| fiscal_year | int | 财年 |
| fiscal_quarter | string | 财季 |
| month_no | int | 月份 |
| period_start / period_end | date | 起止日期 |

### 2.1.4 其他业务维度

- `dim_product`（产品/品类/型号）
- `dim_customer`（客户/渠道/区域）
- `dim_supplier`（供应商/采购类别）
- `dim_project`（项目/合同）
- `dim_cost_center`（成本中心）
- `dim_currency`（币种、汇率类型）

## 2.2 事实表

### 2.2.1 预算明细事实表 `fact_budget_detail`

| 字段 | 类型 | 说明 |
|---|---|---|
| budget_id | string | 预算单号 |
| version | string | BUDGET/FORECAST |
| scenario | string | 场景 |
| period_key | string | 期间 |
| org_id | string | 组织 |
| account_code | string | 科目 |
| product_id / customer_id / project_id | string | 业务维度 |
| amount_lc | decimal(20,2) | 本位币金额 |
| amount_gc | decimal(20,2) | 集团币金额 |
| qty | decimal(20,4) | 数量 |
| unit_price | decimal(20,6) | 单价 |
| driver_code | string | 驱动因子 |
| input_source | string | 填报/系统计算 |

### 2.2.2 实际明细事实表 `fact_actual_gl`

| 字段 | 类型 | 说明 |
|---|---|---|
| voucher_id | string | 凭证号 |
| voucher_line | int | 分录行号 |
| period_key | string | 期间 |
| org_id | string | 组织 |
| account_code | string | 科目 |
| dr_amount / cr_amount | decimal(20,2) | 借/贷金额 |
| amount_signed | decimal(20,2) | 借贷符号化金额 |
| product_id / customer_id / supplier_id / project_id | string | 业务维度 |
| currency_code | string | 币种 |
| amount_lc / amount_gc | decimal(20,2) | 折算后金额 |

### 2.2.3 分摊调整事实表 `fact_adjustment`

| 字段 | 类型 | 说明 |
|---|---|---|
| adj_id | string | 调整单号 |
| adj_type | string | 分摊/重分类/抵销 |
| from_org / to_org | string | 分摊来源与去向 |
| account_code | string | 科目 |
| period_key | string | 期间 |
| amount | decimal(20,2) | 调整金额 |
| rule_id | string | 规则编号 |

### 2.2.4 报表汇总事实表 `fact_statement_snapshot`

| 字段 | 类型 | 说明 |
|---|---|---|
| statement_code | string | BS/PL/EQ/CF |
| line_code | string | 报表行编码 |
| version | string | 版本 |
| period_key | string | 期间 |
| org_id | string | 组织 |
| amount | decimal(20,2) | 金额 |
| ytd_amount | decimal(20,2) | 年累计 |
| yoy_amount | decimal(20,2) | 同比基数 |
| mom_amount | decimal(20,2) | 环比基数 |

---

## 3. 报表口径与勾稽关系（关键控制）

## 3.1 四大报表主勾稽

1. **资产负债表平衡**
   - `总资产 = 总负债 + 所有者权益`
2. **利润与权益勾稽**
   - `期末未分配利润 = 期初未分配利润 + 本期净利润 - 本期分配`
3. **现金流与资产负债表勾稽**
   - `现金及现金等价物净增加额 = 期末现金 - 期初现金`
4. **利润表与现金流（间接法）勾稽**
   - `经营活动现金流净额 = 净利润 + 非现金项目调整 ± 营运资本变动`

## 3.2 预算 vs 实际分析指标

- 差异额：`var_amt = actual - budget`
- 差异率：`var_rate = (actual - budget) / abs(budget)`
- 进度达成：`achv_rate = actual_ytd / budget_ytd`
- 同比增长：`yoy = (actual - last_year_actual) / abs(last_year_actual)`

## 3.3 收入-成本-费用联动

- 毛利：`gross_profit = revenue - cost_of_sales`
- 毛利率：`gross_margin = gross_profit / revenue`
- 期间费用率：`opex_ratio = (selling + admin + rnd + finance) / revenue`
- EBIT：`ebit = gross_profit - opex + other_income`
- EBITDA：`ebitda = ebit + depreciation + amortization`

## 3.4 自动校验规则表 `rule_reconciliation`

建议设计规则驱动校验：

| rule_id | rule_name | expression_sql | tolerance | severity |
|---|---|---|---:|---|
| R001 | 资产负债平衡 | total_asset - total_liab_eq | 0.01 | HIGH |
| R002 | 现金净增勾稽 | cf_net_increase - (cash_end-cash_begin) | 0.01 | HIGH |
| R003 | 利润权益勾稽 | re_end - (re_begin+net_profit-dividend) | 0.01 | HIGH |
| R004 | 收入成本匹配 | gross_profit - (rev-cogs) | 0.01 | MEDIUM |

校验结果表 `fact_recon_result`：`rule_id, period_key, org_id, diff_value, pass_flag, checked_at`。

---

## 4. 明细表与汇总表清单（建议）

## 4.1 明细层（用于追溯）

1. `fact_budget_detail`：预算录入最细颗粒。
2. `fact_actual_gl`：总账分录明细。
3. `fact_adjustment`：管理口径调整/分摊。
4. `fact_cashflow_tagged_detail`：现金流标签后的交易明细。
5. `fact_revenue_detail`：订单/发货/开票/回款链路。
6. `fact_cost_detail`：BOM、采购、制造费用、标准/实际差异。
7. `fact_expense_detail`：销售/管理/研发/财务费用明细。

## 4.2 汇总层（用于看板）

1. `agg_statement_monthly`：四大报表月度汇总。
2. `agg_budget_vs_actual`：预算/实际差异透视。
3. `agg_revenue_analysis`：收入结构（产品/区域/客户）。
4. `agg_cost_analysis`：单位成本、成本结构。
5. `agg_expense_analysis`：费用结构、费用率。
6. `agg_cashflow_bridge`：利润到现金流桥接。

---

## 5. 图表设计（管理层最常用）

1. **经营总览页**
   - KPI 卡：收入、毛利、净利润、经营现金流、ROE、资产负债率。
   - 趋势：收入/利润/现金流月度趋势（折线）。

2. **预算执行页**
   - 预算 vs 实际（簇状柱图 + 差异折线）。
   - 差异归因（瀑布图：价格、销量、结构、汇率、一次性事项）。

3. **收入分析页**
   - 按产品、区域、客户贡献（堆积柱图、帕累托）。

4. **成本费用页**
   - 成本结构环比/同比（堆积面积图）。
   - 费用率对标（雷达图或条形图）。

5. **财务结构页**
   - 资产负债结构（100% 堆积条形图）。
   - 营运资本（DSO/DIO/DPO）与现金转换周期（CCC）趋势。

---

## 6. 自动生成 PPT 的实施方式

## 6.1 推荐技术栈

- 数据处理：`Python + pandas`
- 图表：`matplotlib / seaborn / plotly`
- PPT 生成：`python-pptx`
- 调度：`Airflow / cron`

## 6.2 自动化流程

1. 从数仓读取汇总表（SQL）。
2. 生成图表 PNG（按主题文件夹保存）。
3. 套用 PPT 模板（母版中预留占位符）。
4. 将图表与关键数字写入页面。
5. 导出 `Budget_Review_YYYYMM.pptx`。

## 6.3 产出物目录建议

```text
/output
  /2026-03
    /charts
      kpi_overview.png
      budget_vs_actual.png
      variance_waterfall.png
    Budget_Review_202603.pptx
    recon_check_202603.xlsx
```

---

## 7. SQL 示例（预算实际差异）

```sql
SELECT
  a.period_key,
  a.org_id,
  a.account_code,
  SUM(CASE WHEN a.version='ACTUAL' THEN a.amount ELSE 0 END) AS actual_amt,
  SUM(CASE WHEN a.version='BUDGET' THEN a.amount ELSE 0 END) AS budget_amt,
  SUM(CASE WHEN a.version='ACTUAL' THEN a.amount ELSE 0 END)
    - SUM(CASE WHEN a.version='BUDGET' THEN a.amount ELSE 0 END) AS var_amt
FROM fact_statement_snapshot a
WHERE a.statement_code = 'PL'
GROUP BY a.period_key, a.org_id, a.account_code;
```

---

## 8. 实施路径（建议分三期）

1. **一期（4~6 周）**
   - 完成数据标准化、四大报表基础勾稽、预算 vs 实际主看板。
2. **二期（4~8 周）**
   - 收入/成本/费用专题分析、归因模型、异常预警。
3. **三期（4~6 周）**
   - 自动生成 PPT、管理驾驶舱、移动端订阅推送。

---

## 9. 交付清单（你可以直接让团队照此建设）

- 数据字典（维度、事实、指标口径）
- 勾稽规则库（SQL 表达式 + 阈值 + 告警策略）
- 明细和汇总表 DDL
- 标准图表模板库
- PPT 模板（董事会版 / 经营会版）
- 月结后自动执行任务（数据刷新 -> 校验 -> 图表 -> PPT）

> 如果你希望，我可以在下一步直接给你：
> 1）可执行的 MySQL/PG 建表 SQL；
> 2）可直接跑的 Python 脚本（读取 Excel/CSV 生成图表 + PPT）；
> 3）一套预算执行分析的 PPT 母版结构。

---

## 10. 预算表填写 -> 自动图表/PPT -> 分析建议（操作说明）

## 10.1 先准备预算填报表（CSV/Excel）

请按以下字段准备数据（最少字段）：

| 字段 | 必填 | 示例 | 说明 |
|---|---|---|---|
| period | 是 | 2026-03 | 会计期间，建议 `YYYY-MM` |
| module | 是 | 收入/成本/费用 | 分析模块（可扩展到资产/负债/现金流） |
| actual | 是 | 1250 | 实际值 |
| budget | 是 | 1350 | 预算值 |

> 建议扩展字段：`org_id`、`account_code`、`product_id`、`customer_id`、`project_id`，用于明细钻取与归因分析。

### 填写规范建议

1. 同一期间 + 同一模块可以有多行（系统会自动汇总）。
2. 金额统一币种和口径（含税/不含税必须一致）。
3. 若预算为 0，请单独标注业务背景，避免差异率失真。
4. 费用类科目建议拆分到销售/管理/研发/财务四类，方便费用率分析。

## 10.2 自动生成图表与 PPT

在仓库根目录执行：

```bash
python tools/generate_budget_ppt.py \
  --input data_sample_budget_actual.csv \
  --output-dir output/2026-03
```

执行后自动生成：

- `output/2026-03/charts/budget_vs_actual_monthly.png`（月度预算执行趋势）
- `output/2026-03/charts/budget_vs_actual_module.png`（收入/成本/费用模块对比）
- `output/2026-03/analysis_suggestions.md`（自动分析建议）
- `output/2026-03/Budget_Review.pptx`（自动报告）

## 10.3 自动分析建议的规则逻辑

脚本会按模块汇总后计算：

- `差异额 = actual - budget`
- `差异率 = 差异额 / abs(budget)`

并按阈值输出建议：

- 差异率 `>= 10%`：提示“超预算”，建议做价格/销量/结构归因与费用控制。
- 差异率 `<= -10%`：提示“低于预算”，建议检查确认节奏、交付进度、目标合理性。
- `-10% ~ 10%`：提示“总体可控”，建议继续滚动预测。

## 10.4 管理层分析建议（可直接用于月报）

1. **收入偏差分析**：拆解价格、销量、产品结构、区域结构、汇率因素。
2. **成本偏差分析**：拆解材料、人工、制造费用、采购价差、良率损失。
3. **费用偏差分析**：按费用类型和成本中心做预算执行率排名。
4. **现金流联动分析**：把利润偏差映射到应收、存货、应付和经营现金流变化。
5. **动作闭环**：每个异常模块必须绑定责任人、整改动作、完成日期和复盘结论。
