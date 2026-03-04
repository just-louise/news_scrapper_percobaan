# main.py

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from utils.logger import setup_logger
from ui.main_window import MainWindow


def main():
    # =====================================================
    # LANGKAH 1: Aktifkan logger
    # Harus dilakukan PERTAMA sebelum apapun
    # =====================================================
    setup_logger()

    # =====================================================
    # LANGKAH 2: Buat aplikasi PyQt5
    # sys.argv diteruskan agar PyQt bisa baca
    # argumen command line jika ada
    # =====================================================
    app = QApplication(sys.argv)
    app.setApplicationName("News Scraper")
    app.setApplicationVersion("1.0.0")

    # Agar font terlihat lebih bagus di Windows
    app.setStyle("Fusion")

    # =====================================================
    # LANGKAH 3 & 4: Buat dan tampilkan jendela utama
    # =====================================================
    window = MainWindow()
    window.show()

    # =====================================================
    # LANGKAH 5: Jalankan event loop
    # app.exec_() akan "membekukan" program di sini
    # dan terus menunggu interaksi user (klik, ketik, dll)
    # Program baru keluar ketika user menutup jendela
    # =====================================================
    sys.exit(app.exec_())


if __name__ == "__main__":
    # Pastikan working directory adalah folder project
    # Ini penting agar import antar modul berjalan benar
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    main()
