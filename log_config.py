import logging

# Настраиваем логгер
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('latest.log', encoding='utf-8')
    ]
)

logger = logging.getLogger()