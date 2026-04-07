from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from app.env import ProductivityEnv
import uvicorn

app = FastAPI()
env = ProductivityEnv()

class ResetRequest(BaseModel):
    task: str = "easy"

class StepRequest(BaseModel):
    action: str
    focus_level: float = 0.5
    fatigue: float = 0.1
    distractions: list = []
    time_spent: int = 0
    deadline: int = 60

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/reset")
def reset(body: ResetRequest):
    state = env.reset(task=body.task)
    return {"state": state}

@app.post("/step_rl")
def step_rl(body: StepRequest):
    state = body.dict()
    action = state.pop("action")
    next_state, reward, done = env.step(action, state)
    return {"state": next_state, "reward": reward, "done": done}

@app.get("/score")
def score():
    return {"score": env.get_score()}

# Serve frontend
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.get("/")
def root():
    return FileResponse("app/static/index.html")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)