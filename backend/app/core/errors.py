class AppError(Exception):
    """Base application error."""

    def __init__(self, message: str, code: str = "internal_error") -> None:
        super().__init__(message)
        self.code = code
