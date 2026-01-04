# Vision Module
#
# Teacher Note: This module contains all the "eyes" of the bot - the code that
# looks at screen pixels and extracts meaningful information from them.
#
# Components:
#   - HealthDetector: Detects health/energy bar fill percentage
#   - (future) InventoryDetector: Identifies items in inventory slots
#   - (future) TextReader: OCR for reading game text
#   - (future) TemplateMatatcher: Finds specific images on screen

from .health_detector import HealthDetector

__all__ = ['HealthDetector']
