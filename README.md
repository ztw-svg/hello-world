# hello-world

此仓库提供“全面预算分析系统”的落地示例，包含：

- `docs/comprehensive_budget_analysis_system.md`：系统架构、模型、勾稽关系、图表方案。
- `docs/comprehensive_template_packages.md`：全面预算多表模板包说明（PL/BS/CF/EQ + 映射表）。
- `docs/full_budget_execution_guide.md`：从填报到自动生成四大报表与勾稽报告的执行说明。
- `docs/enterprise_budget_template_guide.md`：企业版预算填报模板说明 + 校验规则 + 流程。
- `docs/monthly_budget_ppt_blueprint.md`：月度管理会 PPT 结构模板。
- `templates/budget_input_template.csv`：轻量单表模板（PoC 用）。
- `templates/comprehensive/`：企业级全面预算多表模板包。
- `tools/build_comprehensive_budget_statements.py`：自动生成四大报表汇总与勾稽结果。
- `tools/generate_budget_ppt.py`：读取 CSV，自动生成图表、建议与 PPT。
- `data_sample_budget_actual.csv`：轻量级示例输入数据。

## A. 全套预算表自动生成（推荐）

```bash
python tools/build_comprehensive_budget_statements.py \
  --input-dir templates/comprehensive \
  --output-dir output/comprehensive/2026-01
```

输出文件：

- `output/comprehensive/2026-01/pl_statement.csv`
- `output/comprehensive/2026-01/bs_statement.csv`
- `output/comprehensive/2026-01/cf_statement.csv`
- `output/comprehensive/2026-01/eq_statement.csv`
- `output/comprehensive/2026-01/reconciliation_report.csv`
- `output/comprehensive/2026-01/statements_summary.md`

## B. 图表 + PPT 自动生成（轻量）

```bash
python tools/generate_budget_ppt.py \
  --input data_sample_budget_actual.csv \
  --output-dir output/2026-03
```

## 建议落地顺序

1. 用 `templates/comprehensive/01_dim_mapping.csv` 固定口径。
2. 按 `templates/comprehensive/02~05` 收集四大报表预算/实际。
3. 运行 `build_comprehensive_budget_statements.py` 生成报表与勾稽结果。
4. 再运行图表/PPT脚本并按 `docs/monthly_budget_ppt_blueprint.md` 补充管理层结论。
