from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.env import FocusEnv   # ✅ FIXED
from app.agent import QLearningAgent
from app.models import Observation

app = FastAPI()

env = FocusEnv()   # ✅ FIXED
agent = QLearningAgent()

# Serve static files (CSS, JS)
app.mount("/static", StaticFiles(directory="app"), name="static")

@app.get("/")
def home():
    return FileResponse("app/index.html")

@app.get("/reset")
def reset():
    return {"state": env.reset().dict()}

@app.post("/step_rl")
def step_rl(obs: Observation):
    action = agent.choose_action(obs.dict())
    next_state, reward, done, _ = env.step(action)

    return {
        "state": next_state.dict(),
        "reward": reward.value,
        "done": done
    }

@app.post("/step")
def step(obs: Observation):
    action = agent.choose_action(obs.dict())
    return {"action": action}