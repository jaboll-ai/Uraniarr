class BaseError(Exception):
    def __init__(self, status_code = 404, detail = ""):
        super().__init__(detail)
        self.type = self.__class__.__name__
        self.status_code = status_code
        self.detail = detail

class ScrapeError(BaseError):
    pass

class AuthorError(BaseError):
    pass

class NzbsError(BaseError):
    pass

class FileError(BaseError):
    pass

class IndexerError(BaseError):
    pass