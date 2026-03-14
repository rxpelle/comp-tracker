import os
import pytest
from datetime import date

from comp_tracker.parsers import parse_comp_csv, parse_comp_yaml, parse_bsr_snapshot_csv


class TestParseCompCSV:
    def test_basic(self):
        csv_text = """title,author,asin,genre
The Silent Patient,Alex Michaelides,B07HKGJN9C,Thriller
Gone Girl,Gillian Flynn,B006LSZECO,Thriller"""
        comps = parse_comp_csv(csv_text)
        assert len(comps) == 2
        assert comps[0].title == "The Silent Patient"
        assert comps[0].author == "Alex Michaelides"
        assert comps[0].asin == "B07HKGJN9C"
        assert comps[0].genre == "Thriller"

    def test_missing_optional_fields(self):
        csv_text = """title,author,asin,genre
Test Book,Test Author,,"""
        comps = parse_comp_csv(csv_text)
        assert len(comps) == 1
        assert comps[0].asin is None
        assert comps[0].genre is None

    def test_whitespace_handling(self):
        csv_text = """title,author,asin,genre
  Spaced Title  ,  Spaced Author  , B123 , Thriller """
        comps = parse_comp_csv(csv_text)
        assert comps[0].title == "Spaced Title"
        assert comps[0].author == "Spaced Author"


class TestParseCompYAML:
    def test_basic(self, tmp_path):
        yaml_file = tmp_path / "comps.yaml"
        yaml_file.write_text("""comp_titles:
  - title: The Silent Patient
    author: Alex Michaelides
    asin: B07HKGJN9C
    genre: Thriller
  - title: Gone Girl
    author: Gillian Flynn
""")
        comps = parse_comp_yaml(str(yaml_file))
        assert len(comps) == 2
        assert comps[0].title == "The Silent Patient"
        assert comps[1].asin is None

    def test_empty_list(self, tmp_path):
        yaml_file = tmp_path / "empty.yaml"
        yaml_file.write_text("comp_titles: []")
        comps = parse_comp_yaml(str(yaml_file))
        assert comps == []


class TestParseBSRSnapshotCSV:
    def test_basic(self):
        csv_text = """asin_or_title,bsr,price,rating,reviews
B07HKGJN9C,523,12.99,4.5,95000
Gone Girl,2150,11.99,4.1,120000"""
        results = parse_bsr_snapshot_csv(csv_text)
        assert len(results) == 2
        assert results[0][0] == "B07HKGJN9C"
        assert results[0][1].bsr == 523
        assert results[0][1].price == 12.99
        assert results[1][0] == "Gone Girl"
        assert results[1][1].reviews == 120000

    def test_missing_optional(self):
        csv_text = """asin_or_title,bsr,price,rating,reviews
B123,1000,,,"""
        results = parse_bsr_snapshot_csv(csv_text)
        assert results[0][1].price is None
        assert results[0][1].rating is None
        assert results[0][1].reviews is None

    def test_snapshot_date_is_today(self):
        csv_text = """asin_or_title,bsr,price,rating,reviews
Test,500,,,"""
        results = parse_bsr_snapshot_csv(csv_text)
        assert results[0][1].snapshot_date == date.today()
