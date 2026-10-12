"""Entry point. Run this file: python app.py"""
import tkinter as tk

import config as cfg
from config import DB_NAME, FONT
from database import connect_db, get_setting, set_setting
from widgets import ToggleSwitch, setup_style
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
        self.conn, self.cursor = connect_db(db_path)
        cfg.apply_theme(get_setting(self.cursor, "theme", "light"))

        self.cat_filter = None
        self.recent_selected = None
        self.recent_rows = {}
        self.edit_id = None
        self.chart_metric = "spending"
        self.chart_data = []
        self.chart_selected = None
        self.chart_hover = None
        self.chart_hit = []
        self.current_page = "dashboard"
        self.build_ui("dashboard")

    def build_ui(self, page):
        """Builds every screen from scratch with the colors of the current theme."""
        for child in self.screen.winfo_children():
            child.destroy()
        self.screen.configure(bg=cfg.BG)
        setup_style()
        self.search_var = tk.StringVar()
        self.recent_rows = {}
        self.chart_hit = []

        self.sidebar = tk.Frame(self.screen, bg=cfg.SIDEBAR, width=200)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)
        tk.Label(self.sidebar, text="Dual-Ledger", bg=cfg.SIDEBAR, fg=cfg.ONBLUE,
                 font=(FONT, 16, "bold")).pack(anchor="w", padx=24, pady=(28, 2))
        tk.Label(self.sidebar, text="Budget and groups", bg=cfg.SIDEBAR, fg=cfg.BLUE_LIGHT,
                 font=(FONT, 9)).pack(anchor="w", padx=24, pady=(0, 28))

        self.content = tk.Frame(self.screen, bg=cfg.BG)
        self.content.pack(side="right", fill="both", expand=True)

        self.pages, self.nav = {}, {}
        for key, label in (("dashboard", "Dashboard"), ("personal", "Personal Budget"),
                           ("group", "Group Splitter")):
            nav = tk.Label(self.sidebar, text=label, anchor="w", padx=24, pady=12,
                           cursor="hand2", font=(FONT, 11, "bold"))
            nav.pack(fill="x")
            nav.bind("<Button-1>", lambda e, k=key: self.show_page(k))
            self.nav[key] = nav
            self.pages[key] = tk.Frame(self.content, bg=cfg.BG)

        row = tk.Frame(self.sidebar, bg=cfg.SIDEBAR)
        row.pack(side="bottom", fill="x", padx=24, pady=(0, 24))
        caption = tk.Label(row, text="Dark mode", bg=cfg.SIDEBAR, fg=cfg.BLUE_LIGHT,
                           font=(FONT, 10, "bold"), cursor="hand2")
        caption.pack(side="left")
        self.theme_switch = ToggleSwitch(row, cfg.THEME == "dark", self.toggle_theme, cfg.SIDEBAR)
        self.theme_switch.pack(side="right")
        caption.bind("<Button-1>", lambda e: self.theme_switch.toggle())

        self.build_dashboard()
        self.build_personal()
        self.build_group()
        self.load_personal()
        self.load_investments()
        self.refresh_groups()
        self.show_page(page)

    def toggle_theme(self):
        name = "dark" if cfg.THEME == "light" else "light"
        cfg.apply_theme(name)
        set_setting(self.conn, self.cursor, "theme", name)
        self.edit_id = None
        self.recent_selected = None
        self.chart_selected = None
        self.chart_hover = None
        self.build_ui(self.current_page)

    def show_page(self, key):
        self.current_page = key
        for page in self.pages.values():
            page.pack_forget()
        self.pages[key].pack(fill="both", expand=True, padx=28, pady=24)
        for name, nav in self.nav.items():
            if name == key:
                nav.config(bg=cfg.SIDE_ACTIVE, fg=cfg.ONBLUE)
            else:
                nav.config(bg=cfg.SIDEBAR, fg=cfg.BLUE_LIGHT)
        if key == "dashboard":
            self.refresh_dashboard()

    def page_title(self, page, title, subtitle):
        tk.Label(page, text=title, bg=cfg.BG, fg=cfg.TEXT, font=(FONT, 20, "bold")).pack(anchor="w")
        tk.Label(page, text=subtitle, bg=cfg.BG, fg=cfg.MUTED, font=(FONT, 10)).pack(anchor="w", pady=(0, 16))

    def run(self):
        self.screen.mainloop()


if __name__ == "__main__":
    FinanceApp().run()
