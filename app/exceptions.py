from fastapi import HTTPException


class ValidationError(HTTPException):
    def __init__(self, detail: str, status_code: int = 400):
        super().__init__(status_code=status_code, detail=detail)

class FileProcessingError(ValidationError):
    def __init__(self, detail: str):
        super().__init__(detail, status_code=422)

class DamagedFileError(ValidationError):
    def __init__(self, detail: str):
        super().__init__(detail, status_code=400)