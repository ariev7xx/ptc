import json
import os
import re
import subprocess
from pathlib import Path

# Gunakan folder tempat edit.py berada sebagai folder kerja.
BASE_DIR = Path(__file__).resolve().parent
os.chdir(BASE_DIR)

APP_TITLE = "HEX / TEXT ENCODER & DECODER"
input_data = ""
output_data = ""


def pause():
    input("\nTekan Enter untuk melanjutkan...")


def clear_terminal():
    """Bersihkan layar terminal pada Android/Termux, Linux, dan Windows."""
    os.system("cls" if os.name == "nt" else "clear")


def menu():
    print("\n" + "=" * 46)
    print(f"       {APP_TITLE}")
    print("=" * 46)
    print("[1]  Decode HEX -> Text")
    print("[2]  Encode Text -> HEX")
    print("[3]  Auto Detect")
    print("[4]  Format JSON")
    print("[5]  Buka DAT -> JSON")
    print("[6]  Encode JSON -> DAT")
    print("[7]  Buka File")
    print("[8]  Simpan Output")
    print("[9]  Simpan DAT")
    print("[10] Simpan JSON")
    print("[11] Tukar Input / Output")
    print("[12] Bersihkan")
    print("[13] Masukkan Input Manual")
    print("[14] Lihat Input")
    print("[15] Lihat Output")
    print("[16] Salin Output")
    print("[0]  Keluar")
    print("=" * 46)


def get_multiline():
    print("\nTempel atau ketik teks.")
    print("Ketik satu titik (.) pada baris baru untuk selesai:")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line == ".":
            break
        lines.append(line)
    return "\n".join(lines)


def decode_line(line):
    compact = re.sub(r"\s+", "", line)
    if not compact:
        return ""
    if len(compact) % 2:
        raise ValueError("Jumlah digit HEX ganjil.")
    if not re.fullmatch(r"[0-9a-fA-F]+", compact):
        raise ValueError("Input mengandung karakter non-HEX.")
    return bytes.fromhex(compact).decode("utf-8", errors="replace")


def decode():
    global output_data
    if not input_data:
        print("\nInput kosong.")
        return
    result = []
    ok = failed = 0
    for number, line in enumerate(input_data.splitlines(), 1):
        if not line.strip():
            result.append("")
            continue
        try:
            result.append(decode_line(line))
            ok += 1
        except ValueError as exc:
            result.append(f"[ERROR baris {number}: {exc}]\n{line}")
            failed += 1
    output_data = "\n".join(result)
    print(f"\nDecode: {ok} berhasil, {failed} gagal.")


def encode():
    global output_data
    if not input_data:
        print("\nInput kosong.")
        return
    lines = input_data.splitlines()
    output_data = "\n".join(line.encode("utf-8").hex() for line in lines)
    print(f"\nEncode: {len(lines)} baris diproses.")


def auto_process():
    source_lines = [line.strip() for line in input_data.splitlines() if line.strip()]
    if not source_lines:
        print("\nInput kosong.")
        return
    is_hex = all(
        re.fullmatch(r"(?:[0-9a-fA-F]{2}\s*)+", line) is not None
        for line in source_lines
    )
    if is_hex:
        print("\nFormat terdeteksi: HEX")
        decode()
    else:
        print("\nFormat terdeteksi: TEXT")
        encode()


def parse_dat_records(content):
    """
    Decode DAT Psiphon mengikuti extractor asli:
    HEX seluruh file -> UTF-8 -> ekstrak objek dengan raw_decode.
    Input JSON/text biasa juga tetap didukung oleh menu Format JSON.
    """
    records = []
    errors = []

    try:
        source = content.strip()
        if not source:
            return records, ["File kosong."]

        compact_hex = re.sub(r"\s+", "", source)

        if compact_hex and re.fullmatch(r"[0-9a-fA-F]+", compact_hex):
            if len(compact_hex) % 2:
                return records, ["Jumlah digit HEX ganjil."]
            text = bytes.fromhex(compact_hex).decode("utf-8")
        else:
            text = source

        decoder = json.JSONDecoder()
        position = 0

        while position < len(text):
            start = text.find("{", position)
            if start == -1:
                break
            try:
                obj, end = decoder.raw_decode(text, start)
                if isinstance(obj, dict):
                    records.append(obj)
                position = end
            except json.JSONDecodeError:
                position = start + 1

        if not records:
            errors.append("Tidak ditemukan objek JSON dalam file.")

    except UnicodeDecodeError as exc:
        errors.append(f"Data hasil decode bukan UTF-8 valid: {exc}")
    except ValueError as exc:
        errors.append(f"Gagal decode HEX: {exc}")

    return records, errors


def format_json():
    global output_data
    records, errors = parse_dat_records(input_data)
    if not records:
        print("\nJSON tidak ditemukan.")
        for error in errors[:8]:
            print(error)
        return
    payload = records[0] if len(records) == 1 else records
    output_data = json.dumps(payload, indent=4, ensure_ascii=False)
    print(f"\nJSON berhasil diformat: {len(records)} record.")
    if errors:
        print(f"{len(errors)} baris dilewati.")


def encode_json_to_dat():
    global output_data
    if not input_data.strip():
        print("\nInput kosong.")
        return
    try:
        parsed = json.loads(input_data)
    except json.JSONDecodeError as exc:
        print(f"\nJSON tidak valid: {exc}")
        return

    records = parsed if isinstance(parsed, list) else [parsed]
    if not records:
        print("\nArray JSON kosong.")
        return

    dat_lines = []
    for item in records:
        compact_json = json.dumps(
            item, ensure_ascii=False, separators=(",", ":")
        )
        dat_text = "0 0 0 0 " + compact_json
        dat_lines.append(dat_text.encode("utf-8").hex())

    output_data = "\n".join(dat_lines)
    print(f"\nEncode berhasil: {len(dat_lines)} record.")
    if input("\nSimpan sebagai DAT? (y/n): ").strip().lower() == "y":
        save_dat()


def open_file():
    global input_data
    path = input("\nMasukkan lokasi file: ").strip()
    if not path:
        return
    try:
        input_data = Path(path).read_text(encoding="utf-8", errors="replace")
        print(f"\nBerhasil membuka: {Path(path).name}")
        print(f"Ukuran: {len(input_data)} karakter.")
    except OSError as exc:
        print(f"\nGagal membuka file: {exc}")


def open_dat_convert():
    global input_data, output_data
    path = input("\nMasukkan lokasi file DAT: ").strip()
    if not path:
        return
    try:
        content = Path(path).read_text(encoding="utf-8", errors="replace")
        records, errors = parse_dat_records(content)
        if not records:
            print("\nKonversi gagal. JSON tidak ditemukan.")
            for error in errors[:10]:
                print(error)
            return

        input_data = content
        payload = records[0] if len(records) == 1 else records
        output_data = json.dumps(payload, indent=4, ensure_ascii=False)

        print(f"\nFile: {Path(path).name}")
        print(f"Berhasil dikonversi: {len(records)} record.")
        if errors:
            print(f"Baris dilewati: {len(errors)}")

        if input("\nSimpan hasil sebagai JSON? (y/n): ").strip().lower() == "y":
            save_json()
    except OSError as exc:
        print(f"\nGagal membuka DAT: {exc}")


def save_output():
    if not output_data:
        print("\nOutput kosong.")
        return
    path = input("\nNama/lokasi file output: ").strip()
    if not path:
        return
    try:
        Path(path).write_text(output_data, encoding="utf-8")
        print(f"\nBerhasil disimpan: {path}")
    except OSError as exc:
        print(f"\nGagal menyimpan: {exc}")


def save_dat():
    if not output_data.strip():
        print("\nOutput kosong.")
        return
    path = input("\nNama file DAT [server_list.dat]: ").strip() or "server_list.dat"
    try:
        Path(path).write_text(output_data.rstrip() + "\n", encoding="utf-8")
        print(f"\nDAT berhasil disimpan: {path}")
    except OSError as exc:
        print(f"\nGagal menyimpan DAT: {exc}")


def save_json():
    if not output_data.strip():
        print("\nOutput kosong.")
        return

    records, errors = parse_dat_records(output_data)
    if not records:
        try:
            parsed = json.loads(output_data)
            records = parsed if isinstance(parsed, list) else [parsed]
        except json.JSONDecodeError:
            print("\nJSON tidak ditemukan.")
            return

    payload = records[0] if len(records) == 1 else records
    path = input("\nNama file JSON [psiphon_servers.json]: ").strip() or "psiphon_servers.json"
    try:
        Path(path).write_text(
            json.dumps(payload, indent=4, ensure_ascii=False) + "\n",
            encoding="utf-8"
        )
        print(f"\nJSON berhasil disimpan: {path}")
        print(f"Jumlah record: {len(records)}")
        if errors:
            print(f"{len(errors)} baris dilewati.")
    except OSError as exc:
        print(f"\nGagal menyimpan JSON: {exc}")


def swap():
    global input_data, output_data
    input_data, output_data = output_data, input_data
    print("\nInput dan output ditukar.")


def clear():
    global input_data, output_data
    input_data = ""
    output_data = ""
    print("\nInput dan output dibersihkan.")


def show_input():
    print("\n" + "=" * 46)
    print("INPUT")
    print("=" * 46)
    print(input_data if input_data else "(Kosong)")


def show_output():
    print("\n" + "=" * 46)
    print("OUTPUT")
    print("=" * 46)
    print(output_data if output_data else "(Kosong)")


def copy_output():
    if not output_data:
        print("\nOutput kosong.")
        return
    try:
        subprocess.run(
            ["termux-clipboard-set"],
            input=output_data,
            text=True,
            check=True
        )
        print("\nOutput berhasil disalin ke clipboard.")
    except FileNotFoundError:
        print("\ntermux-clipboard-set tidak ditemukan.")
        print("Install paket termux-api dan aplikasi Termux:API.")
    except subprocess.CalledProcessError as exc:
        print(f"\nGagal menyalin output: {exc}")


def main():
    global input_data
    actions = {
        "1": decode,
        "2": encode,
        "3": auto_process,
        "4": format_json,
        "5": open_dat_convert,
        "6": encode_json_to_dat,
        "7": open_file,
        "8": save_output,
        "9": save_dat,
        "10": save_json,
        "11": swap,
        "12": clear,
        "14": show_input,
        "15": show_output,
        "16": copy_output,
    }

    while True:
        clear_terminal()
        menu()
        try:
            choice = input("Pilih menu: ").strip()
            if choice == "0":
                print("\nKeluar.")
                break
            elif choice == "13":
                input_data = get_multiline()
                print(f"\nInput diterima: {len(input_data)} karakter.")
            elif choice in actions:
                actions[choice]()
            else:
                print("\nPilihan tidak valid.")
            pause()
        except KeyboardInterrupt:
            print("\n\nDibatalkan.")
            try:
                pause()
            except (KeyboardInterrupt, EOFError):
                print()
                break
        except EOFError:
            print("\nInput berakhir. Keluar.")
            break


if __name__ == "__main__":
    main()
