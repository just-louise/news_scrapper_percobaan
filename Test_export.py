# test_export.py

from utils.logger import setup_logger
from utils.export_manager import export_to_csv, export_to_excel

setup_logger()

# Data dummy untuk test (nanti diganti data asli dari scraping)
dummy_articles = [
    {
        "title": "Judul Berita Pertama",
        "date": "2024-03-01",
        "content": "Ini adalah isi berita pertama yang sangat menarik...",
        "url": "https://example.com/berita-1"
    },
    {
        "title": "Judul Berita Kedua",
        "date": "2024-03-02",
        "content": "Ini adalah isi berita kedua yang tidak kalah menarik...",
        "url": "https://example.com/berita-2"
    },
    {
        "title": "Berita Teknologi Terbaru",
        "date": "2024-03-03",
        "content": "Perkembangan teknologi AI semakin pesat di tahun ini...",
        "url": "https://example.com/berita-teknologi"
    },
]

# Test export CSV
csv_path = export_to_csv(dummy_articles, "test_output.csv")
print(f"✅ CSV berhasil disimpan: {csv_path}")

# Test export Excel
xlsx_path = export_to_excel(dummy_articles, "test_output.xlsx")
print(f"✅ Excel berhasil disimpan: {xlsx_path}")

print("\n📂 Cek folder news_scrapper — seharusnya ada:")
print("   - test_output.csv")
print("   - test_output.xlsx")