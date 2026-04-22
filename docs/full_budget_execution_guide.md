# 全套预算表自动生成与勾稽执行指南

你问“能不能直接填写预算后，通过勾稽关系自动生成对应表格”，答案是：**能**。

本仓库现在提供了一个可执行流程：

1. 先填 5 张输入表（映射 + 四大报表输入）
2. 运行自动生成脚本
3. 自动产出四大报表汇总 + 勾稽报告 + 摘要

## 一、要填写的输入表

- `templates/comprehensive/01_dim_mapping.csv`（组织与科目映射）
- `templates/comprehensive/02_budget_input_pl.csv`（利润表）
- `templates/comprehensive/03_budget_input_bs.csv`（资产负债表）
- `templates/comprehensive/04_budget_input_cf.csv`（现金流量表）
- `templates/comprehensive/05_budget_input_eq.csv`（所有者权益变动表）

## 二、自动生成命令

```bash
python tools/build_comprehensive_budget_statements.py \
  --input-dir templates/comprehensive \
  --output-dir output/comprehensive/2026-01
```

## 三、自动输出内容

- `pl_statement.csv`：利润表汇总
- `bs_statement.csv`：资产负债表汇总
- `cf_statement.csv`：现金流量表汇总
- `eq_statement.csv`：所有者权益变动汇总
- `reconciliation_report.csv`：勾稽结果
- `statements_summary.md`：文字摘要（可复制进月报）

## 四、已内置勾稽规则

- R001：资产负债平衡（资产 = 负债 + 权益）
- R002：现金净增勾稽（期末现金-期初现金 = 经营+投资+筹资净现金流）
- R003：未分配利润勾稽（期末 = 期初 + 净利润，简化口径）

## 五、你下一步怎么做

1. 把你们真实数据替换模板示例行。
2. 先跑单体公司，再做合并公司版本。
3. 查看 `reconciliation_report.csv` 中 `pass_flag`，优先修正 N 的规则。
4. 再接图表/PPT生成脚本做管理层汇报自动化。
