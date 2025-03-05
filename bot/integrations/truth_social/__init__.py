from truthbrush import api as truthbrush_api

from bot.common import void_logger

truthbrush_api.logger = void_logger.VoidLogger('void')
