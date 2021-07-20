class AuthenticationError(PermissionError):
    pass

class BadRequestError(ValueError):
    pass

class FileRetrievalError(RuntimeError):
    pass