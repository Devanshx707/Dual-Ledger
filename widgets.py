"""Reusable UI pieces: buttons, cards, inputs, tables, bars and the ttk theme."""
import tkinter as tk
from tkinter import ttk

import config as cfg
from config import FONT


class FlatButton(tk.Label):
    def __init__(self, parent, text, command, kind="primary"):
        colors = {"primary": (cfg.BLUE, cfg.ONBLUE, cfg.BLUE_DARK), "ghost": (cfg.BORDER, cfg.TEXT, cfg.HOVER)}
        self._base, fg, self._hover = colors[kind]
        super().__init__(parent, text=text, bg=self._base, fg=fg, font=(FONT, 10, "bold"),
                         padx=14, pady=7, cursor="hand2")
        self._cmd = command
        self.bind("<Button-1>", lambda e: self._cmd())
        self.bind("<Enter>", lambda e: self.config(bg=self._hover))
        self.bind("<Leave>", lambda e: self.config(bg=self._base))


class ToggleSwitch(tk.Canvas):
    """A sliding on/off switch. The knob moves first, then command() runs."""
    WIDTH, HEIGHT, PAD = 46, 26, 3

    def __init__(self, parent, on, command, bg):
        super().__init__(parent, width=self.WIDTH, height=self.HEIGHT, bg=bg,
                         highlightthickness=0, cursor="hand2")
        self.on = on
        self._command = command
        self._busy = False
        self._x = self._knob_x(on)
        self.bind("<Button-1>", lambda e: self.toggle())
        self._draw()

    def _knob_x(self, on):
        radius = self.HEIGHT / 2 - self.PAD
        return self.WIDTH - self.PAD - radius if on else self.PAD + radius

    def _draw(self):
        self.delete("all")
        w, h = self.WIDTH, self.HEIGHT
        track = cfg.BLUE_LIGHT if self.on else cfg.SIDE_ACTIVE
        knob = cfg.SIDEBAR if self.on else cfg.ONBLUE
        self.create_oval(0, 0, h, h, fill=track, outline=track)
        self.create_oval(w - h, 0, w, h, fill=track, outline=track)
        self.create_rectangle(h / 2, 0, w - h / 2, h, fill=track, outline=track)
        radius = h / 2 - self.PAD
        self.create_oval(self._x - radius, h / 2 - radius, self._x + radius, h / 2 + radius,
                         fill=knob, outline=knob)

    def toggle(self):
        if self._busy:
            return
        self._busy = True
        self.on = not self.on
        self._slide(self._knob_x(self.on))

    def _slide(self, goal):
        if not self.winfo_exists():
            return
        distance = goal - self._x
        if abs(distance) <= 2:
            self._x = goal
            self._draw()
            self.after(70, self._finish)
            return
        self._x += 2 if distance > 0 else -2
        self._draw()
        self.after(8, lambda: self._slide(goal))

    def _finish(self):
        if self.winfo_exists():
            self._busy = False
            self._command()


def make_card(parent):
    return tk.Frame(parent, bg=cfg.WHITE, highlightbackground=cfg.BORDER, highlightthickness=1)


def make_entry(parent, width=28):
    return tk.Entry(parent, width=width, font=(FONT, 10), bg=cfg.INPUT, fg=cfg.TEXT, relief="flat",
                    highlightthickness=1, highlightbackground=cfg.BORDER, highlightcolor=cfg.BLUE,
                    insertbackground=cfg.TEXT)


def field(parent, index, label, widget):
    tk.Label(parent, text=label, bg=cfg.WHITE, fg=cfg.MUTED, font=(FONT, 9)).grid(
        row=index * 2, column=0, sticky="w", padx=16, pady=(10, 2))
    widget.grid(row=index * 2 + 1, column=0, sticky="ew", padx=16, ipady=4)


def make_tree(parent, columns, widths, height):
    frame = tk.Frame(parent, bg=cfg.WHITE)
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
    canvas.create_rectangle(0, 0, w, h, fill=cfg.TRACK, outline="")
    canvas.create_rectangle(0, 0, int(w * getattr(canvas, "fraction", 0)), h, fill=cfg.BLUE, outline="")


def make_bar(parent, height):
    canvas = tk.Canvas(parent, height=height, bg=cfg.WHITE, highlightthickness=0)
    canvas.bind("<Configure>", lambda e: draw_bar(canvas))
    return canvas


def setup_style():
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("Ledger.Treeview", background=cfg.WHITE, fieldbackground=cfg.WHITE, foreground=cfg.TEXT,
                    rowheight=30, borderwidth=0, font=(FONT, 10),
                    bordercolor=cfg.BORDER, lightcolor=cfg.BORDER, darkcolor=cfg.BORDER)
    style.configure("Ledger.Treeview.Heading", background=cfg.BG, foreground=cfg.MUTED,
                    font=(FONT, 9, "bold"), relief="flat", padding=6)
    style.map("Ledger.Treeview", background=[("selected", cfg.SELECT)],
              foreground=[("selected", cfg.TEXT)])
    style.configure("TCombobox", fieldbackground=cfg.INPUT, background=cfg.INPUT, foreground=cfg.TEXT,
                    bordercolor=cfg.BORDER, lightcolor=cfg.BORDER, darkcolor=cfg.BORDER,
                    arrowcolor=cfg.MUTED, padding=5)
    style.map("TCombobox", fieldbackground=[("readonly", cfg.INPUT)], foreground=[("readonly", cfg.TEXT)],
              selectbackground=[("readonly", cfg.INPUT)], selectforeground=[("readonly", cfg.TEXT)])
    root = style.master
    for option, value in (("background", cfg.INPUT), ("foreground", cfg.TEXT),
                          ("selectBackground", cfg.SELECT), ("selectForeground", cfg.TEXT)):
        root.option_add(f"*TCombobox*Listbox.{option}", value)
    style.configure("TScrollbar", background=cfg.BORDER, troughcolor=cfg.WHITE, bordercolor=cfg.WHITE,
                    lightcolor=cfg.BORDER, darkcolor=cfg.BORDER, arrowcolor=cfg.MUTED, relief="flat")
    style.map("TScrollbar", background=[("active", cfg.HOVER)])
