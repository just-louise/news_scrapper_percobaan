# test_scraper_thread.py

import sys
from PyQt5.QtCore import QCoreApplication
from utils.logger import setup_logger
from core.scraper_thread import ScraperThread

setup_logger()

# Buat aplikasi Qt minimal (diperlukan untuk QThread)
app = QCoreApplication(sys.argv)

print("=" * 60)
print("TEST: Scraper Thread")
print("=" * 60)

hasil_artikel = []

def on_progress(pesan):
    print(f"  📢 {pesan}")

def on_artikel(artikel):
    hasil_artikel.append(artikel)
    print(f"  🗞️  Artikel #{len(hasil_artikel)}: {artikel['title'][:50]}...")

def on_progress_value(nilai):
    # Tampilkan progress bar sederhana di terminal
    bar = "█" * (nilai // 5) + "░" * (20 - nilai // 5)
    print(f"  [{bar}] {nilai}%", end="\r")

def on_selesai(pesan):
    print(f"\n\n{'=' * 60}")
    print(pesan)
    print(f"{'=' * 60}")
    print(f"\n📊 Total artikel terkumpul: {len(hasil_artikel)}")
    # Keluar dari aplikasi setelah selesai
    app.quit()

def on_error(pesan):
    print(f"\n❌ ERROR: {pesan}")
    app.quit()

# Buat dan jalankan thread
thread = ScraperThread(
    url="https://news.detik.com",
    max_articles=5,    # Test dengan 5 artikel dulu
    max_halaman=1,
    delay=2
)

# Hubungkan sinyal
thread.progress_update.connect(on_progress)
thread.article_found.connect(on_artikel)
thread.progress_value.connect(on_progress_value)
thread.finished.connect(on_selesai)
thread.error.connect(on_error)

print(f"\n🚀 Memulai thread...\n")
thread.start()

# Jalankan event loop sampai thread selesai
sys.exit(app.exec_())