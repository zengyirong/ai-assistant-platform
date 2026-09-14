"""Parser-layer errors (avoid circular imports with job.pipeline)."""


class DocumentParseError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)
