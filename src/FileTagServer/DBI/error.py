from dataclasses import dataclass
from typing import Optional


@dataclass
class ApiError(Exception):
    status_code: Optional[int] = 500
    message: Optional[str] = None
