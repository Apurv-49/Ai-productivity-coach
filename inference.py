"""
inference.py — OpenEnv compliant inference script
Uses OpenAI client with API_BASE_URL, MODEL_NAME, HF_TOKEN from env vars
Emits [START], [STEP], [END] logs as required by hackathon spec
"""
import os
import json
import time
import requests
from openai import OpenAI

# ✅ READ FROM ENVIRONMENT VARIABLES (required by spec)
API_BASE_URL = os.environ.get("API_BASE_URL", "http://localhost:8000")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.environ.get("HF_TOKEN", "")

# ✅ OPENAI CLIENT (required by spec)
client = OpenAI(
    base_url=f"{API_BASE_URL}/v1" if not API_BASE_URL.endswith("/v1") else API_BASE_URL,
    api_key=HF_TOKEN if HF_TOKEN else "not-needed"
)

ENV_URL = os.environ.get("ENV_URL", "https://apurv255-ai-productivity-coach.hf.space")


def reset_env(task: str = "easy"):
    try:
        resp = requests.get(f"{ENV_URL}/reset", params={"task": task})
        
        data = resp.json()
        if "state" in data:
            return data["state"]
        elif "error" in data:
            raise Exception(f"Server error: {data['error']}")
        return data
    except Exception as e:
        print(f"[ERROR] reset_env failed: {e}")
        raise


def step_env(state: dict):
    try:
        resp = requests.post(
            f"{ENV_URL}/step_rl",
            json=state,
            headers={"Content-Type": "application/json"}
        )
        
        data = resp.json()
        return data
    except Exception as e:
        print(f"[ERROR] step_env failed: {e}")
        raise


def get_score():
    try:
        resp = requests.get(f"{ENV_URL}/score")
        return resp.json()
    except Exception as e:
        print(f"[ERROR] get_score failed: {e}")
        return {"overall_score": 0, "tasks": {}}


def get_action_from_llm(state: dict) -> str:
    """Use OpenAI client to get action from LLM."""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a productivity coach AI agent. "
                        "Given the current state, choose the best action. "
                        "Reply with ONLY one of: continue, take_break, block_distraction"
                    )
                },
                {
                    "role": "user",
                    "content": (
                        f"Current state:\n"
                        f"- Focus level: {state['focus_level']}\n"
                        f"- Fatigue: {state['fatigue']}\n"
                        f"- Distractions: {state['distractions']}\n"
                        f"- Time spent: {state['time_spent']}/{state['deadline']}\n"
                        f"What action should the agent take?"
                    )
                }
            ],
            max_tokens=10
        )
        action = response.choices[0].message.content.strip().lower()
        if action not in ["continue", "take_break", "block_distraction"]:
            action = "continue"
        return action
    except Exception:
        # fallback to RL agent if LLM unavailable
        return None


def run_episode(task: str = "easy"):
    print("[START]")
    print(json.dumps({
        "task": task,
        "model": MODEL_NAME,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
    }))

    state = reset_env(task)
    done = False
    step_count = 0
    total_reward = 0

    while not done and step_count < 30:
        # try LLM first, fallback to RL agent
        llm_action = get_action_from_llm(state)

        # build step input — always send full state
        step_input = dict(state)
        if llm_action:
            step_input["action"] = llm_action

        result = step_env(state)

        next_state = result.get("state", state)
        reward = result.get("reward", 0)
        done = result.get("done", False)
        total_reward += reward

        print("[STEP]")
        print(json.dumps({
            "step": step_count,
            "action": llm_action or "rl_agent",
            "reward": round(reward, 4),
            "done": done,
            "state": next_state
        }))

        state = next_state
        step_count += 1
        time.sleep(0.1)

    score = get_score()

    print("[END]")
    print(json.dumps({
        "task": task,
        "total_steps": step_count,
        "total_reward": round(total_reward, 4),
        "scores": score
    }))

    return score


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", default="easy",
                        choices=["easy", "medium", "hard", "all"])
    args = parser.parse_args()

    if args.task == "all":
        for t in ["easy", "medium", "hard"]:
            print(f"\n{'='*40}")
            print(f"Running task: {t.upper()}")
            print(f"{'='*40}")
            run_episode(task=t)
            time.sleep(1)
    else:
        run_episode(task=args.task)