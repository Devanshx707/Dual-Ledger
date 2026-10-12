"""Tests for logic.py. Run from the project folder: python -m unittest discover -s tests -v"""
import os
import sys
import unittest
from datetime import date

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from logic import (parse_people, read_amount, parse_payers, safe_payers, compute_balances,
                   compute_settlements, monthly_totals, nice_ceiling, compact_number, portfolio_summary)


class ParsingTests(unittest.TestCase):
    def test_people_are_trimmed_and_blank_names_dropped(self):
        self.assertEqual(parse_people(" Asha , Ravi,, "), ["Asha", "Ravi"])

    def test_people_duplicates_ignore_case_and_keep_first_spelling(self):
        self.assertEqual(parse_people("Asha, asha, ASHA, Ravi"), ["Asha", "Ravi"])

    def test_read_amount_rounds_to_two_places(self):
        self.assertEqual(read_amount("12.346"), 12.35)
        self.assertEqual(read_amount("1.004"), 1.0)

    def test_read_amount_rejects_zero_negative_and_text(self):
        for bad in ("0", "-5", "abc", ""):
            with self.assertRaises(ValueError):
                read_amount(bad)


class PayerTests(unittest.TestCase):
    def test_single_name_pays_the_total(self):
        self.assertEqual(parse_payers("Asha", 900), [("Asha", 900)])

    def test_pairs_must_add_up_to_the_total(self):
        self.assertEqual(parse_payers("Asha:500, Ravi:400", 900), [("Asha", 500.0), ("Ravi", 400.0)])
        with self.assertRaises(ValueError):
            parse_payers("Asha:500, Ravi:300", 900)

    def test_bad_formats_raise(self):
        for bad in ("", "Asha, Ravi", "Asha:", ":500"):
            with self.assertRaises(ValueError):
                parse_payers(bad, 900)

    def test_safe_payers_splits_old_rows_equally(self):
        self.assertEqual(safe_payers("Asha, Ravi", 900), [("Asha", 450.0), ("Ravi", 450.0)])

    def test_safe_payers_handles_empty_text(self):
        self.assertEqual(safe_payers("", 100), [("Unknown", 100)])


class BalanceTests(unittest.TestCase):
    DINNER = [("Asha", 900, ["Asha", "Ravi", "Meera"])]

    def test_one_payer_equal_split(self):
        self.assertEqual(compute_balances(self.DINNER), {"Asha": 600.0, "Ravi": -300.0, "Meera": -300.0})

    def test_two_payers(self):
        balances = compute_balances([("Asha:500, Ravi:400", 900, ["Asha", "Ravi", "Meera"])])
        self.assertEqual(balances, {"Asha": 200.0, "Ravi": 100.0, "Meera": -300.0})

    def test_balances_always_add_up_to_zero(self):
        expenses = [("Asha", 100.10, ["Asha", "Ravi", "Meera"]), ("Ravi:30, Meera:20", 50, ["Asha", "Meera"])]
        self.assertAlmostEqual(sum(compute_balances(expenses).values()), 0, places=1)

    def test_names_merge_without_regard_to_case(self):
        balances = compute_balances([("asha", 300, ["Asha", "Ravi"])])
        self.assertEqual(len(balances), 2)
        self.assertEqual(sorted(balances.values()), [-150.0, 150.0])

    def test_payment_moves_balances_toward_zero(self):
        balances = compute_balances(self.DINNER, [("Ravi", "Asha", 300)])
        self.assertEqual(balances, {"Asha": 300.0, "Ravi": 0.0, "Meera": -300.0})

    def test_partial_payment(self):
        balances = compute_balances(self.DINNER, [("Meera", "Asha", 100)])
        self.assertEqual(balances["Meera"], -200.0)
        self.assertEqual(balances["Asha"], 500.0)

    def test_payment_names_match_without_regard_to_case(self):
        balances = compute_balances(self.DINNER, [("ravi", "ASHA", 300)])
        self.assertEqual(balances["Ravi"], 0.0)


class SettlementTests(unittest.TestCase):
    def test_suggestions_for_two_creditors(self):
        balances = {"Asha": 200.0, "Ravi": 100.0, "Meera": -300.0}
        self.assertEqual(compute_settlements(balances), [("Meera", "Asha", 200.0), ("Meera", "Ravi", 100.0)])

    def test_nothing_to_settle(self):
        self.assertEqual(compute_settlements({"Asha": 0.0, "Ravi": 0.0}), [])

    def test_following_the_suggestions_clears_every_balance(self):
        expenses = [("Asha", 900, ["Asha", "Ravi", "Meera", "Dev"]), ("Ravi", 400, ["Asha", "Ravi", "Dev"])]
        balances = compute_balances(expenses)
        payments = [(debtor, creditor, amount) for debtor, creditor, amount in compute_settlements(balances)]
        after = compute_balances(expenses, payments)
        for value in after.values():
            self.assertAlmostEqual(value, 0, delta=0.02)

    def test_marked_payment_removes_one_suggestion(self):
        expenses = [("Asha:500, Ravi:400", 900, ["Asha", "Ravi", "Meera"])]
        before = compute_settlements(compute_balances(expenses))
        after = compute_settlements(compute_balances(expenses, [before[0]]))
        self.assertEqual(len(before), 2)
        self.assertEqual(after, [before[1]])


class StatsTests(unittest.TestCase):
    def test_monthly_totals_covers_six_months_oldest_first(self):
        rows = [(100, "2026-10-01"), (50, "2026-10-09"), (70, "2026-08-15"), (5, "2025-01-01")]
        result = monthly_totals(rows, date(2026, 10, 9))
        self.assertEqual([r[1] for r in result], ["May", "Jun", "Jul", "Aug", "Sep", "Oct"])
        self.assertEqual([r[2] for r in result], [0.0, 0.0, 0.0, 70.0, 0.0, 150.0])

    def test_monthly_totals_crosses_the_year_boundary(self):
        result = monthly_totals([(20, "2025-12-31"), (10, "2026-01-05")], date(2026, 2, 1), 3)
        self.assertEqual([r[0] for r in result], ["2025-12", "2026-01", "2026-02"])
        self.assertEqual([r[2] for r in result], [20.0, 10.0, 0.0])

    def test_nice_ceiling(self):
        cases = {0: 1, 7: 10, 120: 200, 400: 500, 1700: 2000, 4725: 5000, 99999: 100000}
        for value, expected in cases.items():
            self.assertEqual(nice_ceiling(value), expected)

    def test_compact_number(self):
        cases = {0: "0", 300: "300", 1250: "1.25k", 1500: "1.5k", 2000: "2k", 2500000: "2.5M"}
        for value, expected in cases.items():
            self.assertEqual(compact_number(value), expected)


class PortfolioTests(unittest.TestCase):
    def test_totals_gain_and_kinds(self):
        summary = portfolio_summary([("Stocks", 1000, 1100), ("Gold", 500, 450)])
        self.assertEqual(summary["invested"], 1500)
        self.assertEqual(summary["value"], 1550)
        self.assertEqual(summary["gain"], 50)
        self.assertAlmostEqual(summary["gain_pct"], 50 / 1500 * 100)
        self.assertEqual(summary["by_kind"], {"Stocks": 1100, "Gold": 450})

    def test_empty_portfolio(self):
        summary = portfolio_summary([])
        self.assertEqual((summary["invested"], summary["value"], summary["gain_pct"]), (0, 0, 0.0))


if __name__ == "__main__":
    unittest.main()
