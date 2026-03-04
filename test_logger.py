# test_logger.py

from utils.logger import setup_logger
import logging

# Setup logger
setup_logger()

# Buat logger khusus untuk file ini
logger = logging.getLogger(__name__)

# Coba semua level
logger.debug("Ini pesan DEBUG — hanya muncul di file log")
logger.info("Ini pesan INFO — muncul di terminal dan file")
logger.warning("Ini pesan WARNING — ada yang perlu diperhatikan")
logger.error("Ini pesan ERROR — ada yang gagal")

print("\n✅ Cek folder logs/ — seharusnya ada file .log baru!")