# test_date_filter.py

from utils.logger import setup_logger
from core.date_filter import parse_tanggal, dalam_rentang_tanggal
from datetime import datetime

setup_logger()

print("=" * 50)
print("TEST 1: Parse berbagai format tanggal")
print("=" * 50)

# Berbagai format tanggal dari website berita Indonesia
test_dates = [
    "2024-03-05T10:30:00",
    "2024-03-05",
    "05/03/2024",
    "05 Maret 2024",
    "March 05, 2024",
    "Selasa, 05 Mar 2024 10:30 WIB",
    "Tidak diketahui",
    "",
]

for d in test_dates:
    hasil = parse_tanggal(d)
    status = f"→ {hasil.strftime('%d %B %Y')}" if hasil else "→ Tidak bisa di-parse"
    print(f"  Input: '{d:<40}' {status}")

print("\n" + "=" * 50)
print("TEST 2: Filter rentang tanggal")
print("=" * 50)

start = datetime(2024, 3, 1)   # 1 Maret 2024
end   = datetime(2024, 3, 10)  # 10 Maret 2024

artikel_test = [
    {"title": "Berita 28 Feb", "date": "2024-02-28"},  # Sebelum range → TIDAK LOLOS
    {"title": "Berita 1 Mar",  "date": "2024-03-01"},  # Tepat start   → LOLOS
    {"title": "Berita 5 Mar",  "date": "2024-03-05"},  # Di tengah     → LOLOS
    {"title": "Berita 10 Mar", "date": "2024-03-10"},  # Tepat end     → LOLOS
    {"title": "Berita 11 Mar", "date": "2024-03-11"},  # Setelah range → TIDAK LOLOS
    {"title": "Berita tanpa tanggal", "date": "Tidak diketahui"},  # → LOLOS (aman)
]

for artikel in artikel_test:
    lolos = dalam_rentang_tanggal(artikel['date'], start, end)
    status = "✅ LOLOS" if lolos else "❌ TIDAK LOLOS"
    print(f"  {status} | {artikel['title']:<25} | tanggal: {artikel['date']}")