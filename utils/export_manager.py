# utils/export_manager.py

import pandas as pd
import csv
import os
import logging
from datetime import datetime

# Ambil logger yang sudah kita buat di step 2
logger = logging.getLogger(__name__)


def export_to_csv(articles, filepath=None):
    """
    Export daftar artikel ke file CSV.

    Parameter:
    - articles : list of dict, contoh:
                 [{"title": "...", "date": "...", "content": "...", "url": "..."}]
    - filepath : lokasi file yang akan disimpan
                 Jika None, otomatis diberi nama dengan timestamp

    Return: filepath (string) lokasi file yang disimpan
    """

    # =====================================================
    # BAGIAN 1: Tentukan nama file jika tidak diberikan
    # =====================================================
    if not filepath:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"hasil_scraping_{timestamp}.csv"

    try:
        # =====================================================
        # BAGIAN 2: Tulis data ke CSV
        # encoding utf-8-sig → agar Excel bisa baca
        # karakter Indonesia (é, ñ, dll) dengan benar
        # =====================================================
        with open(filepath, 'w', newline='', encoding='utf-8-sig') as f:
            fieldnames = ['title', 'date', 'content', 'url']
            writer = csv.DictWriter(f, fieldnames=fieldnames)

            # Tulis baris header: title, date, content, url
            writer.writeheader()

            # Tulis setiap artikel sebagai satu baris
            writer.writerows(articles)

        logger.info(f"Export CSV berhasil: {filepath} ({len(articles)} artikel)")
        return filepath

    except PermissionError:
        # Terjadi jika file sedang dibuka di Excel
        logger.error(f"File {filepath} sedang digunakan, tutup dulu!")
        raise Exception(f"File sedang dibuka di program lain. Tutup dulu lalu coba lagi.")

    except Exception as e:
        logger.error(f"Gagal export CSV: {e}")
        raise


def export_to_excel(articles, filepath=None):
    """
    Export daftar artikel ke file Excel (.xlsx).

    Parameter:
    - articles : list of dict (sama seperti export_to_csv)
    - filepath : lokasi file yang akan disimpan

    Return: filepath (string) lokasi file yang disimpan
    """

    # =====================================================
    # BAGIAN 1: Tentukan nama file jika tidak diberikan
    # =====================================================
    if not filepath:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = f"hasil_scraping_{timestamp}.xlsx"

    try:
        # =====================================================
        # BAGIAN 2: Konversi list of dict ke DataFrame pandas
        # DataFrame = tabel data (seperti tabel Excel di Python)
        # =====================================================
        df = pd.DataFrame(articles)

        # Pastikan kolom ada meskipun data kosong
        for col in ['title', 'date', 'content', 'url']:
            if col not in df.columns:
                df[col] = ''

        # Ambil hanya kolom yang diperlukan, urutkan
        df = df[['title', 'date', 'content', 'url']]

        # Ganti nama kolom ke Bahasa Indonesia
        df.columns = ['Judul', 'Tanggal', 'Isi Berita', 'URL']

        # =====================================================
        # BAGIAN 3: Tulis ke file Excel dengan formatting
        # =====================================================
        with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Hasil Scraping')

            # Akses worksheet untuk atur lebar kolom
            worksheet = writer.sheets['Hasil Scraping']

            # Atur lebar tiap kolom (dalam karakter)
            worksheet.column_dimensions['A'].width = 60  # Judul
            worksheet.column_dimensions['B'].width = 20  # Tanggal
            worksheet.column_dimensions['C'].width = 80  # Isi Berita
            worksheet.column_dimensions['D'].width = 50  # URL

            # Atur tinggi baris header
            worksheet.row_dimensions[1].height = 20

        logger.info(f"Export Excel berhasil: {filepath} ({len(articles)} artikel)")
        return filepath

    except PermissionError:
        logger.error(f"File {filepath} sedang digunakan, tutup dulu!")
        raise Exception(f"File sedang dibuka di program lain. Tutup dulu lalu coba lagi.")

    except Exception as e:
        logger.error(f"Gagal export Excel: {e}")
        raise