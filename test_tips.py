"""Tests for tips.py. Run from the project folder: python -m unittest discover -s tests -v"""
import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tips import generate_tips, MAX_TIPS

TODAY = date(2026, 10, 20)


def titles(expenses, investments=()):
    return [tip[0] for tip in generate_tips(expenses, list(investments), TODAY)]


class TipTests(unittest.TestCase):
    def test_no_data_asks_the_user_to_start(self):
        self.assertEqual(titles([]), ["Start tracking"])

    def test_one_category_dominates_the_month(self):
        expenses = [("Food", 900, "2026-10-02"), ("Transport", 300, "2026-10-05"), ("Utilities", 100, "2026-10-08")]
        tips = generate_tips(expenses, [], TODAY)
        self.assertEqual(tips[0][0], "Food leads this month")
        self.assertEqual(tips[0][2], "Food")
        self.assertIn("69%", tips[0][1])

    def test_large_expense_tip_is_skipped_when_it_repeats_the_category_tip(self):
        expenses = [("Food", 900, "2026-10-02"), ("Transport", 300, "2026-10-05"), ("Utilities", 100, "2026-10-08")]
        self.assertNotIn("One large expense", titles(expenses))

    def test_large_expense_tip_in_a_different_category(self):
        expenses = [("Food", 500, "2026-10-02"), ("Food", 500, "2026-10-03"), ("Transport", 700, "2026-10-05")]
        self.assertIn("One large expense", titles(expenses))

    def test_rising_pace_against_last_month(self):
        expenses = [("Food", 1000, "2026-10-02"), ("Transport", 1000, "2026-10-09"), ("Food", 1500, "2026-09-10")]
        self.assertIn("Spending is rising", titles(expenses))

    def test_falling_pace_against_last_month(self):
        expenses = [("Food", 100, "2026-10-02"), ("Food", 5000, "2026-09-10")]
        self.assertIn("Spending is down", titles(expenses))

    def test_pace_tip_waits_until_day_five(self):
        early = date(2026, 10, 3)
        expenses = [("Food", 1000, "2026-10-02"), ("Food", 100, "2026-09-10")]
        self.assertNotIn("Spending is rising", [t[0] for t in generate_tips(expenses, [], early)])

    def test_old_entries_trigger_the_idle_tip(self):
        self.assertIn("No recent entries", titles([("Food", 100, "2026-10-05")]))

    def test_other_category_tip(self):
        expenses = [("Food", 300, "2026-10-02"), ("Other", 300, "2026-10-03"), ("Transport", 300, "2026-10-04")]
        self.assertIn("Unsorted spending", titles(expenses))

    def test_no_investments_yet(self):
        self.assertIn("No investments yet", titles([("Food", 100, "2026-10-19")]))

    def test_concentrated_portfolio(self):
        self.assertIn("Portfolio is concentrated", titles([], [("Stocks", 1000, 1000), ("Stocks", 500, 500)]))

    def test_portfolio_down_and_up(self):
        self.assertIn("Portfolio is down", titles([], [("Stocks", 1000, 900), ("Gold", 500, 500)]))
        self.assertIn("Portfolio is up", titles([], [("Stocks", 1000, 1100), ("Gold", 500, 540)]))

    def test_small_investing_share(self):
        expenses = [("Food", 5000, "2026-10-19")]
        self.assertIn("Small investing share", titles(expenses, [("Gold", 100, 100)]))

    def test_calm_month_shows_on_track(self):
        expenses = [("Food", 300, "2026-10-05"), ("Transport", 300, "2026-10-10"), ("Utilities", 300, "2026-10-19"),
                    ("Food", 400, "2026-09-05"), ("Transport", 400, "2026-09-10"), ("Utilities", 500, "2026-09-15")]
        investments = [("Gold", 500, 510), ("SIP", 500, 505)]
        self.assertEqual(titles(expenses, investments), ["On track"])

    def test_never_more_than_the_maximum_and_urgent_tips_come_first(self):
        expenses = [("Food", 1500, "2026-10-02"), ("Other", 400, "2026-10-05"), ("Transport", 200, "2026-10-08"),
                    ("Food", 300, "2026-09-10")]
        found = titles(expenses)
        self.assertEqual(len(found), MAX_TIPS)
        self.assertEqual(found[0], "Food leads this month")
        self.assertEqual(found[1], "Spending is rising")


if __name__ == "__main__":
    unittest.main()
