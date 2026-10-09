"""Statistics chart on the dashboard: monthly bars with hover, click and a spending or investing switch."""
import tkinter as tk
from datetime import date

from config import BG, BLUE, BLUE_DARK, BORDER, WHITE, TEXT, MUTED, FONT
from logic import monthly_totals, nice_ceiling, compact_number


class StatsMixin:
    def build_stats_chart(self, parent):
        frame = tk.Frame(parent, bg=WHITE)
        self.chart_frame = frame
        bar = tk.Frame(frame, bg=WHITE)
        bar.pack(fill="x", padx=16)
        self.metric_chips = {}
        for key, label in (("spending", "Spending"), ("investing", "Investing")):
            chip = tk.Label(bar, text=label, padx=10, pady=3, cursor="hand2", font=(FONT, 9, "bold"))
            chip.pack(side="left", padx=(0, 6))
            chip.bind("<Button-1>", lambda e, k=key: self.set_metric(k))
            self.metric_chips[key] = chip
        self.stats_info = tk.Label(bar, text="", bg=WHITE, fg=MUTED, font=(FONT, 9))
        self.stats_info.pack(side="right")

        self.chart = tk.Canvas(frame, bg=WHITE, highlightthickness=0, height=220)
        self.chart.pack(fill="both", expand=True, padx=16, pady=(6, 12))
        self.chart.bind("<Configure>", lambda e: self.draw_chart())
        self.chart.bind("<Motion>", self.on_chart_motion)
        self.chart.bind("<Leave>", self.on_chart_leave)
        self.chart.bind("<Button-1>", self.on_chart_click)
        self.paint_metric_chips()

    def set_stats_view(self, view):
        self.cat_frame.pack_forget()
        self.chart_frame.pack_forget()
        if view == "monthly":
            self.chart_frame.pack(fill="both", expand=True)
            self.stats_hint.config(text="Last 6 months. Hover a bar for details, click to pin it.")
        else:
            self.cat_frame.pack(fill="x", padx=8, pady=(0, 14))
            self.stats_hint.config(text="Click a category to filter recent entries")
        for key, chip in self.stats_chips.items():
            chip.config(bg=BLUE if key == view else BG, fg=WHITE if key == view else MUTED)

    def paint_metric_chips(self):
        for key, chip in self.metric_chips.items():
            chip.config(bg=BLUE if key == self.chart_metric else BG,
                        fg=WHITE if key == self.chart_metric else MUTED)

    def set_metric(self, metric):
        self.chart_metric = metric
        self.chart_selected = None
        self.chart_hover = None
        self.paint_metric_chips()
        self.refresh_stats()

    def refresh_stats(self):
        table = "personal_expenses" if self.chart_metric == "spending" else "investments"
        self.cursor.execute(f"SELECT amount, date FROM {table}")
        self.chart_data = monthly_totals(self.cursor.fetchall(), date.today())
        self.draw_chart()
        self.update_stats_info()

    def draw_chart(self):
        canvas = self.chart
        canvas.delete("all")
        self.chart_hit = []
        width, height = canvas.winfo_width(), canvas.winfo_height()
        if width < 80 or height < 80 or not self.chart_data:
            return
        left, right, top, bottom = 46, 56, 22, 26
        plot_w, plot_h = width - left - right, height - top - bottom
        values = [v for _, _, v in self.chart_data]
        peak = nice_ceiling(max(values))
        base = top + plot_h

        for fraction in (0, 0.5, 1):
            y = base - plot_h * fraction
            canvas.create_line(left, y, left + plot_w, y, fill=BORDER)
            canvas.create_text(left - 6, y, text=compact_number(peak * fraction), anchor="e",
                               fill=MUTED, font=(FONT, 8))

        slot = plot_w / len(self.chart_data)
        bar_w = slot * 0.5
        for i, (_, label, value) in enumerate(self.chart_data):
            x0 = left + slot * i + (slot - bar_w) / 2
            x1 = x0 + bar_w
            y0 = base - plot_h * value / peak
            active = i in (self.chart_selected, self.chart_hover)
            if value > 0:
                canvas.create_rectangle(x0, y0, x1, base, fill=BLUE_DARK if active else BLUE, outline="")
                canvas.create_text((x0 + x1) / 2, y0 - 8, text=compact_number(value),
                                   fill=TEXT if active else MUTED, font=(FONT, 8, "bold"))
            else:
                canvas.create_rectangle(x0, base - 2, x1, base, fill=BORDER, outline="")
            canvas.create_text((x0 + x1) / 2, base + 13, text=label,
                               fill=TEXT if active else MUTED, font=(FONT, 9, "bold" if active else "normal"))
            self.chart_hit.append((left + slot * i, left + slot * (i + 1), i))

        filled = [v for v in values if v > 0]
        if filled:
            average = sum(filled) / len(filled)
            y = base - plot_h * average / peak
            canvas.create_line(left, y, left + plot_w, y, fill=MUTED, dash=(4, 3))
            canvas.create_text(left + plot_w + 6, y, anchor="w", text=f"Avg {compact_number(average)}",
                               fill=MUTED, font=(FONT, 8))

    def bar_at(self, x):
        for start, end, index in self.chart_hit:
            if start <= x < end:
                return index
        return None

    def on_chart_motion(self, event):
        index = self.bar_at(event.x)
        if index != self.chart_hover:
            self.chart_hover = index
            self.draw_chart()
            self.update_stats_info()

    def on_chart_leave(self, event):
        self.chart_hover = None
        self.draw_chart()
        self.update_stats_info()

    def on_chart_click(self, event):
        index = self.bar_at(event.x)
        self.chart_selected = None if index == self.chart_selected else index
        self.draw_chart()
        self.update_stats_info()

    def update_stats_info(self):
        index = self.chart_hover if self.chart_hover is not None else self.chart_selected
        if index is None or index >= len(self.chart_data):
            self.stats_info.config(text="")
            return
        key, label, value = self.chart_data[index]
        text = f"{label} {key[:4]}: {value:,.2f}"
        if index > 0 and self.chart_data[index - 1][2] > 0:
            previous = self.chart_data[index - 1]
            change = (value - previous[2]) / previous[2] * 100
            text += f" ({change:+.0f}% vs {previous[1]})"
        self.stats_info.config(text=text)
