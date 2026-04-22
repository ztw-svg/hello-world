# hello-world

此仓库提供“全面预算分析系统”的落地示例，包含：

- `docs/comprehensive_budget_analysis_system.md`：系统架构、模型、勾稽关系、图表方案。
- `docs/comprehensive_template_packages.md`：全面预算多表模板包说明（PL/BS/CF/EQ + 映射表）。
- `docs/enterprise_budget_template_guide.md`：企业版预算填报模板说明 + 校验规则 + 流程。
- `docs/monthly_budget_ppt_blueprint.md`：月度管理会 PPT 结构模板。
- `templates/budget_input_template.csv`：轻量单表模板（PoC 用）。
- `templates/comprehensive/`：企业级全面预算多表模板包。
- `tools/generate_budget_ppt.py`：读取 CSV，自动生成图表、建议与 PPT。
- `data_sample_budget_actual.csv`：轻量级示例输入数据。

## 快速试跑

```bash
python tools/generate_budget_ppt.py \
  --input data_sample_budget_actual.csv \
  --output-dir output/2026-03
```

## 预期输出

- `output/2026-03/charts/budget_vs_actual_monthly.png`
- `output/2026-03/charts/budget_vs_actual_module.png`
- `output/2026-03/analysis_suggestions.md`
- `output/2026-03/Budget_Review.pptx`

## 建议落地顺序

1. 用 `templates/comprehensive/01_dim_mapping.csv` 固定口径。
2. 按 `templates/comprehensive/02~05` 收集四大报表预算/实际。
3. 每月锁数后运行脚本自动生成图表与 PPT。
4. 按 `docs/monthly_budget_ppt_blueprint.md` 补充管理层结论与行动项。
