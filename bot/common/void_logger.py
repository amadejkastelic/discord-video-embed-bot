import logging


class VoidLogger(logging.Logger):
    def _log(self, *args, **kwargs):
        pass
