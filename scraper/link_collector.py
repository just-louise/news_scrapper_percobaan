# scraper/link_collector.py

import time
import logging
from urllib.parse import urljoin, urlparse

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    TimeoutException,
    WebDriverException
)
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)


# =====================================================
# BAGIAN 1: Membuat WebDriver
# =====================================================

def buat_driver(headless=True):
    """
    Membuat instance WebDriver Chrome.

    Parameter:
    - headless : True  → browser tidak tampil (lebih cepat)
                 False → browser tampil (berguna saat debugging)

    Return: WebDriver instance
    """
    options = Options()

    if headless:
        options.add_argument("--headless")

    # Argumen wajib agar Chrome berjalan stabil
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    # Pura-pura jadi browser biasa bukan bot
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )

    # Matikan notifikasi dan popup
    options.add_argument("--disable-notifications")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    # Sembunyikan tanda bahwa ini selenium
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )

    return driver


# =====================================================
# BAGIAN 2: Filter Link Artikel
# =====================================================

# Kata-kata yang menandakan link BUKAN artikel
KATA_SKIP = [
    '#', 'javascript:', 'mailto:', 'tel:',
    '/tag/', '/tags/', '/topic/',
    '/category/', '/categories/', '/kategori/',
    '/author/', '/penulis/',
    '/page/', '/halaman/',
    '/search', '/pencarian/',
    '/login', '/register', '/signup',
    '/about', '/tentang',
    '/contact', '/kontak',
    '/advertise', '/iklan',
    '/privacy', '/terms',
    '/sitemap',
    '.jpg', '.jpeg', '.png', '.gif', '.pdf',
    '.mp4', '.mp3',
]

def adalah_link_artikel(href, base_url):
    """
    Menentukan apakah sebuah link kemungkinan adalah artikel berita.

    Parameter:
    - href     : URL yang akan dicek
    - base_url : URL halaman utama (untuk cek domain)

    Return: True jika kemungkinan artikel, False jika bukan
    """
    if not href:
        return False

    parsed_base = urlparse(base_url)
    parsed_href = urlparse(href)

    # =====================================================
    # FILTER 1: Harus domain yang sama
    # Contoh: base = detik.com, href = kompas.com → SKIP
    # =====================================================
    if parsed_href.netloc:
        if parsed_href.netloc != parsed_base.netloc:
            return False

    # =====================================================
    # FILTER 2: Tidak boleh mengandung kata yang di-skip
    # =====================================================
    href_lower = href.lower()
    for kata in KATA_SKIP:
        if kata in href_lower:
            return False

    # =====================================================
    # FILTER 3: Path harus cukup panjang
    # Link artikel biasanya: /berita/ini-adalah-judul-artikel
    # Link menu biasanya: /news atau /
    # =====================================================
    path = parsed_href.path
    if len(path) < 10:
        return False

    # =====================================================
    # FILTER 4: Tidak boleh sama persis dengan base URL
    # =====================================================
    if href.rstrip('/') == base_url.rstrip('/'):
        return False

    return True


# =====================================================
# BAGIAN 3: Cari Tombol Halaman Berikutnya
# =====================================================

def cari_halaman_berikutnya(driver, url_sekarang):
    """
    Mencari URL halaman berikutnya (pagination).

    Mencoba berbagai pola tombol "Next" yang umum dipakai website.

    Return: URL halaman berikutnya, atau None jika tidak ada.
    """

    # Pola XPath untuk tombol Next
    pola_next = [
        # Berdasarkan teks
        "//a[contains(text(), 'Next')]",
        "//a[contains(text(), 'next')]",
        "//a[contains(text(), 'Selanjutnya')]",
        "//a[contains(text(), 'selanjutnya')]",
        "//a[contains(text(), 'Berikutnya')]",
        "//a[contains(text(), '>')]",
        "//a[contains(text(), '»')]",
        # Berdasarkan class
        "//a[contains(@class, 'next')]",
        "//a[contains(@class, 'Next')]",
        "//a[contains(@class, 'pagination-next')]",
        "//a[contains(@class, 'page-next')]",
        # Berdasarkan rel attribute
        "//a[@rel='next']",
        "//link[@rel='next']",
        # Berdasarkan aria-label
        "//a[@aria-label='Next']",
        "//a[@aria-label='next']",
        # Di dalam elemen li
        "//li[contains(@class, 'next')]/a",
        "//li[@class='next']/a",
    ]

    for pola in pola_next:
        try:
            elemen = driver.find_element(By.XPATH, pola)
            href = elemen.get_attribute("href")
            if href and href != url_sekarang:
                logger.debug(f"Tombol next ditemukan dengan pola: {pola}")
                return href
        except NoSuchElementException:
            continue
        except Exception as e:
            logger.debug(f"Error cek pola {pola}: {e}")
            continue

    return None  # Tidak ada halaman berikutnya


# =====================================================
# BAGIAN 4: Fungsi Utama — Kumpulkan Semua Link
# =====================================================

def kumpulkan_link(url, max_halaman=5, delay=2, callback=None):
    """
    Fungsi utama: kumpulkan semua link artikel dari sebuah halaman.

    Parameter:
    - url          : URL halaman utama/kategori yang akan di-scrape
    - max_halaman  : batas maksimal halaman yang di-crawl (pagination)
    - delay        : jeda antar halaman dalam detik (jangan terlalu kecil!)
    - callback     : fungsi untuk mengirim pesan status ke GUI
                     Contoh: callback("Membuka halaman 1...")

    Return: list of string (URL artikel yang unik)
    """

    # Fungsi helper untuk kirim pesan ke GUI atau print ke terminal
    def log(pesan):
        logger.info(pesan)
        if callback:
            callback(pesan)

    driver = buat_driver(headless=True)
    semua_link = set()  # Set agar tidak ada duplikat
    url_sekarang = url
    halaman = 1

    try:
        while halaman <= max_halaman:
            log(f"📄 Membuka halaman {halaman}: {url_sekarang[:60]}...")

            # =====================================================
            # LANGKAH 1: Buka halaman
            # =====================================================
            try:
                driver.get(url_sekarang)
            except WebDriverException as e:
                log(f"❌ Gagal membuka halaman: {e}")
                break

            # =====================================================
            # LANGKAH 2: Tunggu halaman selesai dimuat
            # Tunggu maksimal 15 detik sampai tag <body> muncul
            # =====================================================
            try:
                WebDriverWait(driver, 15).until(
                    EC.presence_of_element_located((By.TAG_NAME, "body"))
                )
            except TimeoutException:
                log(f"⚠️ Timeout menunggu halaman {halaman}, lanjut...")

            # Delay tambahan untuk konten dinamis (JavaScript)
            time.sleep(delay)

            # =====================================================
            # LANGKAH 3: Scroll ke bawah agar konten lazy-load muncul
            # Beberapa website baru menampilkan artikel setelah di-scroll
            # =====================================================
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
            time.sleep(1)
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1)

            # =====================================================
            # LANGKAH 4: Ambil semua tag <a href="...">
            # =====================================================
            semua_a = driver.find_elements(By.TAG_NAME, "a")
            link_halaman_ini = set()

            for a in semua_a:
                try:
                    href = a.get_attribute("href")
                    if href:
                        # Jadikan URL absolut jika masih relatif
                        # Contoh: "/berita/123" → "https://detik.com/berita/123"
                        url_lengkap = urljoin(url_sekarang, href)

                        if adalah_link_artikel(url_lengkap, url):
                            link_halaman_ini.add(url_lengkap)
                except Exception:
                    continue

            # Hitung link baru (belum ada di halaman sebelumnya)
            link_baru = link_halaman_ini - semua_link
            semua_link.update(link_halaman_ini)

            log(f"✅ Halaman {halaman}: {len(link_baru)} link baru "
                f"(total: {len(semua_link)})")

            # =====================================================
            # LANGKAH 5: Cari tombol halaman berikutnya
            # =====================================================
            url_berikutnya = cari_halaman_berikutnya(driver, url_sekarang)

            if not url_berikutnya:
                log(f"📌 Tidak ada halaman berikutnya. Selesai di halaman {halaman}.")
                break

            url_sekarang = url_berikutnya
            halaman += 1

    except Exception as e:
        logger.error(f"Error tidak terduga di kumpulkan_link: {e}")
        if callback:
            callback(f"❌ Error: {e}")

    finally:
        # SELALU tutup browser meskipun terjadi error
        driver.quit()
        log(f"🏁 Total link terkumpul: {len(semua_link)}")

    return list(semua_link)