from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from app.env import ProductivityEnv
from app.agent import QLearningAgent
from app.models import State

app = FastAPI()

env = ProductivityEnv()
agent = QLearningAgent()

# Serve static files (CSS, JS)
app.mount("/static", StaticFiles(directory="app"), name="static")

@app.get("/")
def home():
    return FileResponse("app/index.html")

@app.post("/reset")
def reset(state: State):
    return env.reset(state.dict())

@app.post("/step_rl")
def step_rl(state: State):
    action = agent.choose_action(state.dict())
    next_state, reward, done = env.step(action)
    return {
        "state": next_state,
        "reward": reward,
        "done": done
    }

@app.post("/step")
def step(state: State):
    action = agent.choose_action(state.dict())
    return {"action": action}