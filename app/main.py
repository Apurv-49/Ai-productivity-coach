from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional

from app.env import ProductivityEnv
from app.models import Action
from app.agent import FocusAgent

import uvicorn
import os


# --------------------------------------------------
# APP INITIALIZATION
# --------------------------------------------------

app = FastAPI(title="AI Productivity Coach")

env = ProductivityEnv()
agent = FocusAgent()


# --------------------------------------------------
# REQUEST MODELS
# --------------------------------------------------

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


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/health")
def health():
    return {
        "status": "ok"
    }


# --------------------------------------------------
# RESET ENVIRONMENT
# --------------------------------------------------

@app.post("/reset")
def reset(body: ResetRequest):

    try:
        state = env.reset(
            task_type=body.task_type
        )

        return {
            "state": state.dict()
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# --------------------------------------------------
# MANUAL RL STEP
# --------------------------------------------------

@app.post("/step_rl")
def step_rl(body: StepRequest):

    action = Action(
        action=body.action,
        target=body.target
    )

    try:

        next_obs, reward, done, _ = env.step(
            action
        )

    except Exception as e:

        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    return {
        "state": next_obs.dict(),
        "reward": reward.value,
        "done": done
    }


# --------------------------------------------------
# AI PRODUCTIVITY ADVICE
# --------------------------------------------------

@app.post("/step")
def step_advice(body: AdviceRequest):
    """
    Uses the trained Q-learning agent to choose
    the best productivity action for the current state.
    """

    # Create state dictionary in the same format
    # expected by FocusAgent.get_state_key()
    state = {
        "focus_level": body.focus_level,
        "fatigue": body.fatigue,
        "distractions": body.distractions,
        "time_spent": body.time_spent,
        "deadline": max(body.deadline, 1)
    }

    try:

        # Use learned Q-table policy
        action, reason = agent.decide(
            state,
            training=False
        )

        action_type = action.action

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}"
        )


    # --------------------------------------------------
    # GENERATE HUMAN-READABLE ADVICE
    # --------------------------------------------------

    if action_type == "take_break":

        advice = (
            f"Your fatigue is currently "
            f"{body.fatigue:.2f}. "
            "Take a short 5–10 minute break "
            "to restore your focus."
        )


    elif action_type == "block_distraction":

        if body.distractions:

            target = body.distractions[0]

        else:

            target = action.target or "your distractions"

        advice = (
            f'"{target}" is affecting your focus. '
            "Block this distraction and return "
            "to your task."
        )


    else:

        advice = (
            f"Your focus is currently "
            f"{body.focus_level:.2f}. "
            "You're in a good state to continue "
            "working."
        )


    # --------------------------------------------------
    # CONFIDENCE ESTIMATION
    # --------------------------------------------------

    confidence_base = (
        body.focus_level * 0.6
        - body.fatigue * 0.3
        - len(body.distractions) * 0.05
    )

    confidence = max(
        0.4,
        min(
            0.99,
            confidence_base + 0.5
        )
    )


    return {
        "advice": advice,
        "suggested_action": action_type,
        "action": action_type,
        "reason": reason,
        "current_focus": body.focus_level,
        "current_fatigue": body.fatigue,
        "confidence": round(confidence, 2)
    }


# --------------------------------------------------
# SCORE
# --------------------------------------------------

@app.get("/score")
def score():

    try:

        return agent.get_score(env)

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=f"Scoring error: {str(e)}"
        )


# --------------------------------------------------
# SERVE FRONTEND
# --------------------------------------------------

APP_DIR = os.path.dirname(
    os.path.abspath(__file__)
)


app.mount(
    "/static",
    StaticFiles(
        directory=APP_DIR
    ),
    name="static"
)


@app.get("/")
def root():

    index_file = os.path.join(
        APP_DIR,
        "index.html"
    )

    if os.path.exists(index_file):

        return FileResponse(
            index_file
        )

    return {
        "message":
        "AI Productivity Coach API is running!"
    }


# --------------------------------------------------
# RUN SERVER
# --------------------------------------------------

if __name__ == "__main__":

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=7860
    )
