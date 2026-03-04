# test_link_collector.py

from utils.logger import setup_logger
from scraper.link_collector import kumpulkan_link

setup_logger()

# Fungsi callback untuk menampilkan progress
def tampilkan_progress(pesan):
    print(f"  {pesan}")

print("=" * 60)
print("TEST: Kumpulkan link dari halaman berita")
print("=" * 60)

# Ganti URL ini dengan website berita yang ingin di-test
# Contoh lain: https://www.kompas.com/tren
URL_TEST = "https://news.detik.com"

print(f"\n🌐 Target: {URL_TEST}")
print("⏳ Proses sedang berjalan...\n")

links = kumpulkan_link(
    url=URL_TEST,
    max_halaman=2,   # Test 2 halaman saja dulu
    delay=2,
    callback=tampilkan_progress
)

print(f"\n{'=' * 60}")
print(f"📋 HASIL: {len(links)} link artikel ditemukan")
print("=" * 60)

# Tampilkan 5 link pertama sebagai contoh
print("\n5 link pertama:")
for i, link in enumerate(links[:5], 1):
    print(f"  {i}. {link}")