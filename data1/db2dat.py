
import sqlite3
import json
from pathlib import Path

# Folder tempat script berada
WORK_DIR = Path(__file__).resolve().parent

DB_FILE = WORK_DIR / "psiphon.db"
JSON_FILE = WORK_DIR / "server_list.json"

output_data = ""


def extract_server_list():
    global output_data

    try:
        with sqlite3.connect(DB_FILE) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                SELECT value_text
                FROM records
                WHERE bucket_id = 8
            """)

            rows = cursor.fetchall()

        if not rows:
            print("\nTidak ada data pada bucket_id 8.")
            return False

        data = [json.loads(row[0]) for row in rows]

        JSON_FILE.write_text(
            json.dumps(data, indent=4, ensure_ascii=False),
            encoding="utf-8"
        )

        print(f"\nDatabase : {DB_FILE.name}")
        print(f"JSON     : {JSON_FILE.name}")
        print(f"Records  : {len(data)}")

        return True

    except (sqlite3.Error, json.JSONDecodeError, OSError) as exc:
        print(f"\nGagal mengambil data: {exc}")
        return False


def encode_json_to_dat():
    global output_data

    print("\nPilih file JSON untuk diencode menjadi DAT.")
    print("Masukkan path file, atau tekan Enter untuk memakai server_list.json.")

    json_path = input("File JSON [server_list.json]: ").strip()

    if not json_path:
        json_file = JSON_FILE
    else:
        json_file = Path(json_path)

        if not json_file.is_absolute():
            json_file = WORK_DIR / json_file

    try:
        source = json_file.read_text(encoding="utf-8")
    except FileNotFoundError:
        print(f"\nFile tidak ditemukan: {json_file}")
        return
    except OSError as exc:
        print(f"\nGagal membaca file: {exc}")
        return

    try:
        parsed = json.loads(source)
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
            item,
            ensure_ascii=False,
            separators=(",", ":")
        )

        dat_text = "0 0 0 0 " + compact_json
        dat_lines.append(dat_text.encode("utf-8").hex())

    output_data = "\n".join(dat_lines)

    print(f"\nFile JSON : {json_file.name}")
    print(f"Encode berhasil: {len(dat_lines)} record.")

    if input("\nSimpan sebagai DAT? (y/n): ").strip().lower() == "y":
        save_dat()


def save_dat():
    global output_data

    output_path = input("Nama file DAT [server_list.dat]: ").strip()

    if not output_path:
        output_path = "server_list.dat"

    dat_file = Path(output_path)

    if not dat_file.is_absolute():
        dat_file = WORK_DIR / dat_file

    try:
        dat_file.write_text(output_data, encoding="utf-8")
        print(f"\nBerhasil disimpan: {dat_file}")

    except OSError as exc:
        print(f"\nGagal menyimpan DAT: {exc}")


def main():
    print("=== Psiphon Database Converter ===")
    print("1. Extract DB dan Encode DAT")
    print("2. Extract DB ke JSON saja")
    print("3. Encode JSON ke DAT")

    choice = input("\nPilih menu: ").strip()

    if choice == "1":
        if extract_server_list():
            encode_json_to_dat()

    elif choice == "2":
        extract_server_list()

    elif choice == "3":
        encode_json_to_dat()

    else:
        print("\nPilihan tidak valid.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"\nTerjadi kesalahan: {exc}")

    input("\nTekan Enter untuk keluar...")
