"""Reusable UI pieces: buttons, cards, inputs, tables, bars and the ttk theme."""
import tkinter as tk
from tkinter import ttk

from config import BLUE, BLUE_DARK, BLUE_LIGHT, WHITE, BG, BORDER, TRACK, TEXT, MUTED, FONT


class FlatButton(tk.Label):
    def __init__(self, parent, text, command, kind="primary"):
        colors = {"primary": (BLUE, WHITE, BLUE_DARK), "ghost": (BORDER, TEXT, "#D1D5DB")}
        self._base, fg, self._hover = colors[kind]
        super().__init__(parent, text=text, bg=self._base, fg=fg, font=(FONT, 10, "bold"),
                         padx=14, pady=7, cursor="hand2")
        self._cmd = command
        self.bind("<Button-1>", lambda e: self._cmd())
        self.bind("<Enter>", lambda e: self.config(bg=self._hover))
        self.bind("<Leave>", lambda e: self.config(bg=self._base))


def make_card(parent):
    return tk.Frame(parent, bg=WHITE, highlightbackground=BORDER, highlightthickness=1)


def make_entry(parent, width=28):
    return tk.Entry(parent, width=width, font=(FONT, 10), bg=WHITE, fg=TEXT, relief="flat",
                    highlightthickness=1, highlightbackground=BORDER, highlightcolor=BLUE,
                    insertbackground=TEXT)


def field(parent, index, label, widget):
    tk.Label(parent, text=label, bg=WHITE, fg=MUTED, font=(FONT, 9)).grid(
        row=index * 2, column=0, sticky="w", padx=16, pady=(10, 2))
    widget.grid(row=index * 2 + 1, column=0, sticky="ew", padx=16, ipady=4)


def make_tree(parent, columns, widths, height):
    frame = tk.Frame(parent, bg=WHITE)
    frame.pack(fill="both", expand=True, padx=8, pady=(0, 8))
    tree = ttk.Treeview(frame, columns=columns, show="headings", height=height, style="Ledger.Treeview")
    for col, width in zip(columns, widths):
        tree.heading(col, text=col.title(), anchor="w")
        tree.column(col, width=width, anchor="w")
    tree["displaycolumns"] = [c for c in columns if c != "id"]
    scroll = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scroll.set)
    tree.pack(side="left", fill="both", expand=True)
    scroll.pack(side="right", fill="y")
    return tree


def draw_bar(canvas, fraction=None):
    if fraction is not None:
        canvas.fraction = fraction
    canvas.delete("all")
    w, h = canvas.winfo_width(), canvas.winfo_height()
    canvas.create_rectangle(0, 0, w, h, fill=TRACK, outline="")
    canvas.create_rectangle(0, 0, int(w * getattr(canvas, "fraction", 0)), h, fill=BLUE, outline="")


def make_bar(parent, height):
    canvas = tk.Canvas(parent, height=height, bg=WHITE, highlightthickness=0)
    canvas.bind("<Configure>", lambda e: draw_bar(canvas))
    return canvas


def setup_style():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Ledger.Treeview", background=WHITE, fieldbackground=WHITE, foreground=TEXT,
                    rowheight=30, borderwidth=0, font=(FONT, 10))
    style.configure("Ledger.Treeview.Heading", background=BG, foreground=MUTED,
                    font=(FONT, 9, "bold"), relief="flat", padding=6)
    style.map("Ledger.Treeview", background=[("selected", BLUE_LIGHT)],
              foreground=[("selected", TEXT)])
    style.configure("TCombobox", fieldbackground=WHITE, background=WHITE, bordercolor=BORDER,
                    lightcolor=BORDER, darkcolor=BORDER, arrowcolor=MUTED, padding=5)
    style.map("TCombobox", fieldbackground=[("readonly", WHITE)],
              selectbackground=[("readonly", WHITE)], selectforeground=[("readonly", TEXT)])
    style.configure("Vertical.TScrollbar", background=BORDER, troughcolor=WHITE,
                    bordercolor=WHITE, arrowcolor=MUTED, relief="flat")
