"""Rule-based tips. Reads expense and investment rows and returns a short list of tips.
Plain Python with no screens or database, so it is easy to test."""
import calendar
from datetime import date, datetime, timedelta

from logic import portfolio_summary

MAX_TIPS = 3


def generate_tips(expenses, investments, today=None):
    """expenses: (category, amount, 'YYYY-MM-DD'). investments: (kind, invested, value).
    Returns up to MAX_TIPS tuples of (title, text, category or None)."""
    today = today or date.today()
    this_key = today.strftime("%Y-%m")
    last_key = (today.replace(day=1) - timedelta(days=1)).strftime("%Y-%m")

    month_rows = [row for row in expenses if row[2].startswith(this_key)]
    month_total = sum(row[1] for row in month_rows)
    last_total = sum(row[1] for row in expenses if row[2].startswith(last_key))
    all_spent = sum(row[1] for row in expenses)
    tips = []  # (priority, title, text, category). A lower priority number shows first.

    if not expenses and not investments:
        return [("Start tracking", "Add a few expenses and your tips appear here.", None)]

    if expenses:
        latest = max(datetime.strptime(row[2], "%Y-%m-%d").date() for row in expenses)
        idle_days = (today - latest).days
        if idle_days >= 7:
            tips.append((2, "No recent entries",
                         f"Your last expense is {idle_days} days old. Log recent spending so totals stay accurate.",
                         None))

    if len(month_rows) >= 3 and month_total > 0:
        by_cat = {}
        for cat, amount, _ in month_rows:
            by_cat[cat] = by_cat.get(cat, 0.0) + amount
        top_cat, top_amount = max(by_cat.items(), key=lambda item: item[1])
        share = top_amount / month_total
        if share >= 0.40:
            tips.append((1, f"{top_cat} leads this month",
                         f"{top_cat} is {share * 100:.0f}% of this month's spending ({top_amount:,.2f}). Review it first.",
                         top_cat))
        other_share = by_cat.get("Other", 0.0) / month_total
        if other_share >= 0.25 and top_cat != "Other":
            tips.append((3, "Unsorted spending",
                         f"Other holds {other_share * 100:.0f}% of this month. Specific categories make tips more useful.",
                         "Other"))
        biggest = max(month_rows, key=lambda row: row[1])
        repeats_top = share >= 0.40 and biggest[0] == top_cat
        if biggest[1] / month_total >= 0.35 and not repeats_top:
            tips.append((2, "One large expense",
                         f"{biggest[0]} on {biggest[2]} ({biggest[1]:,.2f}) is {biggest[1] / month_total * 100:.0f}% of this month.",
                         biggest[0]))

    if last_total > 0 and month_total > 0 and today.day >= 5:
        days = calendar.monthrange(today.year, today.month)[1]
        projected = month_total / today.day * days
        change = projected / last_total - 1
        if change >= 0.15:
            tips.append((1, "Spending is rising",
                         f"At this pace you spend {projected:,.0f} this month. Last month was {last_total:,.0f}, "
                         f"so this is {change * 100:.0f}% higher.", None))
        elif change <= -0.15:
            tips.append((3, "Spending is down",
                         f"At this pace you spend {projected:,.0f} this month, {abs(change) * 100:.0f}% below "
                         f"last month ({last_total:,.0f}).", None))

    summary = portfolio_summary(investments)
    if not investments:
        if all_spent > 0:
            tips.append((2, "No investments yet",
                         "Add investments in Personal Budget to compare them with your spending.", None))
    else:
        if all_spent > 0 and summary["invested"] < 0.10 * all_spent:
            tips.append((2, "Small investing share",
                         f"Your invested amount is {summary['invested'] / all_spent * 100:.0f}% of what you spent. "
                         "A fixed monthly amount builds the habit.", None))
        if len(investments) >= 2 and summary["value"] > 0:
            kind, value = max(summary["by_kind"].items(), key=lambda item: item[1])
            if value / summary["value"] >= 0.70:
                tips.append((2, "Portfolio is concentrated",
                             f"{kind} holds {value / summary['value'] * 100:.0f}% of your portfolio. "
                             "Spreading across types softens one bad result.", None))
        pct = summary["gain_pct"]
        if pct <= -5:
            tips.append((2, "Portfolio is down",
                         f"Value is {abs(pct):.1f}% below the amount invested. Short-term moves are normal, "
                         "so review your plan before you act.", None))
        elif pct >= 5:
            tips.append((3, "Portfolio is up", f"Value is {pct:.1f}% above the amount invested.", None))

    if not tips:
        tips.append((4, "On track", "No warnings this month. Keep logging entries.", None))
    tips.sort(key=lambda tip: tip[0])
    return [(title, text, cat) for _, title, text, cat in tips][:MAX_TIPS]
