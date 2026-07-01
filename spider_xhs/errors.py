class XhsApiError(RuntimeError):
    """Raised when a Spider_XHS facade call reports failure."""

    def __init__(self, operation, message):
        self.operation = operation
        self.message = str(message)
        super().__init__(f"{operation} failed: {self.message}")
