import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import json
import re
from pathlib import Path

APP_TITLE = "Hex / Text Encoder & Decoder"

class HexTool:
    def __init__(self, root):
        self.root = root
        root.title(APP_TITLE)
        root.geometry("1100x720")
        root.minsize(820, 560)

        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        top = ttk.Frame(root, padding=10)
        top.pack(fill="x")
        ttk.Label(top, text=APP_TITLE, font=("Segoe UI", 17, "bold")).pack(side="left")
        ttk.Label(top, text="HEX ⇄ Text / JSON", foreground="#477").pack(side="right")

        controls = ttk.Frame(root, padding=(10, 0, 10, 8))
        controls.pack(fill="x")
        ttk.Button(controls, text="Decode HEX → Text", command=self.decode).pack(side="left", padx=(0, 6))
        ttk.Button(controls, text="Encode Text → HEX", command=self.encode).pack(side="left", padx=6)
        ttk.Button(controls, text="Auto Detect", command=self.auto_process).pack(side="left", padx=6)
        ttk.Button(controls, text="Format JSON", command=self.format_json).pack(side="left", padx=6)
        ttk.Button(controls, text="Tukar", command=self.swap).pack(side="left", padx=6)
        ttk.Button(controls, text="Bersihkan", command=self.clear).pack(side="right")

        panes = ttk.Panedwindow(root, orient="horizontal")
        panes.pack(fill="both", expand=True, padx=10, pady=4)

        left = ttk.Frame(panes, padding=5)
        right = ttk.Frame(panes, padding=5)
        panes.add(left, weight=1)
        panes.add(right, weight=1)

        ttk.Label(left, text="INPUT", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.input_text = self.make_text(left)
        self.input_text.pack(fill="both", expand=True, pady=(5, 0))

        ttk.Label(right, text="OUTPUT", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        self.output_text = self.make_text(right)
        self.output_text.pack(fill="both", expand=True, pady=(5, 0))

        filebar = ttk.Frame(root, padding=10)
        filebar.pack(fill="x")
        ttk.Button(filebar, text="Buka File", command=self.open_file).pack(side="left", padx=(0, 6))
        ttk.Button(filebar, text="Buka .DAT → JSON", command=self.open_dat_convert).pack(side="left", padx=6)
        ttk.Button(filebar, text="Encode JSON → DAT", command=self.encode_json_to_dat).pack(side="left", padx=6)
        ttk.Button(filebar, text="Simpan Output", command=self.save_output).pack(side="left", padx=6)
        ttk.Button(filebar, text="Simpan .DAT", command=self.save_dat).pack(side="left", padx=6)
        ttk.Button(filebar, text="Simpan .JSON", command=self.save_json).pack(side="left", padx=6)
        ttk.Button(filebar, text="Salin Output", command=self.copy_output).pack(side="left", padx=6)
        self.status = tk.StringVar(value="Siap.")
        ttk.Label(filebar, textvariable=self.status).pack(side="right")

    def make_text(self, parent):
        frame = ttk.Frame(parent)
        text = tk.Text(frame, wrap="none", undo=True, font=("Consolas", 10))
        y = ttk.Scrollbar(frame, orient="vertical", command=text.yview)
        x = ttk.Scrollbar(frame, orient="horizontal", command=text.xview)
        text.configure(yscrollcommand=y.set, xscrollcommand=x.set)
        text.grid(row=0, column=0, sticky="nsew")
        y.grid(row=0, column=1, sticky="ns")
        x.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        # Return the frame while retaining its text widget.
        frame.text_widget = text
        return frame

    def get_input(self):
        return self.input_text.text_widget.get("1.0", "end-1c")

    def set_output(self, value):
        widget = self.output_text.text_widget
        widget.delete("1.0", "end")
        widget.insert("1.0", value)

    @staticmethod
    def decode_line(line):
        # Remove whitespace between hex bytes, but preserve decoded content.
        compact = re.sub(r"\s+", "", line)
        if not compact:
            return ""
        if len(compact) % 2:
            raise ValueError("Jumlah digit HEX ganjil.")
        if not re.fullmatch(r"[0-9a-fA-F]+", compact):
            raise ValueError("Input mengandung karakter non-HEX.")
        return bytes.fromhex(compact).decode("utf-8", errors="replace")

    def decode(self):
        source = self.get_input()
        lines = source.splitlines()
        output, ok, failed = [], 0, 0
        for number, line in enumerate(lines, 1):
            if not line.strip():
                output.append("")
                continue
            try:
                output.append(self.decode_line(line))
                ok += 1
            except Exception as exc:
                output.append(f"[ERROR baris {number}: {exc}]\n{line}")
                failed += 1
        self.set_output("\n".join(output))
        self.status.set(f"Decode: {ok} berhasil, {failed} gagal.")

    def encode(self):
        source = self.get_input()
        # Encode each input line separately to retain one-record-per-line format.
        lines = source.splitlines()
        result = [line.encode("utf-8").hex() for line in lines]
        self.set_output("\n".join(result))
        self.status.set(f"Encode: {len(result)} baris diproses.")

    def auto_process(self):
        source = self.get_input().strip()
        if not source:
            self.status.set("Input kosong.")
            return
        lines = [line.strip() for line in source.splitlines() if line.strip()]
        looks_hex = bool(lines) and all(
            re.fullmatch(r"(?:[0-9a-fA-F]{2}\s*)+", line) for line in lines
        )
        if looks_hex:
            self.decode()
        else:
            self.encode()

    @staticmethod
    def clean_record_prefix(line):
        """Buang prefix record seperti '0 0 0 0 ' sebelum objek JSON."""
        return re.sub(r"^\s*\d+(?:\s+\d+){3}\s+(?=[{\[])", "", line, count=1)

    @classmethod
    def parse_dat_records(cls, content):
        records = []
        errors = []
        for number, raw_line in enumerate(content.splitlines(), 1):
            line = raw_line.strip()
            if not line:
                continue

            # DAT bisa berisi hasil decode atau baris HEX mentah.
            cleaned = cls.clean_record_prefix(line)
            if re.fullmatch(r"[0-9a-fA-F\s]+", cleaned) and len(re.sub(r"\s+", "", cleaned)) % 2 == 0:
                try:
                    decoded = bytes.fromhex(re.sub(r"\s+", "", cleaned)).decode("utf-8")
                    cleaned = cls.clean_record_prefix(decoded.strip())
                except Exception:
                    pass

            try:
                value = json.loads(cleaned)
                if isinstance(value, list):
                    records.extend(value)
                else:
                    records.append(value)
            except json.JSONDecodeError as exc:
                errors.append(f"Baris {number}: {exc.msg}")
        return records, errors

    def format_json(self):
        source = self.get_input()
        records, errors = self.parse_dat_records(source)
        if not records:
            messagebox.showerror(
                "JSON tidak ditemukan",
                "\n".join(errors[:8]) if errors else "Tidak ditemukan objek JSON yang valid."
            )
            self.status.set("Tidak ada JSON valid.")
            return

        payload = records[0] if len(records) == 1 else records
        self.set_output(json.dumps(payload, indent=4, ensure_ascii=False))
        self.status.set(
            f"JSON bersih: {len(records)} record; prefix 0000 dihapus"
            + (f"; {len(errors)} baris dilewati" if errors else "")
        )

    def encode_json_to_dat(self):
        """Encode JSON menjadi format DAT: prefix empat angka + JSON satu baris + HEX."""
        source = self.get_input().strip()
        if not source:
            messagebox.showwarning("Input kosong", "Masukkan atau buka file JSON terlebih dahulu.")
            return

        try:
            parsed = json.loads(source)
        except json.JSONDecodeError as exc:
            messagebox.showerror("JSON tidak valid", f"JSON gagal dibaca:\n{exc}")
            return

        # Terima satu objek atau array berisi banyak objek.
        records = parsed if isinstance(parsed, list) else [parsed]
        if not records:
            messagebox.showwarning("JSON kosong", "Array JSON tidak berisi record.")
            return

        dat_lines = []
        for item in records:
            compact_json = json.dumps(item, ensure_ascii=False, separators=(",", ":"))
            dat_text = "0 0 0 0 " + compact_json
            dat_lines.append(dat_text.encode("utf-8").hex())

        result = "\n".join(dat_lines)
        self.set_output(result)
        self.status.set(f"Encode JSON → DAT: {len(dat_lines)} record berhasil.")

        save_path = filedialog.asksaveasfilename(
            title="Simpan hasil encode sebagai DAT",
            defaultextension=".dat",
            initialfile="encoded.dat",
            filetypes=[("DAT", "*.dat"), ("File teks", "*.txt"), ("Semua file", "*.*")]
        )
        if save_path:
            try:
                Path(save_path).write_text(result + "\n", encoding="utf-8")
                self.status.set(f"{len(dat_lines)} record berhasil disimpan ke {Path(save_path).name}")
            except Exception as exc:
                messagebox.showerror("Gagal menyimpan DAT", str(exc))

    def open_dat_convert(self):
        path = filedialog.askopenfilename(
            title="Buka file DAT untuk dikonversi ke JSON",
            filetypes=[("File DAT", "*.dat"), ("Semua file", "*.*")]
        )
        if not path:
            return
        try:
            content = Path(path).read_text(encoding="utf-8", errors="replace")
            records, errors = self.parse_dat_records(content)
            if not records:
                messagebox.showerror(
                    "Konversi gagal",
                    "\n".join(errors[:10]) if errors else "Tidak ditemukan data JSON di file DAT."
                )
                self.status.set("DAT tidak berisi JSON yang dikenali.")
                return

            payload = records[0] if len(records) == 1 else records
            pretty = json.dumps(payload, indent=4, ensure_ascii=False)
            self.input_text.text_widget.delete("1.0", "end")
            self.input_text.text_widget.insert("1.0", content)
            self.set_output(pretty)
            self.status.set(
                f"{Path(path).name}: {len(records)} record dikonversi; prefix 0000 dibersihkan"
                + (f"; {len(errors)} baris dilewati" if errors else "")
            )

            # Tawarkan penyimpanan langsung sebagai file .json.
            save_path = filedialog.asksaveasfilename(
                title="Simpan hasil konversi JSON",
                defaultextension=".json",
                initialfile=Path(path).stem + ".json",
                filetypes=[("JSON", "*.json"), ("Semua file", "*.*")]
            )
            if save_path:
                Path(save_path).write_text(pretty + "\n", encoding="utf-8")
                self.status.set(f"Berhasil: {len(records)} record → {Path(save_path).name}")
            if errors:
                messagebox.showwarning(
                    "Sebagian baris dilewati",
                    f"{len(records)} record berhasil dikonversi.\n"
                    f"{len(errors)} baris tidak valid dilewati."
                )
        except Exception as exc:
            messagebox.showerror("Gagal membuka DAT", str(exc))

    def swap(self):
        a = self.get_input()
        b = self.output_text.text_widget.get("1.0", "end-1c")
        self.input_text.text_widget.delete("1.0", "end")
        self.input_text.text_widget.insert("1.0", b)
        self.set_output(a)
        self.status.set("Input dan output ditukar.")

    def clear(self):
        self.input_text.text_widget.delete("1.0", "end")
        self.output_text.text_widget.delete("1.0", "end")
        self.status.set("Dibersihkan.")

    def open_file(self):
        path = filedialog.askopenfilename(
            title="Pilih file teks",
            filetypes=[("File teks", "*.txt *.hex *.json"), ("Semua file", "*.*")]
        )
        if not path:
            return
        try:
            content = Path(path).read_text(encoding="utf-8", errors="replace")
            self.input_text.text_widget.delete("1.0", "end")
            self.input_text.text_widget.insert("1.0", content)
            self.status.set(f"Dibuka: {Path(path).name}")
        except Exception as exc:
            messagebox.showerror("Gagal membuka file", str(exc))

    def save_output(self):
        content = self.output_text.text_widget.get("1.0", "end-1c")
        if not content:
            messagebox.showwarning("Output kosong", "Tidak ada hasil untuk disimpan.")
            return
        path = filedialog.asksaveasfilename(
            title="Simpan hasil",
            defaultextension=".txt",
            filetypes=[("File teks", "*.txt"), ("File JSON", "*.json"), ("Semua file", "*.*")]
        )
        if not path:
            return
        try:
            Path(path).write_text(content, encoding="utf-8")
            self.status.set(f"Tersimpan: {Path(path).name}")
        except Exception as exc:
            messagebox.showerror("Gagal menyimpan file", str(exc))

    def save_dat(self):
        """Simpan hasil decode sebagai teks .dat tanpa mengubah isinya."""
        content = self.output_text.text_widget.get("1.0", "end-1c")
        if not content.strip():
            messagebox.showwarning("Output kosong", "Decode HEX terlebih dahulu.")
            return
        path = filedialog.asksaveasfilename(
            title="Simpan hasil decode sebagai DAT",
            defaultextension=".dat",
            initialfile="decoded.dat",
            filetypes=[("DAT", "*.dat"), ("File teks", "*.txt"), ("Semua file", "*.*")]
        )
        if not path:
            return
        try:
            Path(path).write_text(content.rstrip() + "\n", encoding="utf-8")
            self.status.set(f"File DAT tersimpan: {Path(path).name}")
        except Exception as exc:
            messagebox.showerror("Gagal menyimpan DAT", str(exc))

    def save_json(self):
        """Simpan hasil sebagai JSON bersih tanpa prefix angka record."""
        content = self.output_text.text_widget.get("1.0", "end-1c")
        if not content.strip():
            content = self.get_input()
        records, errors = self.parse_dat_records(content)
        if not records:
            messagebox.showerror(
                "JSON tidak ditemukan",
                "\n".join(errors[:8]) if errors else "Tidak ditemukan objek JSON."
            )
            return

        payload = records[0] if len(records) == 1 else records
        path = filedialog.asksaveasfilename(
            title="Simpan hasil decode sebagai JSON",
            defaultextension=".json",
            initialfile="decoded.json",
            filetypes=[("JSON", "*.json"), ("Semua file", "*.*")]
        )
        if not path:
            return
        try:
            Path(path).write_text(
                json.dumps(payload, indent=4, ensure_ascii=False) + "\n",
                encoding="utf-8"
            )
            self.status.set(
                f"JSON tersimpan: {Path(path).name} ({len(records)} record; prefix dibersihkan)"
            )
            if errors:
                messagebox.showwarning(
                    "Sebagian baris dilewati",
                    f"{len(records)} record berhasil disimpan.\n"
                    f"{len(errors)} baris tidak valid dilewati."
                )
        except Exception as exc:
            messagebox.showerror("Gagal menyimpan JSON", str(exc))

    def copy_output(self):
        content = self.output_text.text_widget.get("1.0", "end-1c")
        self.root.clipboard_clear()
        self.root.clipboard_append(content)
        self.status.set("Output disalin ke clipboard.")

if __name__ == "__main__":
    root = tk.Tk()
    app = HexTool(root)
    root.mainloop()
