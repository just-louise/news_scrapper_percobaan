# core/date_filter.py

import logging
import re
from datetime import datetime

logger = logging.getLogger(__name__)

# =====================================================
# DAFTAR FORMAT TANGGAL YANG UMUM DIPAKAI WEBSITE BERITA
# Python akan mencoba satu per satu dari atas ke bawah
# =====================================================
DATE_FORMATS = [
    # Format ISO 8601 (paling umum di website modern)
    "%Y-%m-%dT%H:%M:%S",           # 2024-03-05T10:30:00
    "%Y-%m-%dT%H:%M:%S%z",         # 2024-03-05T10:30:00+07:00
    "%Y-%m-%dT%H:%M:%SZ",          # 2024-03-05T10:30:00Z

    # Format tanggal + waktu
    "%Y-%m-%d %H:%M:%S",           # 2024-03-05 10:30:00
    "%d/%m/%Y %H:%M:%S",           # 05/03/2024 10:30:00
    "%d-%m-%Y %H:%M:%S",           # 05-03-2024 10:30:00

    # Format tanggal saja
    "%Y-%m-%d",                     # 2024-03-05
    "%d/%m/%Y",                     # 05/03/2024
    "%d-%m-%Y",                     # 05-03-2024

    # Format dengan nama bulan Inggris
    "%B %d, %Y",                    # March 05, 2024
    "%d %B %Y",                     # 05 March 2024
    "%b %d, %Y",                    # Mar 05, 2024
    "%d %b %Y",                     # 05 Mar 2024

    # Format dengan nama bulan Indonesia
    "%d %B %Y",                     # 05 Maret 2024 (ditangani manual di bawah)
]

# =====================================================
# KAMUS BULAN INDONESIA → INGGRIS
# Karena Python tidak mengenali nama bulan Indonesia
# =====================================================
BULAN_ID = {
    "januari": "January",   "februari": "February",
    "maret": "March",       "april": "April",
    "mei": "May",           "juni": "June",
    "juli": "July",         "agustus": "August",
    "september": "September","oktober": "October",
    "november": "November", "desember": "December",
    # Singkatan
    "jan": "Jan", "feb": "Feb", "mar": "Mar", "apr": "Apr",
    "jun": "Jun", "jul": "Jul", "ags": "Aug", "sep": "Sep",
    "okt": "Oct", "nov": "Nov", "des": "Dec",
}


def terjemahkan_bulan(date_str):
    """
    Ganti nama bulan Indonesia dengan Inggris.
    Contoh: "05 Maret 2024" → "05 March 2024"
    """
    date_lower = date_str.lower()
    for indo, english in BULAN_ID.items():
        if indo in date_lower:
            date_str = re.sub(indo, english, date_lower, flags=re.IGNORECASE)
            break
    return date_str


def bersihkan_tanggal(date_str):
    """
    Bersihkan string tanggal dari karakter yang tidak perlu.

    Contoh:
    "Selasa, 05 Mar 2024 10:30 WIB" → "05 Mar 2024 10:30"
    "  2024-03-05T10:30:00+07:00  " → "2024-03-05T10:30:00+07:00"
    """
    if not date_str:
        return ""

    # Hilangkan spasi di awal/akhir
    date_str = date_str.strip()

    # Hilangkan nama hari (Senin, Selasa, dll) beserta koma
    # Contoh: "Selasa, 05 Mar 2024" → "05 Mar 2024"
    hari = ["senin", "selasa", "rabu", "kamis", "jumat", "sabtu", "minggu",
            "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    for h in hari:
        pattern = rf"(?i){h},?\s*"
        date_str = re.sub(pattern, "", date_str).strip()

    # Hilangkan informasi timezone teks (WIB, WITA, WIT, UTC)
    date_str = re.sub(r'\s*(WIB|WITA|WIT|UTC|GMT)\s*', '', date_str, flags=re.IGNORECASE)

    # Terjemahkan bulan Indonesia ke Inggris
    date_str = terjemahkan_bulan(date_str)

    return date_str.strip()


def parse_tanggal(date_str):
    """
    Ubah string tanggal menjadi objek datetime.

    Mencoba semua format satu per satu hingga berhasil.
    Return: datetime object, atau None jika semua format gagal.
    """
    if not date_str or date_str == "Tidak diketahui":
        return None

    # Bersihkan string tanggal dulu
    date_str_bersih = bersihkan_tanggal(date_str)

    if not date_str_bersih:
        return None

    # Coba setiap format
    for fmt in DATE_FORMATS:
        try:
            # Coba parse dengan panjang sesuai format
            hasil = datetime.strptime(date_str_bersih[:len(fmt)+5], fmt)
            return hasil
        except (ValueError, TypeError):
            continue

    # Jika semua format gagal, coba cari pola tanggal dengan regex
    # Mencari pola: 4 digit tahun
    try:
        # Cari angka tahun (4 digit antara 2000-2030)
        match = re.search(r'(20[0-2][0-9])', date_str_bersih)
        if match:
            tahun = int(match.group(1))
            # Cari angka bulan (1-12)
            angka = re.findall(r'\d+', date_str_bersih)
            if len(angka) >= 2:
                # Asumsi format: dd mm yyyy atau yyyy mm dd
                return datetime(tahun, 1, 1)  # Fallback ke 1 Jan tahun tersebut
    except Exception:
        pass

    logger.warning(f"Tidak bisa parse tanggal: '{date_str}'")
    return None


def dalam_rentang_tanggal(date_str, start_date=None, end_date=None):
    """
    Cek apakah tanggal artikel berada dalam rentang yang ditentukan.

    Parameter:
    - date_str   : string tanggal dari hasil scraping
    - start_date : datetime object batas awal (atau None)
    - end_date   : datetime object batas akhir (atau None)

    Return:
    - True  → artikel LOLOS filter (ditampilkan)
    - False → artikel TIDAK LOLOS filter (dilewati)

    Aturan:
    - Jika start_date dan end_date keduanya None → semua artikel lolos
    - Jika tanggal tidak bisa di-parse → artikel tetap lolos (aman)
    """
    # Tidak ada filter → semua lolos
    if not start_date and not end_date:
        return True

    tanggal_artikel = parse_tanggal(date_str)

    # Tanggal tidak bisa di-parse → tetap lolos (jangan buang artikel)
    if tanggal_artikel is None:
        logger.debug(f"Tanggal tidak bisa di-parse, artikel diloloskan: '{date_str}'")
        return True

    # Hilangkan timezone info untuk perbandingan yang aman
    if hasattr(tanggal_artikel, 'tzinfo') and tanggal_artikel.tzinfo:
        tanggal_artikel = tanggal_artikel.replace(tzinfo=None)

    # Cek batas awal
    if start_date and tanggal_artikel < start_date:
        logger.debug(f"Artikel terlalu lama: {date_str} < {start_date.date()}")
        return False

    # Cek batas akhir
    if end_date and tanggal_artikel > end_date:
        logger.debug(f"Artikel terlalu baru: {date_str} > {end_date.date()}")
        return False

    return True