"""Entry point. Run this file: python app.py"""
import tkinter as tk

from config import DB_NAME, BLUE, BLUE_DARK, BLUE_LIGHT, BG, WHITE, TEXT, MUTED, FONT
from database import connect_db
from widgets import setup_style
from dashboard import DashboardMixin
from personal import PersonalMixin
from group import GroupMixin
from investments import InvestmentsMixin
from stats import StatsMixin


class FinanceApp(DashboardMixin, PersonalMixin, GroupMixin, InvestmentsMixin, StatsMixin):
    """Window, sidebar and navigation. Each page lives in its own file as a mixin."""

    def __init__(self, db_path=DB_NAME):
        self.screen = tk.Tk()
        self.screen.title("Dual-Ledger")
        self.screen.geometry("1100x720")
        self.screen.resizable(False, False)
        self.screen.configure(bg=BG)
        setup_style()
        self.conn, self.cursor = connect_db(db_path)

        self.sidebar = tk.Frame(self.screen, bg=BLUE, width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        tk.Label(self.sidebar, text="Dual-Ledger", bg=BLUE, fg=WHITE,
                 font=(FONT, 16, "bold")).pack(anchor="w", padx=24, pady=(28, 2))
        tk.Label(self.sidebar, text="Budget and groups", bg=BLUE, fg=BLUE_LIGHT,
                 font=(FONT, 9)).pack(anchor="w", padx=24, pady=(0, 28))

        self.content = tk.Frame(self.screen, bg=BG)
        self.content.pack(side="right", fill="both", expand=True)

        self.pages, self.nav = {}, {}
        for key, label in (("dashboard", "Dashboard"), ("personal", "Personal Budget"),
                           ("group", "Group Splitter")):
            nav = tk.Label(self.sidebar, text=label, anchor="w", padx=24, pady=12,
                           cursor="hand2", font=(FONT, 11, "bold"))
            nav.pack(fill="x")
            nav.bind("<Button-1>", lambda e, k=key: self.show_page(k))
            self.nav[key] = nav
            self.pages[key] = tk.Frame(self.content, bg=BG)

        self.cat_filter = None
        self.recent_selected = None
        self.recent_rows = {}
        self.edit_id = None
        self.chart_metric = "spending"
        self.chart_data = []
        self.chart_selected = None
        self.chart_hover = None
        self.chart_hit = []
        self.search_var = tk.StringVar()
        self.build_dashboard()
        self.build_personal()
        self.build_group()
        self.load_personal()
        self.load_investments()
        self.refresh_groups()
        self.show_page("dashboard")

    def show_page(self, key):
        for page in self.pages.values():
            page.pack_forget()
        self.pages[key].pack(fill="both", expand=True, padx=28, pady=24)
        for name, nav in self.nav.items():
            if name == key:
                nav.config(bg=BLUE_DARK, fg=WHITE)
            else:
                nav.config(bg=BLUE, fg=BLUE_LIGHT)
        if key == "dashboard":
            self.refresh_dashboard()

    def page_title(self, page, title, subtitle):
        tk.Label(page, text=title, bg=BG, fg=TEXT, font=(FONT, 20, "bold")).pack(anchor="w")
        tk.Label(page, text=subtitle, bg=BG, fg=MUTED, font=(FONT, 10)).pack(anchor="w", pady=(0, 16))

    def run(self):
        self.screen.mainloop()


if __name__ == "__main__":
    FinanceApp().run()
