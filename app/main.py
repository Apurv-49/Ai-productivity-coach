from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from app.env import FocusEnv
from app.agent import FocusAgent
from app.models import Observation

app = FastAPI()

env = FocusEnv()
agent = FocusAgent()

# Serve static files (CSS, JS)
app.mount("/static", StaticFiles(directory="app"), name="static")

@app.get("/", response_class=HTMLResponse)
def home():
    with open("app/index.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/reset")
def reset():
    return {"state": env.reset().dict()}

@app.post("/step_rl")
def step_rl(obs: Observation):
    action, _ = agent.decide(obs.dict(), training=False)
    next_state, reward, done, _ = env.step(action)

    return {
        "state": next_state.dict(),
        "reward": reward.value,
        "done": done
    }

@app.post("/step")
def step(obs: Observation):
    action, reason = agent.decide(obs.dict(), training=False)

    return {
        "action": action.action,
        "target": action.target,
        "reason": reason
    }