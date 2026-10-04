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
