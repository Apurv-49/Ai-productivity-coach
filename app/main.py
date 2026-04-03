from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
from app.env import FocusEnv
from app.agent import FocusAgent
from app.models import Observation

app = FastAPI(
    title="AI Productivity Coach",
    description="RL-based productivity coaching system",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

env = FocusEnv()
agent = FocusAgent()

@app.on_event("startup")
async def startup_event():
    try:
        if not os.path.exists("q_table.json"):
            print("No Q-table found. Training agent for 300 episodes...")
            agent.train(env, episodes=300)
            print("Training complete.")
        else:
            print("Q-table loaded. Agent ready.")
    except Exception as e:
        print(f"Startup warning: {e}")

app.mount("/static", StaticFiles(directory="app"), name="static")

@app.get("/", response_class=HTMLResponse)
def home():
    try:
        with open("app/index.html", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return HTMLResponse(content="""
            <html>
                <body style='font-family:sans-serif; padding:2rem; background:#0d0d0d; color:white;'>
                    <h2>🧠 AI Productivity Coach API</h2>
                    <p>Backend is running successfully.</p>
                    <p>Visit <a href='/docs' style='color:#a78bfa;'>/docs</a> for API reference.</p>
                </body>
            </html>
        """, status_code=200)

@app.get("/health")
def health():
    return {"status": "ok", "message": "AI Productivity Coach is running"}

@app.get("/reset")
def reset(task: str = "easy"):
    try:
        obs = env.reset(task)
        return {"state": obs.dict()}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ✅ NEW — required by OpenEnv spec
@app.get("/state")
def state():
    try:
        return {"state": env.state().dict()}
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/step_rl")
def step_rl(obs: Observation):
    try:
        action, _ = agent.decide(obs.dict(), training=False)
        next_state, reward, done, _ = env.step(action)
        return {
            "state": next_state.dict(),
            "reward": reward.value,
            "done": done
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

@app.post("/step")
def step(obs: Observation):
    try:
        action, reason = agent.decide(obs.dict(), training=False)
        return {
            "action": action.action,
            "target": action.target,
            "reason": reason
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

# ✅ UPDATED — per-task grader scores
@app.get("/score")
def score():
    try:
        agent.freeze()
        easy = env.grade(agent, "easy")
        medium = env.grade(agent, "medium")
        hard = env.grade(agent, "hard")

        overall = round((easy.score + medium.score + hard.score) / 3, 4)

        return {
            "overall_score": overall,
            "tasks": {
                "easy": easy.dict(),
                "medium": medium.dict(),
                "hard": hard.dict()
            }
        }
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})