import logging

import structlog

# Don't allow libraries to use a logger
logging.basicConfig = lambda **kwargs: None

logger: logging.Logger = structlog.get_logger(__name__)
