# test_article_parser.py

from utils.logger import setup_logger
from scraper.article_parser import parse_artikel

setup_logger()

# Ambil beberapa link dari hasil test sebelumnya
# Ganti dengan link nyata dari detik.com atau website lain
URL_TEST = [
    "https://news.detik.com/berita/d-8384349/taufik-hidayat-kecam-dugaan-pelecehan-di-pelatnas-panjat-tebing",
    "https://news.detik.com/berita/d-8383034/telantarkan-istri-dan-anak-hakim-pn-kraksaan-diberhentikan-ma",
]

print("=" * 60)
print("TEST: Parse konten artikel")
print("=" * 60)

for i, url in enumerate(URL_TEST, 1):
    print(f"\n{'─' * 60}")
    print(f"📰 Artikel {i}: {url[:60]}...")
    print("─" * 60)

    hasil = parse_artikel(url, delay=2)

    if hasil:
        print(f"✅ BERHASIL!")
        print(f"   Judul   : {hasil['title']}")
        print(f"   Tanggal : {hasil['date']}")
        print(f"   Konten  : {hasil['content'][:150]}...")
        print(f"   URL     : {hasil['url'][:60]}...")
    else:
        print(f"❌ GAGAL mengambil artikel")

print(f"\n{'=' * 60}")
print("Test selesai!")