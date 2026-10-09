"""Personal budget page: add, search, edit and delete expenses."""
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from config import CATEGORIES, BG, BLUE, WHITE, TEXT, MUTED, FONT
from logic import read_amount
from widgets import FlatButton, make_card, make_entry, field, make_tree


class PersonalMixin:
    def build_personal(self):
        page = self.pages["personal"]
        self.page_title(page, "Personal Budget", "Track your spending and your investments")
        switch = tk.Frame(page, bg=BG)
        switch.pack(fill="x", pady=(0, 12))
        self.view_chips = {}
        for key, label in (("expenses", "Expenses"), ("investments", "Investments")):
            chip = tk.Label(switch, text=label, padx=16, pady=6, cursor="hand2", font=(FONT, 10, "bold"))
            chip.pack(side="left", padx=(0, 8))
            chip.bind("<Button-1>", lambda e, k=key: self.set_personal_view(k))
            self.view_chips[key] = chip
        body = tk.Frame(page, bg=BG)
        self.exp_body = body

        form = make_card(body)
        form.pack(side="left", fill="y", padx=(0, 16))
        form.columnconfigure(0, weight=1)
        self.form_title = tk.Label(form, text="Add expense", bg=WHITE, fg=TEXT, font=(FONT, 12, "bold"))
        self.form_title.grid(row=0, column=0, sticky="w", padx=16, pady=(16, 0))
        self.amount_entry = make_entry(form)
        self.cat_combo = ttk.Combobox(form, values=CATEGORIES, state="readonly")
        self.date_entry = make_entry(form)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))
        field(form, 1, "Amount", self.amount_entry)
        field(form, 2, "Category", self.cat_combo)
        field(form, 3, "Date (YYYY-MM-DD)", self.date_entry)
        self.save_button = FlatButton(form, "Add entry", self.add_entry)
        self.save_button.grid(row=8, column=0, sticky="ew", padx=16, pady=(18, 16))
        self.cancel_button = FlatButton(form, "Cancel edit", self.end_edit, "ghost")
        self.cancel_button.grid(row=9, column=0, sticky="ew", padx=16, pady=(0, 16))
        self.cancel_button.grid_remove()
        for entry in (self.amount_entry, self.date_entry):
            entry.bind("<Return>", lambda e: self.add_entry())

        right = make_card(body)
        right.pack(side="right", fill="both", expand=True)
        head = tk.Frame(right, bg=WHITE)
        head.pack(fill="x", padx=16, pady=(14, 8))
        tk.Label(head, text="Expense records", bg=WHITE, fg=TEXT, font=(FONT, 12, "bold")).pack(side="left")
        self.search_entry = make_entry(head, width=20)
        self.search_entry.config(textvariable=self.search_var)
        self.search_entry.pack(side="right", ipady=3)
        tk.Label(head, text="Search", bg=WHITE, fg=MUTED, font=(FONT, 9)).pack(side="right", padx=8)
        self.search_var.trace_add("write", lambda *args: self.load_personal(False))

        self.tree = make_tree(right, ("id", "category", "amount", "date"), (0, 150, 110, 110), 14)
        self.tree.bind("<Double-1>", lambda e: self.edit_selected())
        self.tree.bind("<Delete>", lambda e: self.delete_entry())

        foot = tk.Frame(right, bg=WHITE)
        foot.pack(fill="x", padx=16, pady=(0, 14))
        self.total_label = tk.Label(foot, text="", bg=WHITE, fg=TEXT, font=(FONT, 11, "bold"))
        self.total_label.pack(side="left")
        FlatButton(foot, "Delete all", self.delete_all_entries, "ghost").pack(side="right")
        FlatButton(foot, "Delete", self.delete_entry, "ghost").pack(side="right", padx=6)
        FlatButton(foot, "Edit", self.edit_selected).pack(side="right")

        self.build_investments(page)
        self.set_personal_view("expenses")

    def set_personal_view(self, view):
        self.exp_body.pack_forget()
        self.inv_body.pack_forget()
        (self.exp_body if view == "expenses" else self.inv_body).pack(fill="both", expand=True)
        for key, chip in self.view_chips.items():
            chip.config(bg=BLUE if key == view else WHITE, fg=WHITE if key == view else MUTED)

    def add_entry(self):
        category = self.cat_combo.get()
        date = self.date_entry.get().strip()
        if not self.amount_entry.get().strip() or not category or not date:
            messagebox.showerror("Input Error", "Please fill in all fields.")
            return
        try:
            amount = read_amount(self.amount_entry.get().strip())
        except ValueError:
            messagebox.showerror("Input Error", "Amount must be a positive number.")
            return
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Input Error", "Date must use YYYY-MM-DD.")
            return
        if self.edit_id:
            self.cursor.execute(
                "UPDATE personal_expenses SET category = ?, amount = ?, date = ? WHERE id = ?",
                (category, amount, date, self.edit_id))
            self.conn.commit()
            self.end_edit()
        else:
            self.cursor.execute("INSERT INTO personal_expenses (category, amount, date) VALUES (?, ?, ?)",
                                (category, amount, date))
            self.conn.commit()
            self.amount_entry.delete(0, tk.END)
        self.load_personal()

    def start_edit(self, rid):
        self.cursor.execute("SELECT category, amount, date FROM personal_expenses WHERE id = ?", (rid,))
        row = self.cursor.fetchone()
        if not row:
            return
        self.edit_id = rid
        self.cat_combo.set(row[0])
        self.amount_entry.delete(0, tk.END)
        self.amount_entry.insert(0, f"{row[1]:.2f}")
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, row[2])
        self.form_title.config(text=f"Edit expense #{rid}")
        self.save_button.config(text="Save changes")
        self.cancel_button.grid()
        self.show_page("personal")

    def end_edit(self):
        self.edit_id = None
        self.form_title.config(text="Add expense")
        self.save_button.config(text="Add entry")
        self.cancel_button.grid_remove()
        self.amount_entry.delete(0, tk.END)
        self.cat_combo.set("")
        self.date_entry.delete(0, tk.END)
        self.date_entry.insert(0, datetime.now().strftime("%Y-%m-%d"))

    def edit_selected(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Select a row", "Pick a record to edit.")
            return
        self.start_edit(self.tree.item(selected[0])["values"][0])

    def delete_entry(self):
        selected = self.tree.selection()
        if not selected:
            messagebox.showerror("Select a row", "Pick a record to delete.")
            return
        record_id = self.tree.item(selected[0])["values"][0]
        self.cursor.execute("DELETE FROM personal_expenses WHERE id = ?", (record_id,))
        self.conn.commit()
        if self.edit_id == record_id:
            self.end_edit()
        self.load_personal()

    def delete_all_entries(self):
        self.cursor.execute("SELECT COUNT(*) FROM personal_expenses")
        if self.cursor.fetchone()[0] == 0:
            messagebox.showinfo("Nothing to delete", "There are no personal expenses.")
            return
        if not messagebox.askyesno("Delete All", "Delete every personal expense? This cannot be undone."):
            return
        self.cursor.execute("DELETE FROM personal_expenses")
        self.cursor.execute("DELETE FROM sqlite_sequence WHERE name = 'personal_expenses'")
        self.conn.commit()
        self.end_edit()
        self.load_personal()

    def load_personal(self, refresh_dash=True):
        term = self.search_var.get().strip().lower()
        for row in self.tree.get_children():
            self.tree.delete(row)
        self.cursor.execute("SELECT id, category, amount, date FROM personal_expenses "
                            "ORDER BY date DESC, id DESC")
        shown, total = 0, 0.0
        for rid, cat, amt, date in self.cursor.fetchall():
            amount_text = f"{amt:.2f}"
            if term and term not in f"{cat} {amount_text} {date}".lower():
                continue
            self.tree.insert("", tk.END, values=(rid, cat, amount_text, date))
            total += amt
            shown += 1
        self.total_label.config(text=f"{shown} entries | Total: {total:,.2f}")
        if refresh_dash:
            self.refresh_dashboard()
