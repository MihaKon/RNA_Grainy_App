import uuid
import shutil
import logging
from pathlib import Path
from fastapi import HTTPException
from app.settings import TEMP_DIR

logger = logging.getLogger(__name__)

class JobManager:
    @staticmethod
    def create_job_id() -> str:
        return str(uuid.uuid4())
    
    @staticmethod
    def get_job_dir(job_id: str) -> Path:
        job_dir = TEMP_DIR / job_id
        if not job_dir.resolve().is_relative_to(TEMP_DIR.resolve()): #path traversal
            raise HTTPException(status_code=400, detail="Invalid job ID path.")

    @classmethod
    def setup_job_dir(cls, job_id: str ) -> Path:
        job_dir = cls.get_job_dir(job_id)
        job_dir.mkdir(parents=True, exist_ok=True) #
        return job_dir   
    
    @classmethod
    def create_file(cls, job_id: str, content:str, filename:str) -> str:
        job_dir = cls.get_job_dir(job_id) 
        file_path = job_dir / filename
        try:
            with open(file_path, "w",  encoding="utf-8") as f: # check aioflies
                f.write(content)
        except IOError as e:
            logger.error(f"Failed to write file for job {job_id}: {e}")
            raise HTTPException(status_code=500, detail="File storage error.") 
        return file_path
    
    @classmethod
    def get_file_path(cls, job_id:str, filename:str) -> Path:
        job_dir = cls.get_job_dir(job_id)
        file_path = job_dir / filename
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found.")

        if not file_path.resolve().is_relative_to(job_dir.resolve()): #path traversal
            raise HTTPException(status_code=403, detail="Access denied.")

        return file_path

    @classmethod
    def cleanup_job(cls, job_id: str):
        job_dir = cls.get_job_dir(job_id)
        if job_dir.exists():
            shutil.rmtree(job_dir)
            logger.info(f"Cleaned up job {job_id}")        