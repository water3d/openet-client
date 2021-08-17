class AuthenticationError(PermissionError):
    pass


class BadRequestError(ValueError):
    pass


class RateLimitError(ValueError):
    pass

class FileRetrievalError(RuntimeError):
    pass