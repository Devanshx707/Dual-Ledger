"""Group splitter page: shared expenses, balances and settle-up suggestions."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from config import CATEGORIES, BG, WHITE, TEXT, MUTED, FONT
from logic import parse_people, parse_payers, compute_balances, compute_settlements, read_amount
from widgets import FlatButton, make_card, make_entry, field, make_tree


class GroupMixin:
    def build_group(self):
        page = self.pages["group"]
        self.page_title(page, "Group Splitter", "Split shared costs and see who owes whom")
        body = tk.Frame(page, bg=BG)
        body.pack(fill="both", expand=True)

        form = make_card(body)
        form.pack(side="left", fill="y", padx=(0, 16))
        form.columnconfigure(0, weight=1)
        tk.Label(form, text="Add group expense", bg=WHITE, fg=TEXT, font=(FONT, 12, "bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=(16, 0))
        self.group_name_entry = make_entry(form)
        self.group_payer_entry = make_entry(form)
        self.group_amount_entry = make_entry(form)
        self.group_category_combo = ttk.Combobox(form, values=CATEGORIES, state="readonly")
        self.group_date_entry = make_entry(form)
        self.group_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        self.group_people_entry = make_entry(form)
        fields = [("Group name", self.group_name_entry), ("Paid by (Name or Name:amount, ...)", self.group_payer_entry),
                  ("Amount", self.group_amount_entry), ("Category", self.group_category_combo),
                  ("Date (YYYY-MM-DD)", self.group_date_entry),
                  ("Split between (comma separated)", self.group_people_entry)]
        for i, (label, widget) in enumerate(fields, start=1):
            field(form, i, label, widget)
        FlatButton(form, "Add expense", self.add_group_expense).grid(
            row=14, column=0, sticky="ew", padx=16, pady=(18, 16))

        right = tk.Frame(body, bg=BG)
        right.pack(side="right", fill="both", expand=True)
        top = make_card(right)
        top.pack(fill="both", expand=True)
        head = tk.Frame(top, bg=WHITE)
        head.pack(fill="x", padx=16, pady=14)
        tk.Label(head, text="Group", bg=WHITE, fg=MUTED, font=(FONT, 10)).pack(side="left")
        self.view_group = ttk.Combobox(head, state="readonly", width=16)
        self.view_group.pack(side="left", padx=8)
        self.view_group.bind("<<ComboboxSelected>>", lambda e: self.load_group())
        FlatButton(head, "Delete group", self.delete_group_all, "ghost").pack(side="right")
        FlatButton(head, "Delete selected", self.delete_group_expense, "ghost").pack(side="right", padx=6)
        self.group_tree = make_tree(top, ("id", "payer", "amount", "category", "date", "split"),
                                    (0, 150, 65, 70, 80, 120), 6)

        bottom = tk.Frame(right, bg=BG)
        bottom.pack(fill="x", pady=(16, 0))
        bal = make_card(bottom)
        bal.pack(side="left", fill="both", expand=True, padx=(0, 8))
        tk.Label(bal, text="Balances", bg=WHITE, fg=TEXT, font=(FONT, 12, "bold")).pack(
            anchor="w", padx=16, pady=(12, 4))
        self.balance_tree = make_tree(bal, ("person", "net"), (140, 80), 5)
        settle = make_card(bottom)
        settle.pack(side="right", fill="both", expand=True, padx=(8, 0))
        tk.Label(settle, text="Settle up", bg=WHITE, fg=TEXT, font=(FONT, 12, "bold")).pack(
            anchor="w", padx=16, pady=(12, 4))
        self.settle_box = tk.Text(settle, height=8, width=24, bg=WHITE, fg=TEXT, relief="flat",
                                  font=(FONT, 10), state="disabled")
        self.settle_box.pack(fill="both", expand=True, padx=16, pady=(0, 12))

    def add_group_expense(self):
        group = self.group_name_entry.get().strip()
        payer = self.group_payer_entry.get().strip()
        category = self.group_category_combo.get()
        date = self.group_date_entry.get().strip()
        people = parse_people(self.group_people_entry.get())
        if not group or not payer or not category or not date or not people:
            messagebox.showerror("Input Error", "Please fill in all fields.")
            return
        try:
            amount = read_amount(self.group_amount_entry.get().strip())
        except ValueError:
            messagebox.showerror("Input Error", "Amount must be a positive number.")
            return
        try:
            parse_payers(payer, amount)
        except ValueError:
            messagebox.showerror("Input Error",
                                 "Paid by must be one name, or Name:amount pairs that add up to the total.")
            return
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Input Error", "Date must use YYYY-MM-DD.")
            return
        self.cursor.execute(
            "INSERT INTO group_expenses (group_name, payer, amount, category, date, participants) "
            "VALUES (?, ?, ?, ?, ?, ?)", (group, payer, amount, category, date, ",".join(people)))
        self.conn.commit()
        self.group_amount_entry.delete(0, tk.END)
        self.refresh_groups(select=group)

    def delete_group_expense(self):
        selected = self.group_tree.selection()
        if not selected:
            messagebox.showerror("Select a row", "Pick a record to delete.")
            return
        record_id = self.group_tree.item(selected[0])["values"][0]
        self.cursor.execute("DELETE FROM group_expenses WHERE id = ?", (record_id,))
        self.conn.commit()
        self.refresh_groups(select=self.view_group.get())

    def delete_group_all(self):
        group = self.view_group.get()
        if not group:
            messagebox.showinfo("Nothing to delete", "There are no groups.")
            return
        if not messagebox.askyesno("Delete Group", f"Delete every expense in '{group}'? This cannot be undone."):
            return
        self.cursor.execute("DELETE FROM group_expenses WHERE group_name = ?", (group,))
        self.cursor.execute("SELECT COUNT(*) FROM group_expenses")
        if self.cursor.fetchone()[0] == 0:
            self.cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'group_expenses'")
        self.conn.commit()
        self.refresh_groups()

    def refresh_groups(self, select=None):
        self.cursor.execute("SELECT DISTINCT group_name FROM group_expenses ORDER BY group_name")
        names = [r[0] for r in self.cursor.fetchall()]
        self.view_group["values"] = names
        if select in names:
            self.view_group.set(select)
        elif names:
            self.view_group.set(names[0])
        else:
            self.view_group.set("")
        self.load_group()

    def load_group(self):
        for tree in (self.group_tree, self.balance_tree):
            for row in tree.get_children():
                tree.delete(row)
        group = self.view_group.get()
        lines = []
        if group:
            self.cursor.execute(
                "SELECT id, payer, amount, category, date, participants FROM group_expenses "
                "WHERE group_name = ? ORDER BY date DESC, id DESC", (group,))
            rows = self.cursor.fetchall()
            expenses = []
            for rid, payer, amt, cat, date, people in rows:
                self.group_tree.insert("", tk.END, values=(rid, payer, f"{amt:.2f}", cat, date, people))
                expenses.append((payer, amt, people.split(",")))
            balances = compute_balances(expenses)
            for person, net in sorted(balances.items(), key=lambda x: -x[1]):
                self.balance_tree.insert("", tk.END, values=(person, f"{net:+.2f}"))
            for debtor, creditor, pay in compute_settlements(balances):
                lines.append(f"{debtor} pays {creditor}: {pay:.2f}")
            if not lines and rows:
                lines.append("Everyone is settled.")
        self.settle_box.config(state="normal")
        self.settle_box.delete("1.0", tk.END)
        self.settle_box.insert(tk.END, "\n".join(lines))
        self.settle_box.config(state="disabled")
