# scraper/article_parser.py

import time
import logging
from datetime import datetime

from newspaper import Article
from newspaper.article import ArticleException

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)


# =====================================================
# BAGIAN 1: Buat WebDriver (sama seperti link_collector)
# =====================================================

def buat_driver(headless=True):
    """Membuat instance WebDriver Chrome."""
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    )
    options.add_argument("--disable-notifications")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option("useAutomationExtension", False)

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.execute_script(
        "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    )
    return driver


# =====================================================
# BAGIAN 2: Strategi 1 — newspaper3k
# =====================================================

def parse_dengan_newspaper(url):
    """
    Mengambil konten artikel menggunakan library newspaper3k.

    newspaper3k secara otomatis mengenali:
    - Judul artikel
    - Tanggal publikasi
    - Isi berita (sudah dibersihkan dari iklan/menu)
    - Penulis

    Return: dict artikel atau None jika gagal
    """
    try:
        # Buat objek Article
        # language='id' → optimasi untuk bahasa Indonesia
        article = Article(url, language='id')

        # Download HTML halaman
        article.download()

        # Parse HTML → ekstrak komponen artikel
        article.parse()

        # Ambil data
        title   = article.title.strip() if article.title else ""
        content = article.text.strip()  if article.text  else ""
        date    = article.publish_date  # datetime object atau None

        # =====================================================
        # VALIDASI: Data harus valid dan tidak kosong
        # =====================================================
        if not title:
            logger.debug(f"newspaper3k: judul kosong untuk {url}")
            return None

        if not content or len(content) < 100:
            logger.debug(f"newspaper3k: konten terlalu pendek untuk {url}")
            return None

        # Format tanggal
        if date:
            tanggal_str = date.strftime("%Y-%m-%d")
        else:
            tanggal_str = "Tidak diketahui"

        # Potong konten jika terlalu panjang (tampilkan 800 karakter)
        konten_pendek = content[:800] + "..." if len(content) > 800 else content

        logger.info(f"✅ newspaper3k berhasil: {title[:50]}...")
        return {
            "title"  : title,
            "date"   : tanggal_str,
            "content": konten_pendek,
            "url"    : url
        }

    except ArticleException as e:
        logger.debug(f"newspaper3k ArticleException untuk {url}: {e}")
        return None
    except Exception as e:
        logger.debug(f"newspaper3k gagal untuk {url}: {e}")
        return None


# =====================================================
# BAGIAN 3: Helper untuk Selenium Manual
# =====================================================

def ekstrak_judul(driver):
    """
    Coba berbagai cara untuk menemukan judul artikel.
    Urutan: dari yang paling spesifik ke paling umum.
    """

    # Cara 1: Cari tag <h1> (paling umum untuk judul artikel)
    try:
        h1_elements = driver.find_elements(By.TAG_NAME, "h1")
        for h1 in h1_elements:
            text = h1.text.strip()
            if len(text) > 10:  # Judul yang valid minimal 10 karakter
                return text
    except Exception:
        pass

    # Cara 2: Meta tag og:title (Open Graph)
    # Banyak website pakai ini untuk SEO
    try:
        meta = driver.find_element(
            By.XPATH, "//meta[@property='og:title']"
        )
        content = meta.get_attribute("content")
        if content and len(content) > 10:
            return content.strip()
    except Exception:
        pass

    # Cara 3: Tag <title> di halaman
    try:
        title = driver.title
        if title and len(title) > 10:
            # Hapus nama website dari judul
            # Contoh: "Judul Berita | Detik.com" → "Judul Berita"
            if "|" in title:
                title = title.split("|")[0].strip()
            elif "-" in title:
                title = title.split("-")[0].strip()
            return title
    except Exception:
        pass

    return ""


def ekstrak_tanggal(driver):
    """
    Coba berbagai cara untuk menemukan tanggal publikasi.
    """

    # Cara 1: Tag <time> (standar HTML5)
    try:
        time_el = driver.find_element(By.TAG_NAME, "time")
        # Prioritaskan attribute datetime (lebih akurat)
        dt = time_el.get_attribute("datetime")
        if dt:
            return dt.strip()
        # Fallback ke teks yang tampil
        if time_el.text.strip():
            return time_el.text.strip()
    except Exception:
        pass

    # Cara 2: Meta tag article:published_time
    try:
        meta = driver.find_element(
            By.XPATH, "//meta[@property='article:published_time']"
        )
        content = meta.get_attribute("content")
        if content:
            return content.strip()
    except Exception:
        pass

    # Cara 3: Elemen dengan class/id yang mengandung kata "date" atau "time"
    pola_tanggal = [
        "//*[contains(@class,'date')]",
        "//*[contains(@class,'time')]",
        "//*[contains(@class,'publish')]",
        "//*[contains(@class,'posted')]",
        "//*[contains(@class,'created')]",
        "//*[contains(@id,'date')]",
        "//*[contains(@itemprop,'datePublished')]",
    ]

    for pola in pola_tanggal:
        try:
            el = driver.find_element(By.XPATH, pola)
            # Cek attribute datetime dulu
            dt = el.get_attribute("datetime") or el.get_attribute("content")
            if dt and len(dt) > 5:
                return dt.strip()
            # Cek teks
            if el.text and len(el.text.strip()) > 5:
                return el.text.strip()
        except Exception:
            continue

    return "Tidak diketahui"


def ekstrak_konten(driver):
    """
    Ambil isi artikel dengan mencari container konten utama.
    Strategi: cari elemen yang mengandung paragraf terbanyak.
    """

    # Cara 1: Tag <article> (standar HTML5 untuk artikel)
    try:
        article = driver.find_element(By.TAG_NAME, "article")
        paragraphs = article.find_elements(By.TAG_NAME, "p")
        teks = " ".join([p.text for p in paragraphs if len(p.text.strip()) > 20])
        if len(teks) > 200:
            return teks
    except Exception:
        pass

    # Cara 2: Cari div dengan class yang mengandung kata konten
    pola_konten = [
        "//div[contains(@class,'detail-text')]",
        "//div[contains(@class,'article-body')]",
        "//div[contains(@class,'article-content')]",
        "//div[contains(@class,'post-content')]",
        "//div[contains(@class,'entry-content')]",
        "//div[contains(@class,'content-detail')]",
        "//div[contains(@class,'news-content')]",
        "//div[contains(@class,'read-page')]",
        "//div[contains(@class,'detail__body')]",
        "//div[contains(@class,'itp_bodycontent')]",
    ]

    for pola in pola_konten:
        try:
            container = driver.find_element(By.XPATH, pola)
            paragraphs = container.find_elements(By.TAG_NAME, "p")
            teks = " ".join([p.text for p in paragraphs if len(p.text.strip()) > 20])
            if len(teks) > 200:
                return teks
        except Exception:
            continue

    # Cara 3 (Fallback): Ambil SEMUA <p> di halaman
    # Pilih paragraf yang cukup panjang (bukan menu/footer)
    try:
        semua_p = driver.find_elements(By.TAG_NAME, "p")
        teks = " ".join([
            p.text for p in semua_p
            if len(p.text.strip()) > 50  # Filter paragraf pendek
        ])
        if len(teks) > 200:
            return teks
    except Exception:
        pass

    return ""


# =====================================================
# BAGIAN 4: Strategi 2 — Selenium Manual
# =====================================================

def parse_dengan_selenium(url, delay=1):
    """
    Fallback: Ambil konten artikel menggunakan Selenium secara manual.
    Digunakan ketika newspaper3k gagal.

    Return: dict artikel atau None jika gagal
    """
    driver = buat_driver(headless=True)

    try:
        logger.info(f"🔄 Mencoba Selenium manual: {url[:60]}...")

        # Buka halaman
        driver.get(url)

        # Tunggu halaman dimuat
        try:
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        except TimeoutException:
            logger.warning(f"Timeout saat membuka: {url}")

        time.sleep(delay)

        # Ekstrak komponen
        title   = ekstrak_judul(driver)
        date    = ekstrak_tanggal(driver)
        content = ekstrak_konten(driver)

        # Validasi
        if not title or not content or len(content) < 100:
            logger.warning(f"Selenium: data tidak valid untuk {url}")
            return None

        # Potong konten
        konten_pendek = content[:800] + "..." if len(content) > 800 else content

        logger.info(f"✅ Selenium berhasil: {title[:50]}...")
        return {
            "title"  : title,
            "date"   : date,
            "content": konten_pendek,
            "url"    : url
        }

    except WebDriverException as e:
        logger.error(f"WebDriver error untuk {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error tidak terduga untuk {url}: {e}")
        return None
    finally:
        driver.quit()


# =====================================================
# BAGIAN 5: Fungsi Utama — Parse Satu Artikel
# =====================================================

def parse_artikel(url, delay=1):
    """
    Fungsi utama: ambil konten satu artikel dari URL.

    Alur:
    1. Coba dengan newspaper3k (cepat, otomatis)
    2. Jika gagal → coba dengan Selenium manual (lebih lambat, lebih andal)
    3. Jika keduanya gagal → return None

    Parameter:
    - url   : URL artikel yang akan di-parse
    - delay : jeda sebelum scraping (detik)

    Return: dict {title, date, content, url} atau None jika gagal
    """
    logger.info(f"📰 Memproses: {url[:70]}...")

    # === STRATEGI 1: newspaper3k ===
    hasil = parse_dengan_newspaper(url)
    if hasil:
        return hasil

    logger.info(f"⚠️ newspaper3k gagal, mencoba Selenium...")

    # === STRATEGI 2: Selenium manual ===
    hasil = parse_dengan_selenium(url, delay)
    if hasil:
        return hasil

    logger.warning(f"❌ Kedua strategi gagal untuk: {url}")
    return None