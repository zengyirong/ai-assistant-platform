"""Job / pipeline error types."""


class PipelineError(Exception):
    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(message)


# Back-compat alias
ParseError = PipelineError
