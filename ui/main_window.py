# ui/main_window.py

import logging
from datetime import datetime

from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QTableWidget,
    QTableWidgetItem, QProgressBar, QTextEdit,
    QSpinBox, QCheckBox, QDateEdit, QFileDialog,
    QMessageBox, QGroupBox, QSplitter, QHeaderView,
    QAbstractItemView
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QFont, QColor, QDesktopServices
from PyQt5.QtCore import QUrl

from core.scraper_thread import ScraperThread
from utils.export_manager import export_to_csv, export_to_excel

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.articles      = []   # Simpan semua hasil scraping
        self.scraper_thread = None
        self.init_ui()

    # =========================================================
    # BAGIAN 1: Inisialisasi semua komponen UI
    # =========================================================

    def init_ui(self):
        self.setWindowTitle("🗞️ News Scraper — Web Scraping Application")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(self.get_stylesheet())

        # Widget utama sebagai container
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Susun semua bagian dari atas ke bawah
        layout.addWidget(self.buat_header())
        layout.addWidget(self.buat_seksi_input())
        layout.addWidget(self.buat_seksi_progress())

        # Splitter: tabel di atas, log di bawah
        # User bisa drag garis pemisahnya
        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.buat_seksi_tabel())
        splitter.addWidget(self.buat_seksi_log())
        splitter.setSizes([550, 180])  # Tinggi awal masing-masing
        layout.addWidget(splitter)

        layout.addWidget(self.buat_seksi_export())

    # ─────────────────────────────────────────────────────────
    # Header
    # ─────────────────────────────────────────────────────────
    def buat_header(self):
        label = QLabel("🗞️ News Scraper — Aplikasi Web Scraping Berita")
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont("Segoe UI", 16, QFont.Bold))
        label.setStyleSheet("""
            color: white;
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #2c3e50, stop:1 #3498db
            );
            padding: 14px;
            border-radius: 8px;
        """)
        return label

    # ─────────────────────────────────────────────────────────
    # Seksi Input & Pengaturan
    # ─────────────────────────────────────────────────────────
    def buat_seksi_input(self):
        group = QGroupBox("⚙️ Pengaturan Scraping")
        layout = QVBoxLayout()
        layout.setSpacing(10)

        # ── Baris 1: URL ──
        baris_url = QHBoxLayout()
        lbl_url = QLabel("URL Berita:")
        lbl_url.setFixedWidth(80)
        baris_url.addWidget(lbl_url)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(
            "Masukkan URL homepage atau halaman kategori... "
            "Contoh: https://news.detik.com"
        )
        # Tekan Enter = mulai scraping
        self.url_input.returnPressed.connect(self.mulai_scraping)
        baris_url.addWidget(self.url_input)
        layout.addLayout(baris_url)

        # ── Baris 2: Pengaturan angka ──
        baris_opsi = QHBoxLayout()

        baris_opsi.addWidget(QLabel("Maks. Artikel:"))
        self.spin_max_artikel = QSpinBox()
        self.spin_max_artikel.setRange(0, 1000)
        self.spin_max_artikel.setValue(20)
        self.spin_max_artikel.setSpecialValueText("Semua")
        self.spin_max_artikel.setToolTip(
            "0 = ambil semua artikel yang ditemukan"
        )
        self.spin_max_artikel.setFixedWidth(80)
        baris_opsi.addWidget(self.spin_max_artikel)

        baris_opsi.addSpacing(20)
        baris_opsi.addWidget(QLabel("Maks. Halaman:"))
        self.spin_max_halaman = QSpinBox()
        self.spin_max_halaman.setRange(1, 50)
        self.spin_max_halaman.setValue(3)
        self.spin_max_halaman.setFixedWidth(60)
        baris_opsi.addWidget(self.spin_max_halaman)

        baris_opsi.addSpacing(20)
        baris_opsi.addWidget(QLabel("Delay (detik):"))
        self.spin_delay = QSpinBox()
        self.spin_delay.setRange(1, 15)
        self.spin_delay.setValue(2)
        self.spin_delay.setFixedWidth(60)
        self.spin_delay.setToolTip(
            "Jeda antar request. Jangan terlalu kecil agar tidak di-block!"
        )
        baris_opsi.addWidget(self.spin_delay)

        baris_opsi.addStretch()
        layout.addLayout(baris_opsi)

        # ── Baris 3: Filter tanggal + Tombol ──
        baris_tanggal = QHBoxLayout()

        self.chk_filter_tanggal = QCheckBox("🗓️ Filter Tanggal")
        self.chk_filter_tanggal.setToolTip(
            "Aktifkan untuk hanya mengambil berita dalam rentang tanggal tertentu"
        )
        self.chk_filter_tanggal.toggled.connect(self.toggle_filter_tanggal)
        baris_tanggal.addWidget(self.chk_filter_tanggal)

        baris_tanggal.addWidget(QLabel("  Dari:"))
        self.date_mulai = QDateEdit(QDate.currentDate().addDays(-7))
        self.date_mulai.setDisplayFormat("dd/MM/yyyy")
        self.date_mulai.setCalendarPopup(True)
        self.date_mulai.setEnabled(False)
        self.date_mulai.setFixedWidth(110)
        baris_tanggal.addWidget(self.date_mulai)

        baris_tanggal.addWidget(QLabel("Sampai:"))
        self.date_akhir = QDateEdit(QDate.currentDate())
        self.date_akhir.setDisplayFormat("dd/MM/yyyy")
        self.date_akhir.setCalendarPopup(True)
        self.date_akhir.setEnabled(False)
        self.date_akhir.setFixedWidth(110)
        baris_tanggal.addWidget(self.date_akhir)

        baris_tanggal.addStretch()

        # Tombol Scrape
        self.btn_scrape = QPushButton("▶  Mulai Scraping")
        self.btn_scrape.setObjectName("btn_scrape")
        self.btn_scrape.setFixedHeight(36)
        self.btn_scrape.clicked.connect(self.mulai_scraping)
        baris_tanggal.addWidget(self.btn_scrape)

        # Tombol Stop
        self.btn_stop = QPushButton("⏹  Stop")
        self.btn_stop.setObjectName("btn_stop")
        self.btn_stop.setFixedHeight(36)
        self.btn_stop.setEnabled(False)
        self.btn_stop.clicked.connect(self.hentikan_scraping)
        baris_tanggal.addWidget(self.btn_stop)

        layout.addLayout(baris_tanggal)
        group.setLayout(layout)
        return group

    # ─────────────────────────────────────────────────────────
    # Seksi Progress Bar
    # ─────────────────────────────────────────────────────────
    def buat_seksi_progress(self):
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.lbl_status = QLabel("💤 Siap untuk scraping...")
        self.lbl_status.setStyleSheet("color: #555; font-style: italic;")

        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat(" %p%")
        self.progress_bar.setFixedHeight(22)

        layout.addWidget(self.lbl_status)
        layout.addWidget(self.progress_bar)
        return container

    # ─────────────────────────────────────────────────────────
    # Seksi Tabel Hasil
    # ─────────────────────────────────────────────────────────
    def buat_seksi_tabel(self):
        group = QGroupBox("📊 Hasil Scraping")
        layout = QVBoxLayout()

        # Label jumlah artikel
        self.lbl_jumlah = QLabel("0 artikel ditemukan")
        self.lbl_jumlah.setStyleSheet(
            "font-weight: bold; color: #2980b9; font-size: 12px;"
        )
        layout.addWidget(self.lbl_jumlah)

        # Tabel
        self.tabel = QTableWidget()
        self.tabel.setColumnCount(4)
        self.tabel.setHorizontalHeaderLabels(
            ["Judul Berita", "Tanggal", "Isi Berita", "URL"]
        )

        # Atur lebar kolom
        header = self.tabel.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)        # Judul: fleksibel
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents) # Tanggal: auto
        header.setSectionResizeMode(2, QHeaderView.Stretch)        # Isi: fleksibel
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents) # URL: auto

        self.tabel.setAlternatingRowColors(True)
        self.tabel.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tabel.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tabel.verticalHeader().setDefaultSectionSize(55)
        self.tabel.setWordWrap(True)

        # Klik URL → buka di browser
        self.tabel.cellDoubleClicked.connect(self.buka_url_artikel)

        layout.addWidget(self.tabel)
        group.setLayout(layout)
        return group

    # ─────────────────────────────────────────────────────────
    # Seksi Log Aktivitas
    # ─────────────────────────────────────────────────────────
    def buat_seksi_log(self):
        group = QGroupBox("📋 Log Aktivitas")
        layout = QVBoxLayout()

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setFont(QFont("Consolas", 9))

        baris_btn = QHBoxLayout()
        btn_clear_log = QPushButton("🗑  Bersihkan Log")
        btn_clear_log.setFixedWidth(140)
        btn_clear_log.clicked.connect(self.log_text.clear)
        baris_btn.addWidget(btn_clear_log)
        baris_btn.addStretch()

        layout.addWidget(self.log_text)
        layout.addLayout(baris_btn)
        group.setLayout(layout)
        return group

    # ─────────────────────────────────────────────────────────
    # Seksi Tombol Export
    # ─────────────────────────────────────────────────────────
    def buat_seksi_export(self):
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 4, 0, 0)

        self.btn_export_csv = QPushButton("💾  Export CSV")
        self.btn_export_csv.setObjectName("btn_export")
        self.btn_export_csv.setEnabled(False)
        self.btn_export_csv.clicked.connect(self.export_csv)

        self.btn_export_excel = QPushButton("📊  Export Excel")
        self.btn_export_excel.setObjectName("btn_export")
        self.btn_export_excel.setEnabled(False)
        self.btn_export_excel.clicked.connect(self.export_excel)

        btn_bersihkan = QPushButton("🗑  Bersihkan Tabel")
        btn_bersihkan.clicked.connect(self.bersihkan_tabel)

        layout.addStretch()
        layout.addWidget(self.btn_export_csv)
        layout.addWidget(self.btn_export_excel)
        layout.addWidget(btn_bersihkan)
        return container


    # =========================================================
    # BAGIAN 2: Logika Scraping
    # =========================================================

    def toggle_filter_tanggal(self, aktif):
        """Aktifkan/nonaktifkan input tanggal."""
        self.date_mulai.setEnabled(aktif)
        self.date_akhir.setEnabled(aktif)

    def mulai_scraping(self):
        """Validasi input lalu jalankan ScraperThread."""

        url = self.url_input.text().strip()

        # ── Validasi URL ──
        if not url:
            QMessageBox.warning(self, "Peringatan", "URL tidak boleh kosong!")
            return
        if not url.startswith("http"):
            QMessageBox.warning(
                self, "URL Tidak Valid",
                "URL harus dimulai dengan http:// atau https://"
            )
            return

        # ── Ambil nilai pengaturan ──
        max_artikel = self.spin_max_artikel.value() or None
        max_halaman = self.spin_max_halaman.value()
        delay       = self.spin_delay.value()

        # ── Ambil filter tanggal ──
        start_date = end_date = None
        if self.chk_filter_tanggal.isChecked():
            sd = self.date_mulai.date()
            ed = self.date_akhir.date()
            start_date = datetime(sd.year(), sd.month(), sd.day())
            end_date   = datetime(ed.year(), ed.month(), ed.day(), 23, 59, 59)

            # Validasi tanggal
            if start_date > end_date:
                QMessageBox.warning(
                    self, "Tanggal Tidak Valid",
                    "Tanggal mulai tidak boleh lebih besar dari tanggal akhir!"
                )
                return

        # ── Update status UI ──
        self.btn_scrape.setEnabled(False)
        self.btn_stop.setEnabled(True)
        self.btn_export_csv.setEnabled(False)
        self.btn_export_excel.setEnabled(False)
        self.progress_bar.setValue(0)
        self.tambah_log(f"🚀 Memulai scraping: {url}")

        # ── Buat dan jalankan thread ──
        self.scraper_thread = ScraperThread(
            url=url,
            max_articles=max_artikel,
            max_halaman=max_halaman,
            start_date=start_date,
            end_date=end_date,
            delay=delay
        )

        # Hubungkan sinyal thread → fungsi di GUI
        self.scraper_thread.progress_update.connect(self.tambah_log)
        self.scraper_thread.article_found.connect(self.tambah_artikel_ke_tabel)
        self.scraper_thread.progress_value.connect(self.progress_bar.setValue)
        self.scraper_thread.finished.connect(self.on_selesai)
        self.scraper_thread.error.connect(self.on_error)

        self.scraper_thread.start()

    def hentikan_scraping(self):
        """Kirim sinyal stop ke thread."""
        if self.scraper_thread and self.scraper_thread.isRunning():
            self.scraper_thread.stop()
            self.btn_stop.setEnabled(False)
            self.tambah_log("⛔ Menghentikan scraping...")

    def on_selesai(self, pesan):
        """Dipanggil ketika thread selesai."""
        self.tambah_log(pesan)
        self.lbl_status.setText("✅ Scraping selesai!")
        self.btn_scrape.setEnabled(True)
        self.btn_stop.setEnabled(False)
        if self.articles:
            self.btn_export_csv.setEnabled(True)
            self.btn_export_excel.setEnabled(True)
        QMessageBox.information(self, "Selesai", pesan)

    def on_error(self, pesan):
        """Dipanggil ketika thread mengalami error."""
        self.tambah_log(f"❌ {pesan}")
        self.lbl_status.setText("❌ Terjadi error!")
        self.btn_scrape.setEnabled(True)
        self.btn_stop.setEnabled(False)
        QMessageBox.critical(self, "Error", pesan)


    # =========================================================
    # BAGIAN 3: Update Tabel
    # =========================================================

    def tambah_artikel_ke_tabel(self, artikel):
        """
        Dipanggil setiap kali satu artikel selesai di-scrape.
        Menambahkan satu baris baru ke tabel.
        """
        self.articles.append(artikel)

        # Tambah baris baru di bawah
        baris = self.tabel.rowCount()
        self.tabel.insertRow(baris)

        # Kolom 0: Judul
        item_judul = QTableWidgetItem(artikel.get('title', ''))
        item_judul.setToolTip(artikel.get('title', ''))
        self.tabel.setItem(baris, 0, item_judul)

        # Kolom 1: Tanggal
        item_tanggal = QTableWidgetItem(artikel.get('date', ''))
        item_tanggal.setTextAlignment(Qt.AlignCenter)
        self.tabel.setItem(baris, 1, item_tanggal)

        # Kolom 2: Isi Berita
        item_isi = QTableWidgetItem(artikel.get('content', ''))
        item_isi.setToolTip(artikel.get('content', ''))  # Hover = tampilkan lengkap
        self.tabel.setItem(baris, 2, item_isi)

        # Kolom 3: URL (berwarna biru)
        item_url = QTableWidgetItem(artikel.get('url', ''))
        item_url.setForeground(QColor("#2980b9"))
        item_url.setToolTip("Double-click untuk membuka di browser")
        self.tabel.setItem(baris, 3, item_url)

        # Update label jumlah
        self.lbl_jumlah.setText(f"{len(self.articles)} artikel ditemukan")

        # Auto scroll ke baris terbaru
        self.tabel.scrollToBottom()

    def buka_url_artikel(self, baris, kolom):
        """Double-click pada baris tabel → buka URL di browser."""
        url_item = self.tabel.item(baris, 3)  # Kolom 3 = URL
        if url_item:
            url = url_item.text()
            if url.startswith("http"):
                QDesktopServices.openUrl(QUrl(url))

    def bersihkan_tabel(self):
        """Kosongkan tabel dan reset semua data."""
        konfirmasi = QMessageBox.question(
            self, "Konfirmasi",
            "Yakin ingin membersihkan semua data di tabel?",
            QMessageBox.Yes | QMessageBox.No
        )
        if konfirmasi == QMessageBox.Yes:
            self.tabel.setRowCount(0)
            self.articles.clear()
            self.lbl_jumlah.setText("0 artikel ditemukan")
            self.btn_export_csv.setEnabled(False)
            self.btn_export_excel.setEnabled(False)
            self.progress_bar.setValue(0)
            self.tambah_log("🗑️ Tabel dibersihkan.")


    # =========================================================
    # BAGIAN 4: Log
    # =========================================================

    def tambah_log(self, pesan):
        """Tambahkan pesan ke panel log dengan timestamp."""
        waktu = datetime.now().strftime("%H:%M:%S")
        self.log_text.append(f"[{waktu}] {pesan}")
        self.lbl_status.setText(pesan)
        # Auto scroll log ke bawah
        self.log_text.verticalScrollBar().setValue(
            self.log_text.verticalScrollBar().maximum()
        )


    # =========================================================
    # BAGIAN 5: Export
    # =========================================================

    def export_csv(self):
        if not self.articles:
            QMessageBox.warning(self, "Peringatan", "Tidak ada data untuk di-export!")
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Simpan sebagai CSV",
            f"hasil_scraping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )
        if filepath:
            try:
                export_to_csv(self.articles, filepath)
                self.tambah_log(f"💾 Export CSV berhasil: {filepath}")
                QMessageBox.information(
                    self, "Berhasil",
                    f"Data berhasil disimpan!\n\n{filepath}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Gagal Export", str(e))

    def export_excel(self):
        if not self.articles:
            QMessageBox.warning(self, "Peringatan", "Tidak ada data untuk di-export!")
            return

        filepath, _ = QFileDialog.getSaveFileName(
            self, "Simpan sebagai Excel",
            f"hasil_scraping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            "Excel Files (*.xlsx)"
        )
        if filepath:
            try:
                export_to_excel(self.articles, filepath)
                self.tambah_log(f"📊 Export Excel berhasil: {filepath}")
                QMessageBox.information(
                    self, "Berhasil",
                    f"Data berhasil disimpan!\n\n{filepath}"
                )
            except Exception as e:
                QMessageBox.critical(self, "Gagal Export", str(e))


    # =========================================================
    # BAGIAN 6: Stylesheet (tampilan visual)
    # =========================================================

    def get_stylesheet(self):
        return """
        QMainWindow {
            background-color: #f0f2f5;
        }
        QGroupBox {
            font-weight: bold;
            font-size: 12px;
            border: 1px solid #d0d3d9;
            border-radius: 8px;
            margin-top: 8px;
            padding-top: 12px;
            background-color: white;
        }
        QGroupBox::title {
            subcontrol-origin: margin;
            left: 12px;
            padding: 0 6px;
            color: #2c3e50;
        }
        QPushButton {
            padding: 7px 18px;
            border-radius: 6px;
            font-size: 12px;
            font-weight: bold;
            background-color: #3498db;
            color: white;
            border: none;
        }
        QPushButton:hover {
            background-color: #2980b9;
        }
        QPushButton:disabled {
            background-color: #bdc3c7;
            color: #7f8c8d;
        }
        QPushButton#btn_scrape {
            background-color: #27ae60;
            font-size: 13px;
            padding: 8px 24px;
        }
        QPushButton#btn_scrape:hover {
            background-color: #219a52;
        }
        QPushButton#btn_stop {
            background-color: #e74c3c;
            font-size: 13px;
            padding: 8px 24px;
        }
        QPushButton#btn_stop:hover {
            background-color: #c0392b;
        }
        QPushButton#btn_export {
            background-color: #8e44ad;
        }
        QPushButton#btn_export:hover {
            background-color: #7d3c98;
        }
        QLineEdit, QSpinBox, QDateEdit {
            padding: 6px 10px;
            border: 1px solid #d0d3d9;
            border-radius: 6px;
            font-size: 12px;
            background: white;
        }
        QLineEdit:focus, QSpinBox:focus {
            border: 1px solid #3498db;
        }
        QTableWidget {
            gridline-color: #ecf0f1;
            font-size: 11px;
            border: 1px solid #d0d3d9;
            border-radius: 6px;
        }
        QTableWidget::item {
            padding: 4px;
        }
        QTableWidget::item:selected {
            background-color: #d6eaf8;
            color: #2c3e50;
        }
        QHeaderView::section {
            background: qlineargradient(
                x1:0, y1:0, x2:0, y2:1,
                stop:0 #34495e, stop:1 #2c3e50
            );
            color: white;
            padding: 8px;
            font-weight: bold;
            font-size: 11px;
            border: none;
        }
        QProgressBar {
            border: 1px solid #d0d3d9;
            border-radius: 6px;
            background: #ecf0f1;
            text-align: center;
            font-weight: bold;
            color: #2c3e50;
        }
        QProgressBar::chunk {
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:0,
                stop:0 #27ae60, stop:1 #2ecc71
            );
            border-radius: 6px;
        }
        QTextEdit {
            font-family: Consolas, monospace;
            font-size: 10px;
            background: #1e272e;
            color: #dfe6e9;
            border: 1px solid #d0d3d9;
            border-radius: 6px;
        }
        QSplitter::handle {
            background: #d0d3d9;
            height: 4px;
        }
        """