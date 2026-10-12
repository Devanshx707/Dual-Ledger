"""Data tools: export every table to CSV files and save a backup copy of the database."""
import csv
import os
import sqlite3 as sql
from datetime import datetime
from tkinter import messagebox, filedialog

EXPORTS = {
    "personal_expenses.csv": (
        "SELECT id, category, amount, date FROM personal_expenses ORDER BY date, id",
        ["id", "category", "amount", "date"]),
    "group_expenses.csv": (
        "SELECT id, group_name, payer, amount, category, date, participants FROM group_expenses "
        "ORDER BY group_name, date, id",
        ["id", "group", "paid_by", "amount", "category", "date", "split_between"]),
    "settlements.csv": (
        "SELECT id, group_name, payer, receiver, amount, date FROM settlements ORDER BY group_name, date, id",
        ["id", "group", "from", "to", "amount", "date"]),
    "investments.csv": (
        "SELECT id, name, kind, amount, value, date FROM investments ORDER BY date, id",
        ["id", "name", "type", "invested", "current_value", "date"]),
}


class ToolsMixin:
    def export_csv(self):
        folder = filedialog.askdirectory(title="Choose a folder for the CSV files")
        if not folder:
            return
        for filename, (query, header) in EXPORTS.items():
            self.cursor.execute(query)
            with open(os.path.join(folder, filename), "w", newline="", encoding="utf-8") as handle:
                writer = csv.writer(handle)
                writer.writerow(header)
                writer.writerows(self.cursor.fetchall())
        messagebox.showinfo("Export complete", f"Saved {len(EXPORTS)} CSV files to {folder}")

    def backup_db(self):
        target = filedialog.asksaveasfilename(
            title="Save backup", defaultextension=".db",
            initialfile=f"finance_backup_{datetime.now():%Y%m%d}.db",
            filetypes=[("SQLite database", "*.db")])
        if not target:
            return
        self.conn.commit()
        backup = sql.connect(target)
        self.conn.backup(backup)
        backup.close()
        messagebox.showinfo("Backup complete", "Backup saved.")
