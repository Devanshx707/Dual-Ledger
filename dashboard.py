"""Dashboard page: total, category bars and recent entries."""
import tkinter as tk
from tkinter import messagebox
from datetime import datetime

from config import CATEGORIES, BLUE, BLUE_LIGHT, WHITE, BG, TEXT, MUTED, FONT
from widgets import FlatButton, make_card, make_bar, draw_bar


class DashboardMixin:
    def build_dashboard(self):
        page = self.pages["dashboard"]
        self.page_title(page, "Dashboard", "Overview of your personal spending")

        hero = make_card(page)
        hero.pack(fill="x", pady=(0, 16))
        tk.Label(hero, text="Total spent", bg=WHITE, fg=MUTED, font=(FONT, 10)).pack(
            anchor="w", padx=24, pady=(18, 0))
        self.hero_total = tk.Label(hero, text="0.00", bg=WHITE, fg=TEXT, font=(FONT, 28, "bold"))
        self.hero_total.pack(anchor="w", padx=24)
        row = tk.Frame(hero, bg=WHITE)
        row.pack(fill="x", padx=24, pady=(10, 4))
        self.hero_pct = tk.Label(row, text="0%", bg=BLUE, fg=WHITE, font=(FONT, 16, "bold"),
                                 width=6, pady=10)
        self.hero_pct.pack(side="left")
        self.hero_bar = make_bar(row, 46)
        self.hero_bar.pack(side="left", fill="x", expand=True, padx=(8, 0))
        self.hero_caption = tk.Label(hero, text="", bg=WHITE, fg=MUTED, font=(FONT, 9))
        self.hero_caption.pack(anchor="w", padx=24, pady=(0, 16))

        lower = tk.Frame(page, bg=BG)
        lower.pack(fill="both", expand=True)

        cat_card = make_card(lower)
        tk.Label(cat_card, text="Spending by category", bg=WHITE, fg=TEXT,
                 font=(FONT, 12, "bold")).pack(anchor="w", padx=16, pady=(14, 0))
        tk.Label(cat_card, text="Click a category to filter recent entries", bg=WHITE, fg=MUTED,
                 font=(FONT, 9)).pack(anchor="w", padx=16, pady=(0, 6))
        self.cat_frame = tk.Frame(cat_card, bg=WHITE)
        self.cat_frame.pack(fill="x", padx=8, pady=(0, 14))

        recent = make_card(lower)
        recent.pack(side="right", fill="y")
        cat_card.pack(side="left", fill="both", expand=True, padx=(0, 16))
        recent.configure(width=340)
        recent.pack_propagate(False)
        head = tk.Frame(recent, bg=WHITE)
        head.pack(fill="x", padx=16, pady=(14, 6))
        self.recent_title = tk.Label(head, text="Recent entries", bg=WHITE, fg=TEXT,
                                     font=(FONT, 12, "bold"))
        self.recent_title.pack(side="left")
        self.recent_clear = FlatButton(head, "Clear", self.clear_filter, "ghost")
        actions = tk.Frame(recent, bg=WHITE)
        actions.pack(side="bottom", fill="x", padx=16, pady=14)
        FlatButton(actions, "Edit", self.edit_recent).pack(side="left")
        FlatButton(actions, "Delete", self.delete_recent, "ghost").pack(side="left", padx=6)
        self.recent_list = tk.Frame(recent, bg=WHITE)
        self.recent_list.pack(fill="both", expand=True, padx=8)

    def paint(self, widgets, color):
        for widget in widgets:
            widget.config(bg=color)

    def refresh_dashboard(self):
        self.cursor.execute("SELECT category, SUM(amount) FROM personal_expenses GROUP BY category")
        totals = dict(self.cursor.fetchall())
        total = sum(totals.values())
        month = datetime.now().strftime("%Y-%m")
        self.cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM personal_expenses WHERE date LIKE ?",
                            (month + "%",))
        month_total = self.cursor.fetchone()[0]
        share = month_total / total if total else 0

        self.hero_total.config(text=f"{total:,.2f}")
        self.hero_pct.config(text=f"{share * 100:.0f}%")
        draw_bar(self.hero_bar, share)
        self.hero_caption.config(text=f"This month: {month_total:,.2f} of all spending")

        for widget in self.cat_frame.winfo_children():
            widget.destroy()
        for cat in CATEGORIES:
            value = totals.get(cat, 0.0)
            part = value / total if total else 0
            active = self.cat_filter == cat
            bg = BLUE_LIGHT if active else WHITE
            row = tk.Frame(self.cat_frame, bg=bg, cursor="hand2")
            row.pack(fill="x", pady=1)
            row.columnconfigure(1, weight=1)
            name = tk.Label(row, text=cat, bg=bg, fg=TEXT, font=(FONT, 10, "bold"), width=13, anchor="w")
            name.grid(row=0, column=0, padx=(8, 0), pady=8)
            bar = tk.Canvas(row, height=8, bg=bg, highlightthickness=0)
            bar.bind("<Configure>", lambda e, c=bar: draw_bar(c))
            bar.grid(row=0, column=1, sticky="ew", padx=12)
            draw_bar(bar, part)
            amount = tk.Label(row, text=f"{value:,.2f}", bg=bg, fg=MUTED, font=(FONT, 10),
                              width=10, anchor="e")
            amount.grid(row=0, column=2)
            pct = tk.Label(row, text=f"{part * 100:.0f}%", bg=bg, fg=BLUE, font=(FONT, 10, "bold"),
                           width=5, anchor="e")
            pct.grid(row=0, column=3, padx=(0, 8))
            widgets = [row, name, bar, amount, pct]
            for widget in widgets:
                widget.bind("<Button-1>", lambda e, c=cat: self.toggle_category(c))
                widget.bind("<Enter>", lambda e, ws=widgets, a=active: None if a else self.paint(ws, BG))
                widget.bind("<Leave>", lambda e, ws=widgets, a=active: None if a else self.paint(ws, WHITE))
        self.render_recent()

    def toggle_category(self, cat):
        self.cat_filter = None if self.cat_filter == cat else cat
        self.recent_selected = None
        self.refresh_dashboard()

    def clear_filter(self):
        self.cat_filter = None
        self.recent_selected = None
        self.refresh_dashboard()

    def render_recent(self):
        for widget in self.recent_list.winfo_children():
            widget.destroy()
        self.recent_rows = {}
        query = "SELECT id, category, amount, date FROM personal_expenses"
        params = ()
        if self.cat_filter:
            query += " WHERE category = ?"
            params = (self.cat_filter,)
        query += " ORDER BY date DESC, id DESC LIMIT 5"
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()

        if self.cat_filter:
            self.recent_title.config(text=self.cat_filter)
            self.recent_clear.pack(side="right")
        else:
            self.recent_title.config(text="Recent entries")
            self.recent_clear.pack_forget()
        if self.recent_selected not in [r[0] for r in rows]:
            self.recent_selected = None
        if not rows:
            tk.Label(self.recent_list, text="No entries yet.", bg=WHITE, fg=MUTED,
                     font=(FONT, 10)).pack(pady=28)
            return

        for rid, cat, amt, date in rows:
            bg = BLUE_LIGHT if rid == self.recent_selected else WHITE
            row = tk.Frame(self.recent_list, bg=bg, cursor="hand2")
            row.pack(fill="x", pady=1)
            left = tk.Frame(row, bg=bg)
            left.pack(side="left", padx=10, pady=6)
            name = tk.Label(left, text=cat, bg=bg, fg=TEXT, font=(FONT, 10, "bold"))
            name.pack(anchor="w")
            when = tk.Label(left, text=date, bg=bg, fg=MUTED, font=(FONT, 9))
            when.pack(anchor="w")
            amount = tk.Label(row, text=f"{amt:,.2f}", bg=bg, fg=BLUE, font=(FONT, 11, "bold"))
            amount.pack(side="right", padx=12)
            widgets = [row, left, name, when, amount]
            self.recent_rows[rid] = widgets
            for widget in widgets:
                widget.bind("<Button-1>", lambda e, r=rid: self.select_recent(r))
                widget.bind("<Double-Button-1>", lambda e, r=rid: self.start_edit(r))
                widget.bind("<Enter>", lambda e, r=rid: self.hover_recent(r, True))
                widget.bind("<Leave>", lambda e, r=rid: self.hover_recent(r, False))

    def select_recent(self, rid):
        if self.recent_selected in self.recent_rows:
            self.paint(self.recent_rows[self.recent_selected], WHITE)
        self.recent_selected = None if self.recent_selected == rid else rid
        if self.recent_selected is not None:
            self.paint(self.recent_rows[rid], BLUE_LIGHT)

    def hover_recent(self, rid, inside):
        if rid != self.recent_selected and rid in self.recent_rows:
            self.paint(self.recent_rows[rid], BG if inside else WHITE)

    def edit_recent(self):
        if self.recent_selected is None:
            messagebox.showerror("Select an entry", "Click an entry first.")
            return
        self.start_edit(self.recent_selected)

    def delete_recent(self):
        if self.recent_selected is None:
            messagebox.showerror("Select an entry", "Click an entry first.")
            return
        if not messagebox.askyesno("Delete entry", "Delete the selected entry?"):
            return
        self.cursor.execute("DELETE FROM personal_expenses WHERE id = ?", (self.recent_selected,))
        self.conn.commit()
        if self.edit_id == self.recent_selected:
            self.end_edit()
        self.recent_selected = None
        self.load_personal()
