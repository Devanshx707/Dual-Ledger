"""Ledger math. No screens and no database in this file, so it is easy to test."""


def parse_people(text):
    seen, people = set(), []
    for name in text.split(","):
        name = name.strip()
        if name and name.lower() not in seen:
            seen.add(name.lower())
            people.append(name)
    return people


def parse_payers(text, total):
    """'Asha' means Asha pays the full total.
    'Asha:500, Ravi:400' means each person pays the stated amount.
    Raises ValueError when the amounts do not add up to the total."""
    parts = [p.strip() for p in text.split(",") if p.strip()]
    if not parts:
        raise ValueError
    if len(parts) == 1 and ":" not in parts[0]:
        return [(parts[0], total)]
    payers, paid_sum = [], 0.0
    for part in parts:
        name, _, amount = part.partition(":")
        name = name.strip()
        if not name or not amount.strip():
            raise ValueError
        paid = read_amount(amount.strip())
        payers.append((name, paid))
        paid_sum += paid
    if abs(paid_sum - total) > 0.01:
        raise ValueError
    return payers


def safe_payers(text, total):
    """Never crash on stored rows. Falls back to an equal split between the listed names."""
    try:
        return parse_payers(text, total)
    except ValueError:
        names = [p.split(":")[0].strip() for p in text.split(",") if p.split(":")[0].strip()]
        if not names:
            names = ["Unknown"]
        return [(name, total / len(names)) for name in names]


def compute_balances(expenses):
    """expenses: (payer text, total, participants). Positive net means the group owes that person."""
    balances = {}
    for payer_text, amount, people in expenses:
        for name, paid in safe_payers(payer_text, amount):
            balances[name] = balances.get(name, 0.0) + paid
        share = amount / len(people)
        for person in people:
            balances[person] = balances.get(person, 0.0) - share
    return {p: round(v, 2) for p, v in balances.items()}


def compute_settlements(balances):
    creditors = sorted([[p, v] for p, v in balances.items() if v > 0.005], key=lambda x: -x[1])
    debtors = sorted([[p, -v] for p, v in balances.items() if v < -0.005], key=lambda x: -x[1])
    result, i, j = [], 0, 0
    while i < len(debtors) and j < len(creditors):
        pay = round(min(debtors[i][1], creditors[j][1]), 2)
        result.append((debtors[i][0], creditors[j][0], pay))
        debtors[i][1] -= pay
        creditors[j][1] -= pay
        if debtors[i][1] < 0.005:
            i += 1
        if creditors[j][1] < 0.005:
            j += 1
    return result


def read_amount(text):
    value = float(text)
    if value <= 0:
        raise ValueError
    return round(value, 2)


def portfolio_summary(rows):
    """rows: (kind, invested, current value). Returns totals, gain percent and value per kind."""
    invested = sum(r[1] for r in rows)
    value = sum(r[2] for r in rows)
    by_kind = {}
    for kind, _, current in rows:
        by_kind[kind] = by_kind.get(kind, 0.0) + current
    gain_pct = (value - invested) / invested * 100 if invested else 0.0
    return {"invested": round(invested, 2), "value": round(value, 2),
            "gain": round(value - invested, 2), "gain_pct": gain_pct, "by_kind": by_kind}


MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def monthly_totals(rows, today, months=6):
    """rows: (amount, 'YYYY-MM-DD'). Returns [(key, label, total)] for the last months, oldest first."""
    slots, year, month = [], today.year, today.month
    for _ in range(months):
        slots.append((year, month))
        month -= 1
        if month == 0:
            month, year = 12, year - 1
    slots.reverse()
    totals = {f"{y}-{m:02d}": 0.0 for y, m in slots}
    for amount, date_text in rows:
        key = date_text[:7]
        if key in totals:
            totals[key] += amount
    return [(f"{y}-{m:02d}", MONTH_NAMES[m - 1], round(totals[f"{y}-{m:02d}"], 2)) for y, m in slots]


def nice_ceiling(value):
    """Round a value up to a clean axis maximum such as 200, 250, 500 or 1000."""
    if value <= 0:
        return 1
    magnitude = 10 ** (len(str(int(value))) - 1) if value >= 1 else 1
    for step in (1, 2, 2.5, 5, 10):
        if value <= step * magnitude:
            return step * magnitude
    return 10 * magnitude


def compact_number(value):
    """Short labels such as 300, 1.5k, 1.25k or 2M."""
    for size, suffix in ((1_000_000, "M"), (1_000, "k")):
        if value >= size:
            return f"{value / size:.2f}".rstrip("0").rstrip(".") + suffix
    return f"{value:.0f}"
