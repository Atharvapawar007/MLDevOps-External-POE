"""
monitoring.py - Evidently AI integration for MLOps data quality and drift monitoring.

Performs:
1. Data Drift Analysis (comparing incoming request distributions of num1, num2, result vs reference baseline)
2. Data Quality & Integrity Checks (missing values, schema consistency, ranges)
3. Automated Evidently Test Suites for CI/CD gating in Jenkins
4. Interactive HTML dashboard generation and JSON metrics export
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path so both direct and module execution work seamlessly
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import json
import random
import argparse
from datetime import datetime, timezone
from typing import Tuple, Dict, Any

try:
    from src.addition import add_numbers
except ImportError:
    from addition import add_numbers



def generate_synthetic_data(num_samples: int = 50, seed: int = 42) -> list[dict]:
    """Generate synthetic numeric data for addition service testing."""
    random.seed(seed)
    data = []
    for _ in range(num_samples):
        n1 = round(random.uniform(-50.0, 150.0), 2)
        n2 = round(random.uniform(-50.0, 150.0), 2)
        res = round(add_numbers(n1, n2), 2)
        data.append({
            "num1": n1,
            "num2": n2,
            "result": res,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    return data


def save_dataset_csv(filepath: str, data: list[dict]) -> None:
    """Save dataset list of dictionaries to CSV."""
    import csv
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["num1", "num2", "result", "timestamp"])
        writer.writeheader()
        writer.writerows(data)


def load_data_csv(filepath: str):
    """Load dataset from CSV file using pandas if available, else csv reader."""
    try:
        import pandas as pd
        df = pd.read_csv(filepath)
        return df
    except ImportError:
        import csv
        rows = []
        with open(filepath, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                rows.append({
                    "num1": float(row["num1"]),
                    "num2": float(row["num2"]),
                    "result": float(row["result"]),
                    "timestamp": row.get("timestamp", "")
                })
        return rows


def run_evidently_checks(
    reference_path: str,
    current_path: str,
    output_html: str = "reports/evidently_report.html",
    output_json: str = "reports/evidently_report.json",
    fail_on_drift: bool = True
) -> bool:
    """
    Run Evidently Data Drift & Quality evaluations and test suites.

    Args:
        reference_path: Path to reference baseline CSV.
        current_path: Path to current batch CSV.
        output_html: Path to save interactive HTML report.
        output_json: Path to save JSON metrics.
        fail_on_drift: If True, returns False when test conditions fail (gating CI/CD).

    Returns:
        bool: True if test suite passes or succeeds; False if drift/quality fails.
    """
    os.makedirs(os.path.dirname(output_html) or ".", exist_ok=True)
    os.makedirs(os.path.dirname(output_json) or ".", exist_ok=True)

    print(f"Loading reference baseline from: {reference_path}")
    print(f"Loading current batch data from: {current_path}")

    try:
        import pandas as pd
        from evidently.report import Report
        from evidently.metric_preset import DataDriftPreset, DataQualityPreset
        from evidently.test_suite import TestSuite
        from evidently.tests import (
            TestNumberOfMissingValues,
            TestColumnDrift,
            TestShareOfDriftedColumns,
            TestColumnsType
        )

        ref_df = pd.read_csv(reference_path)
        curr_df = pd.read_csv(current_path)

        # Features & targets to evaluate
        eval_cols = ["num1", "num2", "result"]
        ref_df_clean = ref_df[eval_cols]
        curr_df_clean = curr_df[eval_cols]

        print("--> Generating Evidently Comprehensive Visual Report...")
        data_report = Report(metrics=[
            DataQualityPreset(),
            DataDriftPreset()
        ])
        data_report.run(reference_data=ref_df_clean, current_data=curr_df_clean)
        data_report.save_html(output_html)
        print(f"Successfully saved visual report: {output_html}")

        print("--> Running Evidently Gating Test Suite for CI/CD Pipeline...")
        test_suite = TestSuite(tests=[
            TestNumberOfMissingValues(),
            TestColumnsType(),
            TestShareOfDriftedColumns(lt=0.5),
            TestColumnDrift(column_name="num1"),
            TestColumnDrift(column_name="num2"),
            TestColumnDrift(column_name="result")
        ])
        test_suite.run(reference_data=ref_df_clean, current_data=curr_df_clean)
        test_suite.save_json(output_json)
        print(f"Successfully saved test suite JSON: {output_json}")

        summary = test_suite.as_dict().get("summary", {})
        all_passed = summary.get("all_passed", True)
        total_tests = summary.get("total_tests", 0)
        success_tests = summary.get("success_tests", 0)
        failed_tests = summary.get("failed_tests", 0)

        print("-" * 55)
        print("          EVIDENTLY TEST SUITE SUMMARY")
        print("-" * 55)
        print(f"Total Tests Executed  : {total_tests}")
        print(f"Tests Passed          : {success_tests}")
        print(f"Tests Failed          : {failed_tests}")
        print(f"Overall Status        : {'PASSED' if all_passed else 'FAILED'}")
        print("-" * 55)

        if not all_passed and fail_on_drift:
            print("[Alert] Evidently test suite failed! Data quality/drift thresholds breached.")
            return False

        return True

    except ImportError:
        print("[Notice] 'evidently' or 'pandas' library not installed in current environment.")
        print("Running native statistical drift and quality fallback check...")
        
        # Fallback statistical check for basic validation
        import csv
        def read_rows(p):
            with open(p, "r", encoding="utf-8") as f:
                return [r for r in csv.DictReader(f)]

        ref_rows = read_rows(reference_path)
        curr_rows = read_rows(current_path)

        def col_mean(rows, col):
            vals = [float(r[col]) for r in rows if r.get(col) not in (None, "")]
            return sum(vals) / len(vals) if vals else 0.0

        ref_mean_res = col_mean(ref_rows, "result")
        curr_mean_res = col_mean(curr_rows, "result")
        missing_count = sum(1 for r in curr_rows if any(v in (None, "") for v in r.values()))

        fallback_summary = {
            "engine": "fallback_statistical_evaluator",
            "reference_records": len(ref_rows),
            "current_records": len(curr_rows),
            "reference_mean_result": ref_mean_res,
            "current_mean_result": curr_mean_res,
            "missing_values_current": missing_count,
            "drift_detected": abs(ref_mean_res - curr_mean_res) > 200.0,
            "status": "PASSED" if missing_count == 0 else "WARNING"
        }

        # Write fallback HTML and JSON
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(fallback_summary, f, indent=2)

        html_content = f"""<!DOCTYPE html>
<html>
<head><title>Evidently Fallback Monitoring Report</title></head>
<body style="font-family: Arial, sans-serif; padding: 20px;">
    <h2>Evidently MLOps Monitoring Report (Addition Service)</h2>
    <p>Install full 'evidently' package to view interactive JS widgets.</p>
    <table border="1" cellpadding="8" style="border-collapse: collapse;">
        <tr><th>Metric</th><th>Value</th></tr>
        <tr><td>Reference Records</td><td>{len(ref_rows)}</td></tr>
        <tr><td>Current Batch Records</td><td>{len(curr_rows)}</td></tr>
        <tr><td>Reference Mean Result</td><td>{ref_mean_res:.2f}</td></tr>
        <tr><td>Current Mean Result</td><td>{curr_mean_res:.2f}</td></tr>
        <tr><td>Missing Values</td><td>{missing_count}</td></tr>
        <tr><td>Quality / Gating Status</td><td><strong>{fallback_summary['status']}</strong></td></tr>
    </table>
</body>
</html>"""
        with open(output_html, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"Fallback reports saved: {output_html}, {output_json}")
        return missing_count == 0


def main():
    parser = argparse.ArgumentParser(description="Evidently Data Quality and Drift Monitoring for Addition Service")
    parser.add_argument("--reference", default="data/reference_data.csv", help="Path to reference baseline CSV")
    parser.add_argument("--current", default="data/current_data.csv", help="Path to current batch CSV")
    parser.add_argument("--output-html", default="reports/evidently_report.html", help="Path to output HTML report")
    parser.add_argument("--output-json", default="reports/evidently_report.json", help="Path to output JSON report")
    parser.add_argument("--generate-sample-data", action="store_true", help="Generate fresh reference and current data")
    parser.add_argument("--no-fail", action="store_true", help="Do not exit with non-zero code on test failure")

    args = parser.parse_args()

    if args.generate_sample_data:
        print("Generating synthetic baseline and production datasets...")
        ref_data = generate_synthetic_data(num_samples=60, seed=42)
        curr_data = generate_synthetic_data(num_samples=40, seed=123)
        save_dataset_csv(args.reference, ref_data)
        save_dataset_csv(args.current, curr_data)
        print(f"Saved: {args.reference} and {args.current}")

    success = run_evidently_checks(
        reference_path=args.reference,
        current_path=args.current,
        output_html=args.output_html,
        output_json=args.output_json,
        fail_on_drift=not args.no_fail
    )

    if not success:
        print("[CI/CD Pipeline Failure] Evidently tests failed.")
        sys.exit(1)
    else:
        print("[CI/CD Pipeline Success] Evidently tests passed successfully!")
        sys.exit(0)


if __name__ == "__main__":
    main()
