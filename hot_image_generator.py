"""
Модуль-заглушка. Генерация Hot Pics отключена.
"""

import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class HotImageGenerator:
    """Заглушка для генерации Hot Pics (функционал отключён)"""
    def __init__(self):
        pass
    async def load_model(self):
        logger.info("Генерация изображений отключена.")
        return
