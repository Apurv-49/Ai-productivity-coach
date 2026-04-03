from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agent import FocusAgent
from app.models import Observation, Action
from app.env import FocusEnv

app = FastAPI()

# 🔥 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

agent = FocusAgent()
env = FocusEnv()


@app.get("/")
def home():
    return {"message": "AI Productivity Coach API Running 🚀"}


# ==========================
# 🔥 RL SYSTEM (FIXED)
# ==========================

@app.post("/reset")
def reset_env():
    obs = env.reset()
    return {
        "state": obs.dict()
    }


@app.post("/step_rl")
def step_rl(action_data: dict):
    action_type = action_data.get("action")

    # 🔥 AUTO TARGET FIX (IMPORTANT)
    if action_type == "block_distraction":
        target = (
            env.state_data["distractions"][0]
            if env.state_data["distractions"]
            else ""
        )
        action = Action(action=action_type, target=target)
    else:
        action = Action(action=action_type)

    obs, reward, done, _ = env.step(action)

    return {
        "state": obs.dict(),
        "reward": reward.value,
        "done": done
    }


# ==========================
# 🔥 UI SYSTEM (UNCHANGED)
# ==========================

def generate_advice(action, state):
    fatigue = state["fatigue"]
    focus = state["focus_level"]
    distractions = state["distractions"]

    if action.action == "take_break":
        if fatigue > 0.7:
            return "You're highly fatigued. Take a longer break (10–15 mins)."
        return "You're getting tired. Take a short 5–10 minute break."

    elif action.action == "block_distraction":
        if len(distractions) > 1:
            return f"You have multiple distractions ({', '.join(distractions)}). Start by removing {distractions[0]}."
        return f"Remove distraction: {distractions[0]} to regain focus."

    elif action.action == "continue":
        if focus > 0.75:
            return "You're in deep focus. Keep going — this is peak productivity."
        return "You're doing fine. Try to increase focus slightly and continue."

    return "Stay consistent."


def get_confidence(state, action):
    fatigue = state["fatigue"]
    focus = state["focus_level"]
    distractions = len(state["distractions"])

    if action.action == "take_break":
        if fatigue > 0.7:
            return 0.9
        elif fatigue > 0.5:
            return 0.7
        else:
            return 0.4

    elif action.action == "block_distraction":
        if distractions >= 2:
            return 0.85
        elif distractions == 1:
            return 0.7
        else:
            return 0.3

    elif action.action == "continue":
        if focus > 0.75:
            return 0.9
        elif focus > 0.5:
            return 0.7
        else:
            return 0.5

    return 0.5


@app.post("/step")
def step(user_state: Observation):
    state = user_state.dict()

    action, reason = agent.decide(state, training=False)

    advice = generate_advice(action, state)
    confidence = get_confidence(state, action)

    return {
        "action": action.action,
        "target": action.target,
        "reason": reason,
        "advice": advice,
        "confidence": round(confidence, 2)
    }