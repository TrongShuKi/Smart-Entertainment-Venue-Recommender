from pydantic import BaseModel
from typing import Optional, List

class SuggestionRequest(BaseModel):
    query: str
    location: Optional[List[float]] = None # [latitude, longitude]