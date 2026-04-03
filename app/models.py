from pydantic import BaseModel
from typing import List

from pydantic import BaseModel, field_validator

class Observation(BaseModel):
    current_task: str
    focus_level: float
    fatigue: float
    distractions: List[str]
    time_spent: int
    deadline: int

    @field_validator("focus_level")
    def round_focus(cls, v):
        return round(v, 2)

class Action(BaseModel):
    action: str
    target: str = ""

class Reward(BaseModel):
    value: float