import datetime

from django.test import SimpleTestCase

from core.services import (
    average_of,
    merge_duplicate_marks,
    normalize_date,
    normalize_name,
    parse_marks,
    read_and_clean_csv,
)


class NormalizeNameTests(SimpleTestCase):
    def test_title_cases_and_trims(self):
        self.assertEqual(normalize_name("  ARJUN sharma "), "Arjun Sharma")

    def test_collapses_internal_whitespace(self):
        self.assertEqual(normalize_name("Diya   Joshi"), "Diya Joshi")

    def test_already_clean_name_unchanged(self):
        self.assertEqual(normalize_name("Mohit Soni"), "Mohit Soni")

    def test_empty_string(self):
        self.assertEqual(normalize_name(""), "")


class NormalizeDateTests(SimpleTestCase):
    def test_iso_format(self):
        self.assertEqual(normalize_date("2014-03-15"), datetime.date(2014, 3, 15))

    def test_day_first_slash_format(self):
        self.assertEqual(normalize_date("15/03/2014"), datetime.date(2014, 3, 15))

    def test_day_first_dash_format(self):
        self.assertEqual(normalize_date("27-11-2014"), datetime.date(2014, 11, 27))

    def test_dd_mon_yy_format(self):
        self.assertEqual(normalize_date("21-Dec-14"), datetime.date(2014, 12, 21))

    def test_dd_mon_yyyy_format(self):
        self.assertEqual(normalize_date("15-Mar-2014"), datetime.date(2014, 3, 15))

    def test_invalid_format_raises(self):
        with self.assertRaises(ValueError):
            normalize_date("not-a-date")


class ParseMarksTests(SimpleTestCase):
    def test_blank_string_is_absent(self):
        self.assertIsNone(parse_marks(""))

    def test_none_is_absent(self):
        self.assertIsNone(parse_marks(None))

    def test_whitespace_only_is_absent(self):
        self.assertIsNone(parse_marks("   "))

    def test_valid_integer_string(self):
        self.assertEqual(parse_marks("87"), 87)

    def test_never_coerces_absent_to_zero(self):
        self.assertNotEqual(parse_marks(""), 0)


class MergeDuplicateMarksTests(SimpleTestCase):
    def test_keeps_higher_value(self):
        self.assertEqual(merge_duplicate_marks(45, 61), 61)
        self.assertEqual(merge_duplicate_marks(61, 45), 61)

    def test_real_value_beats_absent(self):
        self.assertEqual(merge_duplicate_marks(None, 76), 76)
        self.assertEqual(merge_duplicate_marks(76, None), 76)

    def test_both_absent_stays_absent(self):
        self.assertIsNone(merge_duplicate_marks(None, None))

    def test_equal_values(self):
        self.assertEqual(merge_duplicate_marks(75, 75), 75)


class AverageOfTests(SimpleTestCase):
    def test_rounds_to_one_decimal(self):
        self.assertEqual(average_of([80, 81, 82]), 81.0)
        self.assertEqual(average_of([70, 71]), 70.5)

    def test_excludes_none_values(self):
        self.assertEqual(average_of([80, None, 90]), 85.0)

    def test_all_none_returns_none(self):
        self.assertIsNone(average_of([None, None]))

    def test_empty_list_returns_none(self):
        self.assertIsNone(average_of([]))

    def test_rounding_uses_one_decimal_not_more(self):
        self.assertEqual(average_of([70, 71, 71]), 70.7)


class ReadAndCleanCsvTests(SimpleTestCase):
    """Uses the real uploaded export so the dedup rule is exercised
    against actual duplicate rows (e.g. EIS-1035 / EIS-1019 appear twice)."""

    CSV_PATH = "data/students_marks.csv"

    def test_duplicate_rows_collapse_to_one_mark(self):
        students, marks = read_and_clean_csv(self.CSV_PATH)
        # EIS-1019 has two identical Hindi rows (76, 76) in the export.
        self.assertEqual(marks["EIS-1019"]["Hindi"], 76)

    def test_names_are_title_cased_after_import(self):
        students, _ = read_and_clean_csv(self.CSV_PATH)
        self.assertEqual(students["EIS-1035"]["name"], "Mohit Soni")

    def test_dates_are_parsed_to_date_objects(self):
        students, _ = read_and_clean_csv(self.CSV_PATH)
        self.assertIsInstance(students["EIS-1034"]["date_of_birth"], datetime.date)

    def test_absent_mark_kept_as_none(self):
        _, marks = read_and_clean_csv(self.CSV_PATH)
        # EIS-1034's Social Science row has a blank marks_obtained.
        self.assertIsNone(marks["EIS-1034"]["Social Science"])
