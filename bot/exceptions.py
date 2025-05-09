class BaseError(Exception):
    pass


class RepositoryError(BaseError):
    def __init__(self, error: str) -> None:
        super().__init__(f'Database error: {error}')


class IntegrationClientError(BaseError):
    def __init__(self, error: str) -> None:
        super().__init__(f'Site scraper/client error: {error}')


class NotAllowedError(BaseError):
    def __init__(self, action: str) -> None:
        super().__init__(f'Action not allowed: {action}')


class NotSupportedError(BaseError):
    def __init__(self, action: str) -> None:
        super().__init__(f'Action not supported: {action}')


class IntegrationError(BaseError):
    def __init__(self, error: str) -> None:
        super().__init__(f'Integration error: {error}')
        self.error = error


class ConfigurationError(BaseError):
    pass


class BotError(BaseError):
    pass
