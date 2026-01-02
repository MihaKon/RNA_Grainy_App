import uuid
import shutil
from pathlib import Path
from app.exceptions import ValidationError, FileProcessingError
from app.settings import TEMP_DIR


class JobManager:    
    @staticmethod
    def check_path(job_dir: Path) -> None:
        if not job_dir.resolve().is_relative_to(TEMP_DIR.resolve()): 
            raise ValidationError("Invalid job directory path.")

    @staticmethod
    def create_job_id() -> str:
        return str(uuid.uuid4())
    
    @classmethod
    def get_job_dir(cls, job_id: str) -> Path:
        try:
            uuid.UUID(job_id)
        except ValueError:
            raise ValidationError("Invalid job ID format.")
        
        job_dir = TEMP_DIR / job_id

        cls.check_path(job_dir)
        return job_dir
    
    @classmethod
    def setup_job_dir(cls, job_id: str ) -> Path:
        job_dir = cls.get_job_dir(job_id)
        job_dir.mkdir(parents=True, exist_ok=True) 
        return job_dir   
    
    @classmethod
    def reconstruct_file_path(cls, job_id: str, filename:str)-> Path:
        job_dir = cls.get_job_dir(job_id) 
        file_path = job_dir / filename
        return file_path
    
    @classmethod
    async def create_file(cls, job_id: str, content:str, filename:str) -> Path:
        file_path = cls.reconstruct_file_path(job_id, filename)
        try:
            with open(file_path, "w",  encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            raise FileProcessingError(f"Error creating file: {e}")
        
        return file_path
    
    @classmethod
    def get_file_path(cls, job_id:str, filename:str) -> Path:
        file_path = cls.reconstruct_file_path(job_id, filename)
        if not file_path.exists():
            raise FileProcessingError("Requested file does not exist.")

        cls.check_path(file_path)

        return file_path

    @classmethod
    def cleanup_job(cls, job_id: str) -> None:
        job_dir = cls.get_job_dir(job_id)
        if job_dir.exists():
            shutil.rmtree(job_dir)
