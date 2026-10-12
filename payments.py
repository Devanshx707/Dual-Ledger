"""Group payments: record who paid whom so balances move toward zero."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

import config as cfg
from config import FONT
from logic import read_amount
from widgets import FlatButton, make_card, make_entry, make_tree


class PaymentsMixin:
    def record_payment(self, group, payer, receiver, amount, date=None):
        date = date or datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute(
            "INSERT INTO settlements (group_name, payer, receiver, amount, date) VALUES (?, ?, ?, ?, ?)",
            (group, payer, receiver, amount, date))
        self.conn.commit()
        self.load_group()

    def mark_paid(self):
        selected = self.settle_tree.selection()
        if not selected:
            messagebox.showerror("Select a payment", "Pick a payment in the Settle up list.")
            return
        index = self.settle_tree.index(selected[0])
        if index >= len(self.suggested):
            return
        debtor, creditor, amount = self.suggested[index]
        self.record_payment(self.view_group.get(), debtor, creditor, amount)

    def close_payments(self):
        if self.pay_win is not None and self.pay_win.winfo_exists():
            self.pay_win.destroy()
        self.pay_win = None

    def open_payments(self):
        group = self.view_group.get()
        if not group:
            messagebox.showinfo("No group", "Add a group expense first.")
            return
        self.close_payments()
        win = tk.Toplevel(self.screen)
        self.pay_win = win
        win.title(f"Payments: {group}")
        win.geometry("540x500")
        win.resizable(False, False)
        win.configure(bg=cfg.BG)
        win.transient(self.screen)

        form = make_card(win)
        form.pack(fill="x", padx=20, pady=(20, 12))
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)
        tk.Label(form, text="Record a payment", bg=cfg.WHITE, fg=cfg.TEXT, font=(FONT, 12, "bold")).grid(
            row=0, column=0, columnspan=2, sticky="w", padx=16, pady=(14, 0))
        self.pay_from = ttk.Combobox(form, values=self.members, state="readonly")
        self.pay_to = ttk.Combobox(form, values=self.members, state="readonly")
        self.pay_amount = make_entry(form, 14)
        self.pay_date = make_entry(form, 14)
        self.pay_date.insert(0, datetime.now().strftime("%Y-%m-%d"))
        cells = [("From (payer)", self.pay_from, 1, 0), ("To (receiver)", self.pay_to, 1, 1),
                 ("Amount", self.pay_amount, 3, 0), ("Date (YYYY-MM-DD)", self.pay_date, 3, 1)]
        for label, widget, row, col in cells:
            tk.Label(form, text=label, bg=cfg.WHITE, fg=cfg.MUTED, font=(FONT, 9)).grid(
                row=row, column=col, sticky="w", padx=16, pady=(10, 2))
            widget.grid(row=row + 1, column=col, sticky="ew", padx=16, ipady=4)
        FlatButton(form, "Record payment", self.add_payment).grid(
            row=5, column=0, columnspan=2, sticky="ew", padx=16, pady=14)

        card = make_card(win)
        card.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        head = tk.Frame(card, bg=cfg.WHITE)
        head.pack(fill="x", padx=16, pady=(12, 6))
        tk.Label(head, text="Payment history", bg=cfg.WHITE, fg=cfg.TEXT, font=(FONT, 12, "bold")).pack(side="left")
        FlatButton(head, "Delete", self.delete_payment, "ghost").pack(side="right")
        self.pay_tree = make_tree(card, ("id", "date", "from", "to", "amount"), (0, 90, 120, 120, 80), 6)
        self.load_payments()

    def add_payment(self):
        payer, receiver = self.pay_from.get(), self.pay_to.get()
        date = self.pay_date.get().strip()
        if not payer or not receiver or payer == receiver:
            messagebox.showerror("Input Error", "Pick two different people.", parent=self.pay_win)
            return
        try:
            amount = read_amount(self.pay_amount.get().strip())
        except ValueError:
            messagebox.showerror("Input Error", "Amount must be a positive number.", parent=self.pay_win)
            return
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Input Error", "Date must use YYYY-MM-DD.", parent=self.pay_win)
            return
        self.record_payment(self.view_group.get(), payer, receiver, amount, date)
        self.pay_amount.delete(0, tk.END)

    def delete_payment(self):
        selected = self.pay_tree.selection()
        if not selected:
            messagebox.showerror("Select a row", "Pick a payment to delete.", parent=self.pay_win)
            return
        payment_id = self.pay_tree.item(selected[0])["values"][0]
        self.cursor.execute("DELETE FROM settlements WHERE id = ?", (payment_id,))
        self.conn.commit()
        self.load_group()

    def load_payments(self):
        if self.pay_win is None or not self.pay_win.winfo_exists():
            return
        self.pay_from["values"] = self.members
        self.pay_to["values"] = self.members
        for row in self.pay_tree.get_children():
            self.pay_tree.delete(row)
        self.cursor.execute(
            "SELECT id, date, payer, receiver, amount FROM settlements WHERE group_name = ? "
            "ORDER BY date DESC, id DESC", (self.view_group.get(),))
        for pid, date, payer, receiver, amount in self.cursor.fetchall():
            self.pay_tree.insert("", tk.END, values=(pid, date, payer, receiver, f"{amount:.2f}"))
