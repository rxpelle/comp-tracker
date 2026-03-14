import os
import pytest
from click.testing import CliRunner
from datetime import date

from comp_tracker.cli import main


@pytest.fixture
def runner(tmp_path):
    db_path = str(tmp_path / "test.db")
    r = CliRunner()
    return r, ['--db', db_path]


class TestAddCommand:
    def test_add_comp(self, runner):
        r, opts = runner
        result = r.invoke(main, opts + ['add', 'Test Book', '--author', 'Author'])
        assert result.exit_code == 0
        assert "Added comp" in result.output

    def test_add_duplicate(self, runner):
        r, opts = runner
        r.invoke(main, opts + ['add', 'Test Book', '--author', 'Author'])
        result = r.invoke(main, opts + ['add', 'Test Book', '--author', 'Author'])
        assert "already exists" in result.output

    def test_add_with_options(self, runner):
        r, opts = runner
        result = r.invoke(main, opts + [
            'add', 'Test', '--author', 'A', '--asin', 'B123', '--genre', 'Thriller',
        ])
        assert result.exit_code == 0


class TestListCommand:
    def test_list_empty(self, runner):
        r, opts = runner
        result = r.invoke(main, opts + ['list'])
        assert "No comps tracked" in result.output

    def test_list_with_data(self, runner):
        r, opts = runner
        r.invoke(main, opts + ['add', 'Book A', '--author', 'A'])
        r.invoke(main, opts + ['add', 'Book B', '--author', 'B'])
        result = r.invoke(main, opts + ['list'])
        assert "Book A" in result.output
        assert "Book B" in result.output

    def test_list_active_only(self, runner):
        r, opts = runner
        r.invoke(main, opts + ['add', 'Active', '--author', 'A'])
        r.invoke(main, opts + ['add', 'Inactive', '--author', 'B'])
        r.invoke(main, opts + ['deactivate', 'Inactive'])
        result = r.invoke(main, opts + ['list', '--active-only'])
        assert "Active" in result.output
        assert "Inactive" not in result.output


class TestRecordCommand:
    def test_record_snapshot(self, runner):
        r, opts = runner
        r.invoke(main, opts + ['add', 'Test', '--author', 'A'])
        result = r.invoke(main, opts + ['record', 'Test', '--bsr', '5000'])
        assert result.exit_code == 0
        assert "Recorded BSR" in result.output

    def test_record_not_found(self, runner):
        r, opts = runner
        result = r.invoke(main, opts + ['record', 'Nonexistent', '--bsr', '5000'])
        assert "not found" in result.output

    def test_record_with_all_options(self, runner):
        r, opts = runner
        r.invoke(main, opts + ['add', 'Test', '--author', 'A'])
        result = r.invoke(main, opts + [
            'record', 'Test', '--bsr', '5000', '--price', '12.99',
            '--rating', '4.5', '--reviews', '1000', '--ku',
        ])
        assert result.exit_code == 0


class TestImportCommand:
    def test_import_csv(self, runner, tmp_path):
        r, opts = runner
        csv_file = tmp_path / "comps.csv"
        csv_file.write_text("title,author,asin,genre\nBook A,Author A,B123,Thriller\nBook B,Author B,,\n")
        result = r.invoke(main, opts + ['import', str(csv_file)])
        assert "Imported 2" in result.output

    def test_import_yaml(self, runner, tmp_path):
        r, opts = runner
        yaml_file = tmp_path / "comps.yaml"
        yaml_file.write_text("comp_titles:\n  - title: YAML Book\n    author: YAML Author\n")
        result = r.invoke(main, opts + ['import', str(yaml_file)])
        assert "Imported 1" in result.output

    def test_import_skips_duplicates(self, runner, tmp_path):
        r, opts = runner
        r.invoke(main, opts + ['add', 'Book A', '--author', 'Author A'])
        csv_file = tmp_path / "comps.csv"
        csv_file.write_text("title,author,asin,genre\nBook A,Author A,,\nBook B,Author B,,\n")
        result = r.invoke(main, opts + ['import', str(csv_file)])
        assert "1 skipped" in result.output


class TestRecordBulkCommand:
    def test_record_bulk(self, runner, tmp_path):
        r, opts = runner
        r.invoke(main, opts + ['add', 'Test', '--author', 'A', '--asin', 'B123'])
        csv_file = tmp_path / "snapshots.csv"
        csv_file.write_text("asin_or_title,bsr,price,rating,reviews\nB123,5000,12.99,4.5,1000\n")
        result = r.invoke(main, opts + ['record-bulk', str(csv_file)])
        assert "Recorded 1" in result.output


class TestAnalyzeCommand:
    def test_analyze(self, runner):
        r, opts = runner
        r.invoke(main, opts + ['add', 'Test', '--author', 'A'])
        r.invoke(main, opts + ['record', 'Test', '--bsr', '5000'])
        result = r.invoke(main, opts + ['analyze', 'Test'])
        assert result.exit_code == 0
        assert "Test" in result.output

    def test_analyze_not_found(self, runner):
        r, opts = runner
        result = r.invoke(main, opts + ['analyze', 'Missing'])
        assert "not found" in result.output


class TestDashboardCommand:
    def test_dashboard_empty(self, runner):
        r, opts = runner
        result = r.invoke(main, opts + ['dashboard'])
        assert "No comps tracked" in result.output

    def test_dashboard_with_data(self, runner):
        r, opts = runner
        r.invoke(main, opts + ['add', 'Test', '--author', 'A'])
        r.invoke(main, opts + ['record', 'Test', '--bsr', '5000'])
        result = r.invoke(main, opts + ['dashboard'])
        assert result.exit_code == 0


class TestAlertsCommand:
    def test_alerts_no_data(self, runner):
        r, opts = runner
        result = r.invoke(main, opts + ['alerts'])
        assert "No active alerts" in result.output


class TestDeactivateCommand:
    def test_deactivate(self, runner):
        r, opts = runner
        r.invoke(main, opts + ['add', 'Test', '--author', 'A'])
        result = r.invoke(main, opts + ['deactivate', 'Test'])
        assert "Deactivated" in result.output

    def test_deactivate_not_found(self, runner):
        r, opts = runner
        result = r.invoke(main, opts + ['deactivate', 'Missing'])
        assert "not found" in result.output


class TestHistoryCommand:
    def test_history(self, runner):
        r, opts = runner
        r.invoke(main, opts + ['add', 'Test', '--author', 'A'])
        r.invoke(main, opts + ['record', 'Test', '--bsr', '5000'])
        result = r.invoke(main, opts + ['history', 'Test'])
        assert result.exit_code == 0

    def test_history_not_found(self, runner):
        r, opts = runner
        result = r.invoke(main, opts + ['history', 'Missing'])
        assert "not found" in result.output


class TestDeleteCommand:
    def test_delete(self, runner):
        r, opts = runner
        r.invoke(main, opts + ['add', 'Test', '--author', 'A'])
        result = r.invoke(main, opts + ['delete', 'Test', '--confirm'])
        assert "Deleted" in result.output

    def test_delete_not_found(self, runner):
        r, opts = runner
        result = r.invoke(main, opts + ['delete', 'Missing', '--confirm'])
        assert "not found" in result.output
