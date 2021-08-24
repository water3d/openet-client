class DataProcessingError(RuntimeError):
    def __init__(self, text, data=None):
        self.text = text
        self.data = data

    def __str__(self):
        return self.text

    def __repr__(self):
        return self.text


class AuthenticationError(PermissionError):
    pass


class BadRequestError(ValueError):
    pass


class RateLimitError(DataProcessingError):
    pass

class FileRetrievalError(RuntimeError):
    pass