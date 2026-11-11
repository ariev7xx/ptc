
import json
import zlib
import urllib.request
import traceback
from pathlib import Path

URL = "https://s3.amazonaws.com/psiphon/web/mjr4-p23r-puwl/server_list_compressed"

BASE_DIR = Path(__file__).resolve().parent

COMPRESSED_FILE = BASE_DIR / "server_list_compressed"
DAT_FILE = BASE_DIR / "server_list.dat"
JSON_FILE = BASE_DIR / "psiphon_servers.json"


def main():
    print("=" * 45)
    print("       PSIPHON SERVER LIST EXTRACTOR")
    print("=" * 45)

    # 1. Download server list
    print("\n[1/5] Mengunduh server list...")

    request = urllib.request.Request(
        URL,
        headers={"User-Agent": "Psiphon"}
    )

    with urllib.request.urlopen(request, timeout=60) as response:
        data = response.read()

    COMPRESSED_FILE.write_bytes(data)

    print(f"      Berhasil: {len(data):,} bytes")

    # 2. Decompress ZLIB
    print("\n[2/5] Dekompresi ZLIB...")

    decoded = zlib.decompress(data)
    wrapper = json.loads(decoded)

    hex_data = wrapper["data"]

    print("      Berhasil")

    # 3. Save HEX data
    print("\n[3/5] Menyimpan server_list.dat...")

    DAT_FILE.write_text(hex_data, encoding="utf-8")

    # 4. HEX to UTF-8
    print("\n[4/5] Mengubah HEX menjadi teks...")

    text = bytes.fromhex(hex_data).decode("utf-8")

    # 5. Extract JSON objects
    print("\n[5/5] Mengekstrak daftar server...")

    decoder = json.JSONDecoder()
    servers = []
    position = 0

    while position < len(text):
        start = text.find("{", position)

        if start == -1:
            break

        try:
            obj, end = decoder.raw_decode(text, start)

            if isinstance(obj, dict):
                servers.append(obj)

            position = end

        except json.JSONDecodeError:
            position = start + 1

    # Save JSON
    JSON_FILE.write_text(
        json.dumps(servers, indent=4, ensure_ascii=False),
        encoding="utf-8"
    )

    file = Path(COMPRESSED_FILE)
    file.unlink()

    print("\n" + "=" * 45)
    print("             PROSES SELESAI")
    print("=" * 45)

    print(f"\nTotal server : {len(servers)}")
    print(f"Ukuran JSON : {JSON_FILE.stat().st_size:,} bytes")

    print("\nFile berhasil dibuat:")

    print(f"\n1. {DAT_FILE.name}")
    print(f"2. {JSON_FILE.name}")

    print("\nLokasi:")
    print(BASE_DIR)

    print("\n" + "=" * 45)


if __name__ == "__main__":
    try:
        main()

    except Exception:
        print("\n[ERROR] Proses gagal!")
        traceback.print_exc()

    input("\nTekan ENTER untuk keluar...")
