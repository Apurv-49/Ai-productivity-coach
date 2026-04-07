from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from app.env import ProductivityEnv
from app.models import Action
import uvicorn
import os

app = FastAPI(title="AI Productivity Coach")
env = ProductivityEnv()


class ResetRequest(BaseModel):
    task_type: str = "easy"


class StepRequest(BaseModel):
    action: str
    target: Optional[str] = None


class AdviceRequest(BaseModel):
    focus_level: float = 0.5
    fatigue: float = 0.1
    distractions: List[str] = []
    time_spent: int = 0
    deadline: int = 60


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/reset")
def reset(body: ResetRequest):
    state = env.reset(task_type=body.task_type)
    return {"state": state.dict()}


@app.post("/step_rl")
def step_rl(body: StepRequest):
    action = Action(action=body.action, target=body.target)
    try:
        next_obs, reward, done, _ = env.step(action)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    return {
        "state": next_obs.dict(),
        "reward": reward.value,
        "done": done
    }


@app.post("/step")
def step_advice(body: AdviceRequest):
    """UI-friendly endpoint: takes raw state values, returns AI advice."""
    focus = body.focus_level
    fatigue = body.fatigue
    distractions = body.distractions

    # Simple rule-based advice (no agent needed)
    if fatigue > 0.6:
        advice = "Take a break — your fatigue is high."
        suggested_action = "take_break"
    elif len(distractions) > 0:
        advice = f"Block distractions: {', '.join(distractions)}"
        suggested_action = "block_distraction"
    elif focus < 0.4:
        advice = "Take a short break to restore focus."
        suggested_action = "take_break"
    else:
        advice = "You're in a good state — keep working!"
        suggested_action = "continue"

    return {
        "advice": advice,
        "suggested_action": suggested_action,
        "current_focus": focus,
        "current_fatigue": fatigue
    }


@app.get("/score")
def score():
    return {"score": env.get_score()}


# Serve frontend static files if they exist
static_dir = "app/static"
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    @app.get("/")
    def root():
        index = os.path.join(static_dir, "index.html")
        if os.path.exists(index):
            return FileResponse(index)
        return {"message": "AI Productivity Coach API is running!"}
else:
    @app.get("/")
    def root():
        return {"message": "AI Productivity Coach API is running!"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)