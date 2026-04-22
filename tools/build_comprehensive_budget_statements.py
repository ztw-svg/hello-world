"""Build full budget statements and reconciliation outputs from comprehensive templates.

Usage:
  python tools/build_comprehensive_budget_statements.py \
    --input-dir templates/comprehensive \
    --output-dir output/comprehensive/2026-01
"""

from __future__ import annotations

import argparse
import csv
from collections import defaultdict
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path


@dataclass
class ReconResult:
    rule_id: str
    period: str
    scenario: str
    version: str
    lhs: Decimal
    rhs: Decimal
    diff: Decimal
    tolerance: Decimal
    pass_flag: str
    detail: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", required=True, help="Directory containing comprehensive template CSV files")
    parser.add_argument("--output-dir", required=True, help="Directory to write generated statement files")
    return parser.parse_args()


def to_decimal(value: str) -> Decimal:
    if value is None or value == "":
        return Decimal("0")
    try:
        return Decimal(str(value).replace(",", "").strip())
    except InvalidOperation as error:
        raise ValueError(f"Invalid numeric value: {value}") from error


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(path: Path, rows: list[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def aggregate_pl(pl_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict[tuple[str, str, str], dict[str, Decimal]]]:
    grouped: dict[tuple[str, str, str], dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))

    for row in pl_rows:
        key = (row["period"], row["scenario"], row["version"])
        module = row["module"]
        amount = to_decimal(row["budget_amount"] if row["version"] != "ACTUAL" else row["actual_amount"])
        grouped[key][module] += amount

    output_rows: list[dict[str, str]] = []
    for (period, scenario, version), module_map in sorted(grouped.items()):
        revenue = module_map.get("收入", Decimal("0"))
        cost = module_map.get("成本", Decimal("0"))
        expense = module_map.get("费用", Decimal("0"))
        gross_profit = revenue - cost
        net_profit = gross_profit - expense
        output_rows.append(
            {
                "period": period,
                "scenario": scenario,
                "version": version,
                "revenue": str(revenue),
                "cost": str(cost),
                "expense": str(expense),
                "gross_profit": str(gross_profit),
                "net_profit": str(net_profit),
            }
        )

    return output_rows, grouped


def aggregate_bs(bs_rows: list[dict[str, str]], dim_map_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict[tuple[str, str, str], dict[str, Decimal]]]:
    account_to_module = {row["account_code"]: row["module"] for row in dim_map_rows}
    grouped: dict[tuple[str, str, str], dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))

    for row in bs_rows:
        key = (row["period"], row["scenario"], row["version"])
        module = account_to_module.get(row["account_code"], row.get("module", "未分类"))
        begin_amount = to_decimal(row["budget_begin"] if row["version"] != "ACTUAL" else row["actual_begin"])
        end_amount = to_decimal(row["budget_end"] if row["version"] != "ACTUAL" else row["actual_end"])

        grouped[key][f"{module}_begin"] += begin_amount
        grouped[key][f"{module}_end"] += end_amount

    output_rows: list[dict[str, str]] = []
    for (period, scenario, version), values in sorted(grouped.items()):
        asset_begin = values.get("资产_begin", Decimal("0"))
        asset_end = values.get("资产_end", Decimal("0"))
        liab_begin = values.get("负债_begin", Decimal("0"))
        liab_end = values.get("负债_end", Decimal("0"))
        equity_begin = values.get("权益_begin", Decimal("0"))
        equity_end = values.get("权益_end", Decimal("0"))

        output_rows.append(
            {
                "period": period,
                "scenario": scenario,
                "version": version,
                "asset_begin": str(asset_begin),
                "asset_end": str(asset_end),
                "liability_begin": str(liab_begin),
                "liability_end": str(liab_end),
                "equity_begin": str(equity_begin),
                "equity_end": str(equity_end),
                "balance_diff_begin": str(asset_begin - liab_begin - equity_begin),
                "balance_diff_end": str(asset_end - liab_end - equity_end),
            }
        )

    return output_rows, grouped


def aggregate_cf(cf_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict[tuple[str, str, str], dict[str, Decimal]]]:
    grouped: dict[tuple[str, str, str], dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))

    for row in cf_rows:
        key = (row["period"], row["scenario"], row["version"])
        cf_type = row["cashflow_type"]
        amount = to_decimal(row["budget_amount"] if row["version"] != "ACTUAL" else row["actual_amount"])
        grouped[key][cf_type] += amount

    output_rows: list[dict[str, str]] = []
    for (period, scenario, version), values in sorted(grouped.items()):
        cfo = values.get("经营活动", Decimal("0"))
        cfi = values.get("投资活动", Decimal("0"))
        cff = values.get("筹资活动", Decimal("0"))
        net_increase = cfo + cfi + cff
        output_rows.append(
            {
                "period": period,
                "scenario": scenario,
                "version": version,
                "cfo": str(cfo),
                "cfi": str(cfi),
                "cff": str(cff),
                "cash_net_increase": str(net_increase),
            }
        )

    return output_rows, grouped


def aggregate_eq(eq_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], dict[tuple[str, str, str], dict[str, Decimal]]]:
    grouped: dict[tuple[str, str, str], dict[str, Decimal]] = defaultdict(lambda: defaultdict(Decimal))

    for row in eq_rows:
        key = (row["period"], row["scenario"], row["version"])
        item = row["equity_item"]
        begin = to_decimal(row["budget_begin"] if row["version"] != "ACTUAL" else row["actual_begin"])
        change = to_decimal(row["budget_change"] if row["version"] != "ACTUAL" else row["actual_change"])
        end = to_decimal(row["budget_end"] if row["version"] != "ACTUAL" else row["actual_end"])
        grouped[key][f"{item}_begin"] += begin
        grouped[key][f"{item}_change"] += change
        grouped[key][f"{item}_end"] += end

    output_rows: list[dict[str, str]] = []
    for (period, scenario, version), values in sorted(grouped.items()):
        capital_begin = values.get("实收资本_begin", Decimal("0"))
        capital_change = values.get("实收资本_change", Decimal("0"))
        capital_end = values.get("实收资本_end", Decimal("0"))
        re_begin = values.get("未分配利润_begin", Decimal("0"))
        re_change = values.get("未分配利润_change", Decimal("0"))
        re_end = values.get("未分配利润_end", Decimal("0"))
        output_rows.append(
            {
                "period": period,
                "scenario": scenario,
                "version": version,
                "capital_begin": str(capital_begin),
                "capital_change": str(capital_change),
                "capital_end": str(capital_end),
                "retained_earnings_begin": str(re_begin),
                "retained_earnings_change": str(re_change),
                "retained_earnings_end": str(re_end),
            }
        )

    return output_rows, grouped


def extract_cash_begin_end(bs_rows: list[dict[str, str]], dim_map_rows: list[dict[str, str]]) -> dict[tuple[str, str, str], tuple[Decimal, Decimal]]:
    cash_accounts = {
        row["account_code"]
        for row in dim_map_rows
        if row.get("cashflow_tag", "") == "期末现金及现金等价物"
    }

    result: dict[tuple[str, str, str], tuple[Decimal, Decimal]] = {}
    for row in bs_rows:
        if row["account_code"] not in cash_accounts:
            continue
        key = (row["period"], row["scenario"], row["version"])
        begin = to_decimal(row["budget_begin"] if row["version"] != "ACTUAL" else row["actual_begin"])
        end = to_decimal(row["budget_end"] if row["version"] != "ACTUAL" else row["actual_end"])
        result[key] = (begin, end)
    return result


def build_reconciliation(
    bs_grouped: dict[tuple[str, str, str], dict[str, Decimal]],
    cf_grouped: dict[tuple[str, str, str], dict[str, Decimal]],
    eq_grouped: dict[tuple[str, str, str], dict[str, Decimal]],
    pl_grouped: dict[tuple[str, str, str], dict[str, Decimal]],
    cash_begin_end: dict[tuple[str, str, str], tuple[Decimal, Decimal]],
    tolerance: Decimal = Decimal("0.01"),
) -> list[ReconResult]:
    keys = set(bs_grouped) | set(cf_grouped) | set(eq_grouped) | set(pl_grouped)
    recon_results: list[ReconResult] = []

    for period, scenario, version in sorted(keys):
        bs = bs_grouped.get((period, scenario, version), {})
        cf = cf_grouped.get((period, scenario, version), {})
        eq = eq_grouped.get((period, scenario, version), {})
        pl = pl_grouped.get((period, scenario, version), {})

        # R001: 资产负债平衡（期末）
        lhs = bs.get("资产_end", Decimal("0"))
        rhs = bs.get("负债_end", Decimal("0")) + bs.get("权益_end", Decimal("0"))
        diff = lhs - rhs
        recon_results.append(
            ReconResult(
                "R001",
                period,
                scenario,
                version,
                lhs,
                rhs,
                diff,
                tolerance,
                "Y" if abs(diff) <= tolerance else "N",
                "资产_end = 负债_end + 权益_end",
            )
        )

        # R002: 现金净增勾稽
        begin, end = cash_begin_end.get((period, scenario, version), (Decimal("0"), Decimal("0")))
        lhs = end - begin
        rhs = cf.get("经营活动", Decimal("0")) + cf.get("投资活动", Decimal("0")) + cf.get("筹资活动", Decimal("0"))
        diff = lhs - rhs
        recon_results.append(
            ReconResult(
                "R002",
                period,
                scenario,
                version,
                lhs,
                rhs,
                diff,
                tolerance,
                "Y" if abs(diff) <= tolerance else "N",
                "现金净增 = 经营+投资+筹资净现金流",
            )
        )

        # R003: 未分配利润勾稽
        lhs = eq.get("未分配利润_end", Decimal("0"))
        rhs = eq.get("未分配利润_begin", Decimal("0")) + pl.get("收入", Decimal("0")) - pl.get("成本", Decimal("0")) - pl.get("费用", Decimal("0"))
        diff = lhs - rhs
        recon_results.append(
            ReconResult(
                "R003",
                period,
                scenario,
                version,
                lhs,
                rhs,
                diff,
                tolerance,
                "Y" if abs(diff) <= tolerance else "N",
                "未分配利润_end = begin + 净利润(简化)",
            )
        )

    return recon_results


def write_markdown_summary(path: Path, pl_rows: list[dict[str, str]], recon_rows: list[ReconResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = ["# 全面预算自动生成结果摘要", "", "## 利润表关键指标"]
    for row in pl_rows:
        lines.append(
            f"- {row['period']} | {row['scenario']} | {row['version']}：收入 {row['revenue']}，成本 {row['cost']}，费用 {row['expense']}，净利润 {row['net_profit']}"
        )

    lines.append("")
    lines.append("## 勾稽校验结果")
    for item in recon_rows:
        icon = "✅" if item.pass_flag == "Y" else "❌"
        lines.append(
            f"- {icon} {item.rule_id} {item.period}/{item.version}: lhs={item.lhs}, rhs={item.rhs}, diff={item.diff} ({item.detail})"
        )

    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    args = parse_args()
    input_dir = Path(args.input_dir)
    output_dir = Path(args.output_dir)

    dim_map_rows = read_csv(input_dir / "01_dim_mapping.csv")
    pl_rows_raw = read_csv(input_dir / "02_budget_input_pl.csv")
    bs_rows_raw = read_csv(input_dir / "03_budget_input_bs.csv")
    cf_rows_raw = read_csv(input_dir / "04_budget_input_cf.csv")
    eq_rows_raw = read_csv(input_dir / "05_budget_input_eq.csv")

    pl_rows, pl_grouped = aggregate_pl(pl_rows_raw)
    bs_rows, bs_grouped = aggregate_bs(bs_rows_raw, dim_map_rows)
    cf_rows, cf_grouped = aggregate_cf(cf_rows_raw)
    eq_rows, eq_grouped = aggregate_eq(eq_rows_raw)
    cash_begin_end = extract_cash_begin_end(bs_rows_raw, dim_map_rows)

    recon_results = build_reconciliation(bs_grouped, cf_grouped, eq_grouped, pl_grouped, cash_begin_end)

    write_csv(
        output_dir / "pl_statement.csv",
        pl_rows,
        ["period", "scenario", "version", "revenue", "cost", "expense", "gross_profit", "net_profit"],
    )
    write_csv(
        output_dir / "bs_statement.csv",
        bs_rows,
        [
            "period",
            "scenario",
            "version",
            "asset_begin",
            "asset_end",
            "liability_begin",
            "liability_end",
            "equity_begin",
            "equity_end",
            "balance_diff_begin",
            "balance_diff_end",
        ],
    )
    write_csv(
        output_dir / "cf_statement.csv",
        cf_rows,
        ["period", "scenario", "version", "cfo", "cfi", "cff", "cash_net_increase"],
    )
    write_csv(
        output_dir / "eq_statement.csv",
        eq_rows,
        [
            "period",
            "scenario",
            "version",
            "capital_begin",
            "capital_change",
            "capital_end",
            "retained_earnings_begin",
            "retained_earnings_change",
            "retained_earnings_end",
        ],
    )

    recon_csv_rows = [
        {
            "rule_id": row.rule_id,
            "period": row.period,
            "scenario": row.scenario,
            "version": row.version,
            "lhs": str(row.lhs),
            "rhs": str(row.rhs),
            "diff": str(row.diff),
            "tolerance": str(row.tolerance),
            "pass_flag": row.pass_flag,
            "detail": row.detail,
        }
        for row in recon_results
    ]
    write_csv(
        output_dir / "reconciliation_report.csv",
        recon_csv_rows,
        ["rule_id", "period", "scenario", "version", "lhs", "rhs", "diff", "tolerance", "pass_flag", "detail"],
    )

    write_markdown_summary(output_dir / "statements_summary.md", pl_rows, recon_results)

    print(f"Generated: {output_dir / 'pl_statement.csv'}")
    print(f"Generated: {output_dir / 'bs_statement.csv'}")
    print(f"Generated: {output_dir / 'cf_statement.csv'}")
    print(f"Generated: {output_dir / 'eq_statement.csv'}")
    print(f"Generated: {output_dir / 'reconciliation_report.csv'}")
    print(f"Generated: {output_dir / 'statements_summary.md'}")


if __name__ == "__main__":
    main()
