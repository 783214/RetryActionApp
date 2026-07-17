import os
import json
import csv
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, filedialog
from datetime import datetime, date, timedelta
import db
from translations import t

# Path for persisted technicians
TECH_FILE = os.path.join(db.get_app_dir(), "technicians.json")

# Default technicians (used if technicians.json missing or invalid)
DEFAULT_TECHNICIANS = [
    "Alkei Figuracion", "Angel Islas", "Adan Mateo",
    "Daniel Hernandez", "Manuel Espinoza", "Brandon Espinoza",
    "Leilany Saldana"
]


def load_technicians():
    try:
        if os.path.exists(TECH_FILE):
            with open(TECH_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list) and data:
                return data
    except Exception:
        pass
    return list(DEFAULT_TECHNICIANS)


def save_technicians(lst):
    try:
        with open(TECH_FILE, "w", encoding="utf-8") as f:
            json.dump(lst, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


class App:
    def __init__(self, root):
        self.root = root
        self.lang = "es"
        root.title(t(self.lang, "title"))
        self.tech_list = load_technicians() 
        self.create_widgets()
        self.refresh_actions()
        self.refresh_recent()
        # ensure closing handler is set
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        frm = ttk.Frame(self.root, padding=10)
        frm.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        # Language selector
        ttk.Label(frm, text=t(self.lang, "lang_label")).grid(row=0, column=0, sticky="w")
        self.lang_var = tk.StringVar(value=self.lang)
        lang_cb = ttk.Combobox(frm, values=["es", "en"], textvariable=self.lang_var, width=5, state="readonly")
        lang_cb.grid(row=0, column=1, sticky="w")
        lang_cb.bind("<<ComboboxSelected>>", self.on_lang_change)

        # Pin
        ttk.Label(frm, text=t(self.lang, "label_pin")).grid(row=1, column=0, sticky="w", pady=(8, 0))
        self.entry_pin = ttk.Entry(frm, width=30)
        self.entry_pin.grid(row=1, column=1, columnspan=2, sticky="w", pady=(8, 0))

        # Action
        ttk.Label(frm, text=t(self.lang, "label_action")).grid(row=2, column=0, sticky="w", pady=(6, 0))
        self.action_var = tk.StringVar()
        self.action_cb = ttk.Combobox(frm, textvariable=self.action_var, state="readonly", width=28)
        self.action_cb.grid(row=2, column=1, sticky="w", pady=(6, 0))
        self.action_cb.bind("<<ComboboxSelected>>", self.on_action_select)

        # Technician
        ttk.Label(frm, text=t(self.lang, "label_technician")).grid(row=3, column=0, sticky="w", pady=(6, 0))
        self.tech_var = tk.StringVar()
        tech_values = list(self.tech_list) + [t(self.lang, "other")]
        self.tech_cb = ttk.Combobox(frm, values=tech_values, textvariable=self.tech_var, state="readonly", width=28)
        self.tech_cb.grid(row=3, column=1, sticky="w", pady=(6, 0))
        self.tech_cb.bind("<<ComboboxSelected>>", self.on_tech_select)
        if self.tech_list:
            self.tech_cb.set(self.tech_list[0])

        # Status
        ttk.Label(frm, text=t(self.lang, "label_status")).grid(row=4, column=0, sticky="w", pady=(6, 0))
        self.status_var = tk.StringVar()
        self.status_cb = ttk.Combobox(frm, values=[t(self.lang, "status_fixed"), t(self.lang, "status_monitoring")],
                                      textvariable=self.status_var, state="readonly", width=28)
        self.status_cb.grid(row=4, column=1, sticky="w", pady=(6, 0))
        self.status_cb.set(t(self.lang, "status_fixed"))

        # Comments
        ttk.Label(frm, text=t(self.lang, "label_comments")).grid(row=5, column=0, sticky="nw", pady=(6, 0))
        self.txt_comments = tk.Text(frm, width=40, height=4)
        self.txt_comments.grid(row=5, column=1, columnspan=2, sticky="w", pady=(6, 0))

        # Buttons: Update, Records, Export, Import
        btn_frame = ttk.Frame(frm)
        btn_frame.grid(row=6, column=1, sticky="w", pady=(10, 0))
        self.btn_update = ttk.Button(btn_frame, text=t(self.lang, "btn_update"), command=self.on_update)
        self.btn_update.grid(row=0, column=0, padx=(0, 8))
        self.btn_records = ttk.Button(btn_frame, text=t(self.lang, "btn_records"), command=self.open_records_window)
        self.btn_records.grid(row=0, column=1, padx=(0, 8))
        self.btn_export = ttk.Button(btn_frame, text=t(self.lang, "btn_export"), command=self.export_main_view)
        self.btn_export.grid(row=0, column=2, padx=(0, 8))
        self.btn_import = ttk.Button(btn_frame, text=t(self.lang, "btn_import"), command=self.on_import_file)
        self.btn_import.grid(row=0, column=3)

        # Recent records (Treeview)
        cols = ("id", "pin", "action", "tech", "status", "time")
        self.tree = ttk.Treeview(frm, columns=cols, show="headings", height=12)
        self.tree.grid(row=7, column=0, columnspan=3, pady=(12, 0), sticky="nsew")
        frm.rowconfigure(7, weight=1)
        self.tree.heading("id", text=t(self.lang, "col_id"))
        self.tree.heading("pin", text=t(self.lang, "col_pin"))
        self.tree.heading("action", text=t(self.lang, "col_action"))
        self.tree.heading("tech", text=t(self.lang, "col_tech"))
        self.tree.heading("status", text=t(self.lang, "col_status"))
        self.tree.heading("time", text=t(self.lang, "col_time"))
        self.tree.column("id", width=40, anchor="center")
        self.tree.column("pin", width=90, anchor="center")
        self.tree.column("action", width=220)
        self.tree.column("tech", width=160)
        self.tree.column("status", width=90, anchor="center")
        self.tree.column("time", width=160)

    def on_lang_change(self, _ev=None):
        self.lang = self.lang_var.get()
        self.root.title(t(self.lang, "title"))
        self.btn_update.config(text=t(self.lang, "btn_update"))
        self.btn_records.config(text=t(self.lang, "btn_records"))
        self.btn_export.config(text=t(self.lang, "btn_export"))
        self.btn_import.config(text=t(self.lang, "btn_import"))
        self.status_cb.config(values=[t(self.lang, "status_fixed"), t(self.lang, "status_monitoring")])
        # update combobox values for technicians with localized "Other"
        tech_values = list(self.tech_list) + [t(self.lang, "other")]
        self.tech_cb['values'] = tech_values
        # update headings
        self.tree.heading("id", text=t(self.lang, "col_id"))
        self.tree.heading("pin", text=t(self.lang, "col_pin"))
        self.tree.heading("action", text=t(self.lang, "col_action"))
        self.tree.heading("tech", text=t(self.lang, "col_tech"))
        self.tree.heading("status", text=t(self.lang, "col_status"))
        self.tree.heading("time", text=t(self.lang, "col_time"))
        self.refresh_actions()
        self.refresh_recent()

    def refresh_actions(self):
        actions = db.get_actions()
        other_label = t(self.lang, "other")
        mapped = []
        for a in actions:
            if a.lower() in ("otro", "other"):
                mapped.append(other_label)
            else:
                mapped.append(a)
        self.action_cb['values'] = mapped
        if mapped:
            self.action_cb.set(mapped[0])

    def on_action_select(self, _ev=None):
        sel = self.action_var.get()
        if sel == t(self.lang, "other"):
            self.ask_new_action()

    def ask_new_action(self):
        prompt = t(self.lang, "add_action_prompt")
        title = t(self.lang, "add_action_title")
        new = simpledialog.askstring(title, prompt, parent=self.root)
        if new:
            db.add_action(new)
            self.refresh_actions()
            self.action_cb.set(new)

    def on_tech_select(self, _ev=None):
        sel = self.tech_var.get()
        if sel == t(self.lang, "other"):
            new = simpledialog.askstring(t(self.lang, "add_action_title"), "Ingrese nombre del técnico:", parent=self.root)
            if new:
                self.tech_list.append(new)
                save_technicians(self.tech_list)
                vals = list(self.tech_list) + [t(self.lang, "other")]
                self.tech_cb['values'] = vals
                self.tech_cb.set(new)
            else:
                if self.tech_list:
                    self.tech_cb.set(self.tech_list[0])

    def on_update(self):
        pin = self.entry_pin.get().strip()
        if not pin:
            messagebox.showwarning(t(self.lang, "title"), t(self.lang, "err_pin"))
            return
        action = self.action_var.get()
        if action == t(self.lang, "other"):
            self.ask_new_action()
            action = self.action_var.get()
        technician = self.tech_var.get()
        comments = self.txt_comments.get("1.0", "end").strip()
        status = self.status_var.get()
        db.add_failure(pin, action, technician, comments, status)
        messagebox.showinfo(t(self.lang, "title"), t(self.lang, "msg_saved"))
        self.entry_pin.delete(0, "end")
        self.txt_comments.delete("1.0", "end")
        self.refresh_recent()

    def refresh_recent(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        rows = db.get_recent_after_time(limit=100, time_threshold="08:00:00", today_only=True)
        for r in rows:
            self.tree.insert("", "end", values=(r["id"], r["pin"], r["action"], r["technician"], r["status"], r["created_at"]))

    def export_main_view(self):
        rows = db.get_recent_after_time(limit=1000, time_threshold="08:00:00", today_only=True)
        self._export_rows_csv(rows, default_name="retry_actions_today.csv")

    def _export_rows_csv(self, rows, default_name="export.csv"):
        if not rows:
            messagebox.showinfo(t(self.lang, "title"), t(self.lang, "export_err"))
            return
        dest = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=default_name,
                                            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not dest:
            return
        try:
            with open(dest, "w", newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(
                    [t(self.lang, "col_id"), t(self.lang, "col_pin"), t(self.lang, "col_action"),
                     t(self.lang, "col_tech"), t(self.lang, "col_status"), t(self.lang, "col_time")])
                for r in rows:
                    writer.writerow([r["id"], r["pin"], r["action"], r["technician"], r["status"], r["created_at"]])
            messagebox.showinfo(t(self.lang, "title"), t(self.lang, "export_done"))
        except Exception as e:
            messagebox.showerror(t(self.lang, "title"), f"{t(self.lang, 'export_err')} {e}")

    def on_import_file(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not path:
            return
        try:
            rows = self._read_csv_auto(path)
        except Exception as e:
            messagebox.showerror(t(self.lang, "title"), f"{t(self.lang, 'import_err').format(err=e)}")
            return
        win = tk.Toplevel(self.root)
        win.title(f"{t(self.lang, 'btn_import')} - {os.path.basename(path)}")
        win.geometry("980x600")
        ImportRecordsWindow(win, self.lang, rows)

    def _read_csv_auto(self, path):
        with open(path, "r", encoding='utf-8') as f:
            sample = f.read(4096)
            f.seek(0)
            dialect = None
            try:
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample, delimiters=[',', ';'])
            except Exception:
                class D:
                    delimiter = ','
                dialect = D()
            reader = csv.reader(f, delimiter=dialect.delimiter)
            header = next(reader, None)
            if not header:
                raise ValueError("CSV vacío")
            hdr = [h.strip().lower() for h in header]
            mapping = {}
            for i, name in enumerate(hdr):
                if "pin" in name:
                    mapping["pin"] = i
                elif "action" in name or "accion" in name or "acción" in name:
                    mapping["action"] = i
                elif "technician" in name or "técnico" in name or "technician" in name:
                    mapping["technician"] = i
                elif "status" in name or "estado" in name:
                    mapping["status"] = i
                elif "time" in name or "hora" in name or "date" in name or "fecha" in name:
                    mapping["time"] = i
                elif "comment" in name or "coment" in name:
                    mapping["comments"] = i
            expected_keys = ["pin", "action", "technician", "status", "time", "comments"]
            for idx, key in enumerate(expected_keys):
                if key not in mapping and idx < len(hdr):
                    mapping[key] = idx
            rows = []
            for row in reader:
                if not any(cell.strip() for cell in row):
                    continue
                def getcol(k):
                    i = mapping.get(k)
                    if i is None or i >= len(row):
                        return ""
                    return row[i].strip()
                pin = getcol("pin")
                action = getcol("action")
                technician = getcol("technician")
                status = getcol("status")
                time_s = getcol("time")
                comments = getcol("comments")
                created_at = None
                if time_s:
                    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
                        try:
                            dt = datetime.strptime(time_s, fmt)
                            if fmt == "%Y-%m-%d":
                                dt = datetime.combine(dt.date(), datetime.min.time())
                            created_at = dt.strftime("%Y-%m-%d %H:%M:%S")
                            break
                        except Exception:
                            continue
                if created_at is None:
                    created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                rows.append({
                    "pin": pin,
                    "action": action,
                    "technician": technician,
                    "status": status,
                    "created_at": created_at,
                    "comments": comments
                })
            return rows

    def open_records_window(self):
        win = tk.Toplevel(self.root)
        win.title(t(self.lang, "btn_records"))
        win.geometry("900x550")
        RecordsWindow(win, self.lang)

    def on_closing(self):
        # debug line (visible in terminal)
        print("DEBUG: on_closing called")
        try:
            total = db.get_total_count()
            db_path = db.get_db_path()
        except Exception as e:
            total = "??"
            db_path = "??"
            print("DEBUG: error getting DB info:", e)

        # Simple dialog, on top, centered, auto-close after 2s
        dlg = tk.Toplevel(self.root)
        dlg.title(t(self.lang, "title"))
        frame = ttk.Frame(dlg, padding=20)
        frame.pack(fill="both", expand=True)

        ttk.Label(frame, text="Developed by Andy Herrera", font=("Segoe UI", 12, "bold")).pack(pady=(0, 6))
        ttk.Label(frame, text="Version 1.0").pack()
        ttk.Label(frame, text="Ciudad Juarez, Chih").pack(pady=(6, 6))
        ttk.Label(frame, text=f"Total registros: {total}").pack()
        ttk.Label(frame, text=f"DB: {db_path}", wraplength=400, justify="center").pack(pady=(6, 0))

        close_text = t(self.lang, "close_now")
        btn = ttk.Button(frame, text=close_text, command=lambda: self._close_app_from_dialog(dlg))
        btn.pack(pady=(12, 0))

        dlg.transient(self.root)
        dlg.lift()
        dlg.attributes("-topmost", True)
        dlg.update_idletasks()
        w = dlg.winfo_reqwidth()
        h = dlg.winfo_reqheight()
        rx = self.root.winfo_rootx()
        ry = self.root.winfo_rooty()
        rw = max(self.root.winfo_width(), 300)
        rh = max(self.root.winfo_height(), 200)
        x = rx + (rw - w) // 2
        y = ry + (rh - h) // 2
        dlg.geometry(f"{w}x{h}+{x}+{y}")

        dlg.after(2000, lambda: self._close_app_from_dialog(dlg))

    def _close_app_from_dialog(self, dlg):
        try:
            dlg.destroy()
        except Exception:
            pass
        try:
            # destroy any other Toplevels
            for w in list(self.root.winfo_children()):
                if isinstance(w, tk.Toplevel):
                    try:
                        w.destroy()
                    except Exception:
                        pass
        except Exception:
            pass
        try:
            self.root.quit()
        except Exception:
            pass
        try:
            self.root.destroy()
        except Exception:
            pass


class RecordsWindow:
    def __init__(self, root, lang):
        self.root = root
        self.lang = lang
        self.current_date = date.today()
        self.create_widgets()
        self.load_for_date(self.current_date)

    def create_widgets(self):
        frm = ttk.Frame(self.root, padding=8)
        frm.pack(fill="both", expand=True)
        top = ttk.Frame(frm)
        top.pack(fill="x", pady=(0, 8))

        self.btn_prev = ttk.Button(top, text=t(self.lang, "prev"), command=self.on_prev)
        self.btn_prev.pack(side="left", padx=(0, 6))
        self.btn_next = ttk.Button(top, text=t(self.lang, "next"), command=self.on_next)
        self.btn_next.pack(side="left", padx=(0, 6))

        ttk.Label(top, text=t(self.lang, "select_date")).pack(side="left", padx=(12, 6))
        self.day_var = tk.StringVar(value=str(self.current_date.day))
        self.month_var = tk.StringVar(value=str(self.current_date.month))
        self.year_var = tk.StringVar(value=str(self.current_date.year))

        day_cb = ttk.Combobox(top, width=3, values=[str(i) for i in range(1, 32)], textvariable=self.day_var,
                              state="readonly")
        day_cb.pack(side="left")
        month_cb = ttk.Combobox(top, width=3, values=[str(i) for i in range(1, 13)], textvariable=self.month_var,
                                state="readonly")
        month_cb.pack(side="left", padx=(4, 0))
        y = self.current_date.year
        years = [str(i) for i in range(y - 2, y + 3)]
        year_cb = ttk.Combobox(top, width=5, values=years, textvariable=self.year_var, state="readonly")
        year_cb.pack(side="left", padx=(4, 0))

        go_btn = ttk.Button(top, text="Go", command=self.on_go)
        go_btn.pack(side="left", padx=(8, 0))
        today_btn = ttk.Button(top, text=t(self.lang, "today"), command=self.on_today)
        today_btn.pack(side="left", padx=(6, 0))

        export_btn = ttk.Button(top, text=t(self.lang, "btn_export"), command=self.on_export)
        export_btn.pack(side="right")

        cols = ("id", "pin", "action", "tech", "status", "time")
        self.tree = ttk.Treeview(frm, columns=cols, show="headings", height=20)
        self.tree.pack(fill="both", expand=True)
        self.tree.heading("id", text=t(self.lang, "col_id"))
        self.tree.heading("pin", text=t(self.lang, "col_pin"))
        self.tree.heading("action", text=t(self.lang, "col_action"))
        self.tree.heading("tech", text=t(self.lang, "col_tech"))
        self.tree.heading("status", text=t(self.lang, "col_status"))
        self.tree.heading("time", text=t(self.lang, "col_time"))
        self.tree.column("id", width=50, anchor="center")
        self.tree.column("pin", width=100, anchor="center")
        self.tree.column("action", width=260)
        self.tree.column("tech", width=180)
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("time", width=180)

    def on_prev(self):
        self.current_date = self.current_date - timedelta(days=1)
        self._update_date_controls()
        self.load_for_date(self.current_date)

    def on_next(self):
        self.current_date = self.current_date + timedelta(days=1)
        self._update_date_controls()
        self.load_for_date(self.current_date)

    def on_go(self):
        try:
            d = int(self.day_var.get())
            m = int(self.month_var.get())
            y = int(self.year_var.get())
            self.current_date = date(y, m, d)
            self.load_for_date(self.current_date)
        except Exception:
            messagebox.showwarning(t(self.lang, "title"), "Fecha inválida")

    def on_today(self):
        self.current_date = date.today()
        self._update_date_controls()
        self.load_for_date(self.current_date)

    def _update_date_controls(self):
        self.day_var.set(str(self.current_date.day))
        self.month_var.set(str(self.current_date.month))
        self.year_var.set(str(self.current_date.year))

    def load_for_date(self, date_obj):
        for i in self.tree.get_children():
            self.tree.delete(i)
        ds = date_obj.isoformat()  # YYYY-MM-DD
        rows = db.get_by_date(ds)
        for r in rows:
            self.tree.insert("", "end", values=(r["id"], r["pin"], r["action"], r["technician"], r["status"],
                                                r["created_at"]))
        self._update_date_controls()

    def on_export(self):
        ds = self.current_date.isoformat()
        rows = db.get_by_date(ds)
        default = f"retry_actions_{ds}.csv"
        if not rows:
            messagebox.showinfo(t(self.lang, "title"), t(self.lang, "export_err"))
            return
        dest = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=default,
                                            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not dest:
            return
        try:
            with open(dest, "w", newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow([t(self.lang, "col_id"), t(self.lang, "col_pin"), t(self.lang, "col_action"),
                                 t(self.lang, "col_tech"), t(self.lang, "col_status"), t(self.lang, "col_time")])
                for r in rows:
                    writer.writerow([r["id"], r["pin"], r["action"], r["technician"], r["status"], r["created_at"]])
            messagebox.showinfo(t(self.lang, "title"), t(self.lang, "export_done"))
        except Exception as e:
            messagebox.showerror(t(self.lang, "title"), f"{t(self.lang, 'export_err')} {e}")


class ImportRecordsWindow:
    """
    Similar to RecordsWindow but backed by an in-memory list of rows
    provided from a CSV file. Allows preview by date and import into DB.
    """
    def __init__(self, root, lang, rows):
        self.root = root
        self.lang = lang
        # rows: list of dicts with keys pin, action, technician, status, created_at, comments
        self.rows_all = rows
        self.dates = sorted({r["created_at"][:10] for r in self.rows_all}, reverse=True)
        self.current_date = date.today()
        self.create_widgets()
        if self.current_date.isoformat() in self.dates:
            self.load_for_date(self.current_date)
        elif self.dates:
            y, m, d = map(int, self.dates[0].split("-"))
            self.current_date = date(y, m, d)
            self._update_date_controls()
            self.load_for_date(self.current_date)
        else:
            self.load_for_date(self.current_date)

    def create_widgets(self):
        frm = ttk.Frame(self.root, padding=8)
        frm.pack(fill="both", expand=True)
        top = ttk.Frame(frm)
        top.pack(fill="x", pady=(0, 8))

        self.btn_prev = ttk.Button(top, text=t(self.lang, "prev"), command=self.on_prev)
        self.btn_prev.pack(side="left", padx=(0, 6))
        self.btn_next = ttk.Button(top, text=t(self.lang, "next"), command=self.on_next)
        self.btn_next.pack(side="left", padx=(0, 6))

        ttk.Label(top, text=t(self.lang, "select_date")).pack(side="left", padx=(12, 6))

        self.day_var = tk.StringVar(value=str(self.current_date.day))
        self.month_var = tk.StringVar(value=str(self.current_date.month))
        self.year_var = tk.StringVar(value=str(self.current_date.year))

        day_cb = ttk.Combobox(top, width=3, values=[str(i) for i in range(1, 32)], textvariable=self.day_var,
                              state="readonly")
        day_cb.pack(side="left")
        month_cb = ttk.Combobox(top, width=3, values=[str(i) for i in range(1, 13)], textvariable=self.month_var,
                                state="readonly")
        month_cb.pack(side="left", padx=(4, 0))
        y = self.current_date.year
        years = [str(i) for i in range(y - 5, y + 6)]
        year_cb = ttk.Combobox(top, width=5, values=years, textvariable=self.year_var, state="readonly")
        year_cb.pack(side="left", padx=(4, 0))

        go_btn = ttk.Button(top, text="Go", command=self.on_go)
        go_btn.pack(side="left", padx=(8, 0))
        today_btn = ttk.Button(top, text=t(self.lang, "today"), command=self.on_today)
        today_btn.pack(side="left", padx=(6, 0))

        import_btn = ttk.Button(top, text=t(self.lang, "btn_import"), command=self.on_import_to_db)
        import_btn.pack(side="right", padx=(6, 0))

        export_btn = ttk.Button(top, text=t(self.lang, "btn_export"), command=self.on_export)
        export_btn.pack(side="right")

        cols = ("pin", "action", "tech", "status", "time", "comments")
        self.tree = ttk.Treeview(frm, columns=cols, show="headings", height=20)
        self.tree.pack(fill="both", expand=True)
        self.tree.heading("pin", text=t(self.lang, "col_pin"))
        self.tree.heading("action", text=t(self.lang, "col_action"))
        self.tree.heading("tech", text=t(self.lang, "col_tech"))
        self.tree.heading("status", text=t(self.lang, "col_status"))
        self.tree.heading("time", text=t(self.lang, "col_time"))
        self.tree.heading("comments", text=t(self.lang, "label_comments"))
        self.tree.column("pin", width=100, anchor="center")
        self.tree.column("action", width=260)
        self.tree.column("tech", width=180)
        self.tree.column("status", width=100, anchor="center")
        self.tree.column("time", width=180)
        self.tree.column("comments", width=260)

    def on_prev(self):
        self.current_date = self.current_date - timedelta(days=1)
        self._update_date_controls()
        self.load_for_date(self.current_date)

    def on_next(self):
        self.current_date = self.current_date + timedelta(days=1)
        self._update_date_controls()
        self.load_for_date(self.current_date)

    def on_go(self):
        try:
            d = int(self.day_var.get())
            m = int(self.month_var.get())
            y = int(self.year_var.get())
            self.current_date = date(y, m, d)
            self.load_for_date(self.current_date)
        except Exception:
            messagebox.showwarning(t(self.lang, "title"), "Fecha inválida")

    def on_today(self):
        self.current_date = date.today()
        self._update_date_controls()
        self.load_for_date(self.current_date)

    def _update_date_controls(self):
        self.day_var.set(str(self.current_date.day))
        self.month_var.set(str(self.current_date.month))
        self.year_var.set(str(self.current_date.year))

    def load_for_date(self, date_obj):
        for i in self.tree.get_children():
            self.tree.delete(i)
        ds = date_obj.isoformat()
        day_rows = [r for r in self.rows_all if r["created_at"][:10] == ds]
        for r in day_rows:
            self.tree.insert("", "end", values=(r["pin"], r["action"], r["technician"], r["status"], r["created_at"], r["comments"]))

    def on_export(self):
        ds = self.current_date.isoformat()
        day_rows = [r for r in self.rows_all if r["created_at"][:10] == ds]
        default = f"import_preview_{ds}.csv"
        if not day_rows:
            messagebox.showinfo(t(self.lang, "title"), t(self.lang, "export_err"))
            return
        dest = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=default,
                                            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")])
        if not dest:
            return
        try:
            with open(dest, "w", newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Pin", "Action", "Technician", "Status", "Time", "Comments"])
                for r in day_rows:
                    writer.writerow([r["pin"], r["action"], r["technician"], r["status"], r["created_at"], r["comments"]])
            messagebox.showinfo(t(self.lang, "title"), t(self.lang, "export_done"))
        except Exception as e:
            messagebox.showerror(t(self.lang, "title"), f"{t(self.lang, 'export_err')} {e}")

    def on_import_to_db(self):
        ds = self.current_date.isoformat()
        day_rows = [r for r in self.rows_all if r["created_at"][:10] == ds]
        if not day_rows:
            messagebox.showinfo(t(self.lang, "title"), t(self.lang, "export_err"))
            return
        inserted = 0
        skipped = 0
        for r in day_rows:
            try:
                ok = db.add_failure_with_time(r["pin"], r["action"], r["technician"], r["comments"], r["status"], r["created_at"])
                if ok:
                    inserted += 1
                else:
                    skipped += 1
            except Exception:
                skipped += 1
        messagebox.showinfo(t(self.lang, "title"), t(self.lang, "import_ok").format(ins=inserted, skp=skipped))


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.geometry("980x600")
    root.mainloop()
