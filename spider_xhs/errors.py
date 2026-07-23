class XhsApiError(RuntimeError):
    """Raised when a Spider_XHS facade call reports failure."""

    def __init__(self, operation, message, code=None, response=None):
        self.operation = operation
        self.message = str(message)
        self.code = code
        self.response = response
        has_code = code is not None and f"code={code}" in self.message
        code_text = f" code={code}" if code is not None and not has_code else ""
        super().__init__(f"{operation} failed:{code_text} {self.message}")
