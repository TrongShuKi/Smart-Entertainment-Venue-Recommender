from pydantic import BaseModel
from typing import List

class Place(BaseModel):
    id: str
    name: str
    tag: str
    distance: float
    description: str
    fact: str

class SuggestionResponse(BaseModel):
    status: str
    message: str
    top_places: List[Place]