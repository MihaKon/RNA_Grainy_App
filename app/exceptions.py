class ValidationError(Exception):
    pass

class FileProcessingError(ValidationError):
    pass

class ModelLoadingError(ValidationError):
    pass

class JobError(Exception):
    pass