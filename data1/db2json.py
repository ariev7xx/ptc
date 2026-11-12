
import sqlite3
import json
from pathlib import Path

WORK_DIR = Path(__file__).resolve().parent
WORK_DIR.mkdir(parents=True, exist_ok=True)

DB_FILE = WORK_DIR / "psiphon.db"
JSON_FILE = WORK_DIR / "server_list.json"

try:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT value_text
        FROM records
        WHERE bucket_id = 8
    """)

    rows = cursor.fetchall()

    # Parse setiap value_text menjadi objek JSON
    data = [json.loads(row[0]) for row in rows]

    # Simpan sebagai JSON
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    print(f"Berhasil: {len(data)} records")
    print(f"Output: {OUTPUT_FILE}")

except (sqlite3.Error, json.JSONDecodeError) as e:
    print(f"Error: {e}")

finally:
    if 'conn' in locals():
        conn.close()
