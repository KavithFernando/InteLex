from typing import List, Optional

from pydantic import BaseModel


class IngestJobResponse(BaseModel):
    job_id: str
    status: str
    submitted_at: str
    filenames: List[str]
    clauses: Optional[List[str]]
    log: List[str]
    frames_created: int
    frames_skipped: int
    errors: int
    error: Optional[str]
