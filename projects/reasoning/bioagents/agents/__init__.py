from loguru import logger
import sys

# Configure logger
logger.remove()
logger.add(
    sink=sys.stderr,
    format=(
        "<green>{time:HH:mm:ss}</green>|" 
        "<cyan>{name}</cyan>:<bold><yellow>{function}</yellow></bold>:" 
        "<cyan>{line}</cyan>-<white>{message}</white>"),
)
