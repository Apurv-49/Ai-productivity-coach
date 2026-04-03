from pydantic import BaseModel, field_validator
from typing import List, Dict

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

class TaskScore(BaseModel):
    task: str
    score: float
    grade: str
    avg_focus: float
    total_reward: float
    steps: int

class EpisodeScore(BaseModel):
    overall_score: float
    tasks: Dict[str, TaskScore]