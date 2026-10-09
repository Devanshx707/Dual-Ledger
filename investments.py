"""Investments view inside the Personal Budget page."""
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from datetime import datetime

from config import INVESTMENT_TYPES, BG, BLUE, WHITE, TEXT, MUTED, FONT
from logic import read_amount, portfolio_summary
from widgets import FlatButton, make_card, make_entry, field, make_tree


class InvestmentsMixin:
    def build_investments(self, page):
        body = tk.Frame(page, bg=BG)
        self.inv_body = body

        form = make_card(body)
        form.pack(side="left", fill="y", padx=(0, 16))
        form.columnconfigure(0, weight=1)
        tk.Label(form, text="Add investment", bg=WHITE, fg=TEXT, font=(FONT, 12, "bold")).grid(
            row=0, column=0, sticky="w", padx=16, pady=(16, 0))
        self.inv_name_entry = make_entry(form)
        self.inv_type_combo = ttk.Combobox(form, values=INVESTMENT_TYPES, state="readonly")
        self.inv_amount_entry = make_entry(form)
        self.inv_value_entry = make_entry(form)
        self.inv_date_entry = make_entry(form)
        self.inv_date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        field(form, 1, "Name", self.inv_name_entry)
        field(form, 2, "Type", self.inv_type_combo)
        field(form, 3, "Amount invested", self.inv_amount_entry)
        field(form, 4, "Current value (optional)", self.inv_value_entry)
        field(form, 5, "Date (YYYY-MM-DD)", self.inv_date_entry)
        FlatButton(form, "Add investment", self.add_investment).grid(
            row=12, column=0, sticky="ew", padx=16, pady=(18, 16))

        right = make_card(body)
        right.pack(side="right", fill="both", expand=True)
        tk.Label(right, text="Portfolio", bg=WHITE, fg=TEXT, font=(FONT, 12, "bold")).pack(
            anchor="w", padx=16, pady=(14, 6))
        stats = tk.Frame(right, bg=WHITE)
        stats.pack(fill="x", padx=16, pady=(0, 8))
        self.inv_stats = {}
        for key, caption in (("invested", "Invested"), ("value", "Current value"), ("gain", "Gain")):
            cell = tk.Frame(stats, bg=WHITE)
            cell.pack(side="left", fill="x", expand=True)
            tk.Label(cell, text=caption, bg=WHITE, fg=MUTED, font=(FONT, 9)).pack(anchor="w")
            label = tk.Label(cell, text="0.00", bg=WHITE, fg=TEXT, font=(FONT, 14, "bold"))
            label.pack(anchor="w")
            self.inv_stats[key] = label

        self.inv_tree = make_tree(right, ("id", "name", "type", "invested", "value", "gain", "date"),
                                  (0, 100, 95, 72, 72, 52, 92), 11)
        self.inv_tree.bind("<Double-1>", lambda e: self.update_investment_value())
        foot = tk.Frame(right, bg=WHITE)
        foot.pack(fill="x", padx=16, pady=(0, 14))
        FlatButton(foot, "Update value", self.update_investment_value).pack(side="left")
        FlatButton(foot, "Delete", self.delete_investment, "ghost").pack(side="left", padx=6)

    def add_investment(self):
        name = self.inv_name_entry.get().strip()
        kind = self.inv_type_combo.get()
        date = self.inv_date_entry.get().strip()
        if not name or not kind or not self.inv_amount_entry.get().strip() or not date:
            messagebox.showerror("Input Error", "Fill in name, type, amount and date.")
            return
        try:
            amount = read_amount(self.inv_amount_entry.get().strip())
            value_text = self.inv_value_entry.get().strip()
            value = read_amount(value_text) if value_text else amount
        except ValueError:
            messagebox.showerror("Input Error", "Amounts must be positive numbers.")
            return
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Input Error", "Date must use YYYY-MM-DD.")
            return
        self.cursor.execute(
            "INSERT INTO investments (name, kind, amount, value, date) VALUES (?, ?, ?, ?, ?)",
            (name, kind, amount, value, date))
        self.conn.commit()
        for entry in (self.inv_name_entry, self.inv_amount_entry, self.inv_value_entry):
            entry.delete(0, tk.END)
        self.load_investments()

    def selected_investment(self):
        selected = self.inv_tree.selection()
        if not selected:
            messagebox.showerror("Select a row", "Pick an investment first.")
            return None
        return self.inv_tree.item(selected[0])["values"][0]

    def update_investment_value(self):
        rid = self.selected_investment()
        if rid is None:
            return
        value = simpledialog.askfloat("Update value", "Current value:", parent=self.screen, minvalue=0)
        if value is None:
            return
        self.cursor.execute("UPDATE investments SET value = ? WHERE id = ?", (round(value, 2), rid))
        self.conn.commit()
        self.load_investments()

    def delete_investment(self):
        rid = self.selected_investment()
        if rid is None:
            return
        self.cursor.execute("DELETE FROM investments WHERE id = ?", (rid,))
        self.conn.commit()
        self.load_investments()

    def load_investments(self):
        for row in self.inv_tree.get_children():
            self.inv_tree.delete(row)
        self.cursor.execute("SELECT id, name, kind, amount, value, date FROM investments "
                            "ORDER BY date DESC, id DESC")
        rows = self.cursor.fetchall()
        for rid, name, kind, amount, value, date in rows:
            gain = (value - amount) / amount * 100 if amount else 0.0
            self.inv_tree.insert("", tk.END, values=(
                rid, name, kind, f"{amount:,.2f}", f"{value:,.2f}", f"{gain:+.1f}%", date))
        summary = portfolio_summary([(r[2], r[3], r[4]) for r in rows])
        self.inv_stats["invested"].config(text=f"{summary['invested']:,.2f}")
        self.inv_stats["value"].config(text=f"{summary['value']:,.2f}")
        self.inv_stats["gain"].config(
            text=f"{summary['gain']:+,.2f} ({summary['gain_pct']:+.1f}%)",
            fg=BLUE if summary["gain"] >= 0 else TEXT)
        self.refresh_dashboard()
