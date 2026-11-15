"""
test_monitoring.py - Pytest unit and integration tests for Evidently monitoring module.
"""

import os
import json
import math
import tempfile
import unittest
from pathlib import Path

try:
    import pytest
except ImportError:
    class _PytestApprox:
        def __init__(self, expected, rel=1e-5, abs=1e-5):
            self.expected = expected
            self.rel = rel
            self.abs = abs
        def __eq__(self, actual):
            return math.isclose(actual, self.expected, rel_tol=self.rel, abs_tol=self.abs)

    class _PytestShim:
        @staticmethod
        def approx(expected, rel=1e-5, abs=1e-5):
            return _PytestApprox(expected, rel=rel, abs=abs)
    pytest = _PytestShim()

from src.monitoring import (
    generate_synthetic_data,
    save_dataset_csv,
    load_data_csv,
    run_evidently_checks
)


class TestMonitoringModule(unittest.TestCase):
    """Test suite for data generation, loading, and Evidently drift/quality checks."""

    def test_generate_synthetic_data(self):
        """Test generating synthetic datasets with correct calculation and structure."""
        data = generate_synthetic_data(num_samples=10, seed=99)
        assert len(data) == 10
        for row in data:
            assert "num1" in row
            assert "num2" in row
            assert "result" in row
            assert "timestamp" in row
            assert round(row["num1"] + row["num2"], 2) == pytest.approx(row["result"], abs=0.01)

    def test_save_and_load_dataset(self):
        """Test writing and reading CSV data for monitoring."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_csv = Path(tmpdir) / "test_data.csv"
            sample_data = generate_synthetic_data(num_samples=5, seed=1)
            save_dataset_csv(str(test_csv), sample_data)
            assert os.path.exists(test_csv)

            loaded = load_data_csv(str(test_csv))
            assert len(loaded) == 5

    def test_run_evidently_checks(self):
        """Test running Evidently checks generates valid HTML and JSON reports."""
        with tempfile.TemporaryDirectory() as tmpdir:
            ref_file = Path(tmpdir) / "ref.csv"
            curr_file = Path(tmpdir) / "curr.csv"
            out_html = Path(tmpdir) / "report.html"
            out_json = Path(tmpdir) / "report.json"

            # Generate test baseline and current batches
            ref_data = generate_synthetic_data(num_samples=25, seed=42)
            curr_data = generate_synthetic_data(num_samples=20, seed=43)
            save_dataset_csv(str(ref_file), ref_data)
            save_dataset_csv(str(curr_file), curr_data)

            # Execute Evidently checks
            success = run_evidently_checks(
                reference_path=str(ref_file),
                current_path=str(curr_file),
                output_html=str(out_html),
                output_json=str(out_json),
                fail_on_drift=False
            )

            assert success is True
            assert os.path.exists(out_html)
            assert os.path.exists(out_json)

            # Check content of JSON report
            with open(out_json, "r", encoding="utf-8") as f:
                report_data = json.load(f)
                assert isinstance(report_data, dict)
