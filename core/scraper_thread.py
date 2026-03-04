# core/scraper_thread.py

import logging
from PyQt5.QtCore import QThread, pyqtSignal
from scraper.link_collector import kumpulkan_link
from scraper.article_parser import parse_artikel
from core.date_filter import dalam_rentang_tanggal

logger = logging.getLogger(__name__)


class ScraperThread(QThread):
    """
    Thread terpisah untuk menjalankan proses scraping.

    Kenapa pakai QThread bukan Thread biasa?
    → QThread terintegrasi dengan sistem event PyQt5
    → Aman untuk mengirim sinyal ke GUI
    → Bisa dihentikan dengan bersih

    =====================================================
    SINYAL yang bisa diterima oleh GUI:
    =====================================================
    """

    # Kirim pesan teks untuk ditampilkan di log
    # Contoh: "Membuka halaman 1..."
    progress_update = pyqtSignal(str)

    # Kirim data satu artikel yang berhasil di-scrape
    # Contoh: {"title": "...", "date": "...", ...}
    article_found = pyqtSignal(dict)

    # Kirim nilai progress bar (0-100)
    progress_value = pyqtSignal(int)

    # Kirim pesan ketika scraping selesai
    finished = pyqtSignal(str)

    # Kirim pesan ketika terjadi error fatal
    error = pyqtSignal(str)

    def __init__(
        self,
        url,
        max_articles=None,
        max_halaman=5,
        start_date=None,
        end_date=None,
        delay=2
    ):
        """
        Parameter:
        - url          : URL yang akan di-scrape
        - max_articles : batas jumlah artikel (None = tidak dibatasi)
        - max_halaman  : batas jumlah halaman pagination
        - start_date   : filter tanggal awal (datetime object / None)
        - end_date     : filter tanggal akhir (datetime object / None)
        - delay        : jeda antar request (detik)
        """
        super().__init__()

        self.url          = url
        self.max_articles = max_articles
        self.max_halaman  = max_halaman
        self.start_date   = start_date
        self.end_date     = end_date
        self.delay        = delay

        # Flag untuk menghentikan scraping dari luar
        # Ketika user klik tombol "Stop" → _is_running = False
        self._is_running  = True

    def stop(self):
        """
        Dipanggil dari GUI ketika user klik tombol Stop.
        Mengubah flag sehingga loop scraping akan berhenti
        di iterasi berikutnya.
        """
        self._is_running = False
        self.progress_update.emit("⛔ Permintaan stop diterima...")
        logger.info("Scraping dihentikan oleh user")

    # =====================================================
    # FUNGSI UTAMA — Dijalankan saat thread.start() dipanggil
    # =====================================================

    def run(self):
        """
        Isi dari thread. Urutan kerja:

        FASE 1: Kumpulkan semua link artikel
             ↓
        FASE 2: Parse setiap artikel satu per satu
             ↓
        FASE 3: Kirim hasil ke GUI via sinyal
        """
        try:
            self._jalankan_scraping()
        except Exception as e:
            logger.error(f"Error fatal di ScraperThread: {e}")
            self.error.emit(f"Error tidak terduga: {str(e)}")

    def _jalankan_scraping(self):
        """Logika utama scraping, dipisah agar run() tetap bersih."""

        # =====================================================
        # FASE 1: Kumpulkan semua link artikel
        # =====================================================
        self.progress_update.emit(f"🔍 Memulai scraping: {self.url}")
        self.progress_value.emit(3)

        links = kumpulkan_link(
            url=self.url,
            max_halaman=self.max_halaman,
            delay=self.delay,
            # Callback: teruskan pesan dari link_collector ke GUI
            callback=lambda pesan: self.progress_update.emit(pesan)
        )

        # Validasi hasil
        if not links:
            self.error.emit(
                "Tidak ada link artikel yang ditemukan.\n"
                "Pastikan URL benar dan website dapat diakses."
            )
            return

        total_link = len(links)
        self.progress_update.emit(f"📋 Total link ditemukan: {total_link}")
        self.progress_value.emit(10)

        # =====================================================
        # Terapkan batas jumlah artikel jika ada
        # =====================================================
        if self.max_articles and self.max_articles > 0:
            links = links[:self.max_articles]
            self.progress_update.emit(
                f"⚙️ Dibatasi {self.max_articles} artikel "
                f"(dari {total_link} link)"
            )

        total_proses = len(links)

        # =====================================================
        # FASE 2: Parse setiap artikel
        # =====================================================
        jumlah_berhasil = 0
        jumlah_gagal    = 0
        jumlah_dilewati = 0  # Tidak lolos filter tanggal

        for i, link in enumerate(links):

            # ─── Cek apakah user menekan Stop ───
            if not self._is_running:
                self.progress_update.emit("⛔ Scraping dihentikan oleh user.")
                break

            # ─── Update status ───
            self.progress_update.emit(
                f"[{i+1}/{total_proses}] Memproses artikel..."
            )

            # ─── Parse artikel ───
            artikel = parse_artikel(link, delay=self.delay)

            # ─── Artikel gagal diambil ───
            if not artikel:
                jumlah_gagal += 1
                self.progress_update.emit(f"  ⚠️ Gagal: {link[:50]}...")

                # Update progress meskipun gagal
                nilai_progress = self._hitung_progress(i + 1, total_proses)
                self.progress_value.emit(nilai_progress)
                continue

            # ─── Filter tanggal (jika aktif) ───
            if self.start_date or self.end_date:
                lolos = dalam_rentang_tanggal(
                    artikel['date'],
                    self.start_date,
                    self.end_date
                )
                if not lolos:
                    jumlah_dilewati += 1
                    self.progress_update.emit(
                        f"  ⏭️ Dilewati (luar rentang tanggal): "
                        f"{artikel['title'][:40]}..."
                    )
                    nilai_progress = self._hitung_progress(i + 1, total_proses)
                    self.progress_value.emit(nilai_progress)
                    continue

            # ─── Artikel berhasil → kirim ke GUI ───
            self.article_found.emit(artikel)
            jumlah_berhasil += 1
            self.progress_update.emit(
                f"  ✅ Berhasil: {artikel['title'][:50]}..."
            )

            # ─── Update progress bar ───
            nilai_progress = self._hitung_progress(i + 1, total_proses)
            self.progress_value.emit(nilai_progress)

        # =====================================================
        # FASE 3: Selesai — kirim ringkasan
        # =====================================================
        self.progress_value.emit(100)

        pesan_selesai = (
            f"✅ Scraping selesai!\n"
            f"   Berhasil  : {jumlah_berhasil} artikel\n"
            f"   Gagal     : {jumlah_gagal} artikel\n"
            f"   Dilewati  : {jumlah_dilewati} artikel (filter tanggal)\n"
            f"   Total     : {total_proses} link diproses"
        )

        logger.info(pesan_selesai)
        self.finished.emit(pesan_selesai)

    def _hitung_progress(self, selesai, total):
        """
        Hitung nilai progress bar (10-100).
        Mulai dari 10 karena 0-10 dipakai untuk fase collect links.
        """
        if total == 0:
            return 100
        # Range 10-100 untuk fase parsing artikel
        return 10 + int((selesai / total) * 90)