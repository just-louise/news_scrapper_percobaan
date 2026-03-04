# utils/logger.py

import logging
import os
from datetime import datetime


def setup_logger():
    """
    Setup sistem logging aplikasi.
    
    Log akan dikirim ke 2 tempat sekaligus:
    1. File  → disimpan di folder logs/ (lengkap, level DEBUG ke atas)
    2. Console/terminal → hanya INFO ke atas (tidak terlalu ramai)
    """

    # =====================================================
    # BAGIAN 1: Buat folder logs jika belum ada
    # =====================================================
    os.makedirs("logs", exist_ok=True)
    # exist_ok=True → tidak error meskipun folder sudah ada

    # =====================================================
    # BAGIAN 2: Tentukan nama file log
    # Format: scraping_20240315_103045.log
    # Setiap kali app dijalankan = file log baru
    # =====================================================
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"logs/scraping_{timestamp}.log"

    # =====================================================
    # BAGIAN 3: Format tampilan log
    # Contoh output: 10:30:01 [INFO] scraper.link_collector: Membuka halaman 1
    # =====================================================
    formatter = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S"
    )

    # =====================================================
    # BAGIAN 4: Setup root logger
    # Root logger = "induk" dari semua logger di seluruh app
    # =====================================================
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Tangkap semua level

    # Hindari duplikasi handler jika fungsi ini dipanggil 2x
    if root_logger.handlers:
        root_logger.handlers.clear()

    # =====================================================
    # BAGIAN 5: Handler 1 — Simpan ke FILE
    # =====================================================
    file_handler = logging.FileHandler(log_filename, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)  # Simpan semua level ke file
    file_handler.setFormatter(formatter)

    # =====================================================
    # BAGIAN 6: Handler 2 — Tampilkan di CONSOLE/TERMINAL
    # =====================================================
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)  # Terminal hanya tampilkan INFO ke atas
    console_handler.setFormatter(formatter)

    # =====================================================
    # BAGIAN 7: Daftarkan kedua handler ke root logger
    # =====================================================
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # Catat bahwa logger sudah aktif
    logging.info(f"Logger aktif. File log disimpan di: {log_filename}")

    return root_logger