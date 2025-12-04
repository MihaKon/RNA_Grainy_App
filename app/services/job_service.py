import uuid
import shutil
from pathlib import Path
from fastapi import HTTPException
from app.settings import TEMP_DIR


class JobManager:    
    @staticmethod
    def check_path(job_dir: str):
        if not job_dir.resolve().is_relative_to(TEMP_DIR.resolve()): 
            raise HTTPException(status_code=400, detail="Invalid job ID path.")

    @staticmethod
    def create_job_id() -> str:
        return str(uuid.uuid4())
    
    @classmethod
    def get_job_dir(cls, job_id: str) -> Path:
        try:
            uuid.UUID(job_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid job ID format")
        
        job_dir = TEMP_DIR / job_id

        cls.check_path(job_dir)
        return job_dir
    
    @classmethod
    def setup_job_dir(cls, job_id: str ) -> Path:
        job_dir = cls.get_job_dir(job_id)
        job_dir.mkdir(parents=True, exist_ok=True) 
        return job_dir   
    
    @classmethod
    def reconstruct_file_path(cls, job_id: str, filename:str)-> str:
        job_dir = cls.get_job_dir(job_id) 
        file_path = job_dir / filename
        return file_path
    
    @classmethod
    async def create_file(cls, job_id: str, content:str, filename:str) -> str:
        file_path = cls.reconstruct_file_path(job_id, filename)
        try:
            with open(file_path, "w",  encoding="utf-8") as f:
                f.write(content)
        except IOError as e:
            raise HTTPException(status_code=500, detail="File storage error.") 
        
        return file_path
    
    @classmethod
    def get_file_path(cls, job_id:str, filename:str) -> Path:
        file_path = cls.reconstruct_file_path(job_id, filename)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found.")

        cls.check_path(file_path)

        return file_path

    @classmethod
    def cleanup_job(cls, job_id: str):
        job_dir = cls.get_job_dir(job_id)
        if job_dir.exists():
            shutil.rmtree(job_dir)
