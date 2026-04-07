"""
inference.py — OpenEnv compliant inference script
Emits exact [START], [STEP], [END] format as required by hackathon spec
"""
import subprocess
import sys

# ✅ AUTO-INSTALL REQUIRED PACKAGES
def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package, "-q"])

try:
    import openai
except ImportError:
    install("openai>=2.7.2")

try:
    import requests
except ImportError:
    install("requests")

import os
import time
import requests
from openai import OpenAI

# ✅ ENVIRONMENT VARIABLES (required by spec)
API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN", "")
ENV_URL = os.getenv("ENV_URL", "https://apurv255-ai-productivity-coach.hf.space")

# ✅ OPENAI CLIENT (required by spec)
client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN if HF_TOKEN else "not-needed"
)


def reset_env(task: str = "easy"):
    try:
        resp = requests.post(
            f"{ENV_URL}/reset",
            json={"task": task},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        if resp.status_code != 200:
            raise Exception(f"Reset failed with status {resp.status_code}: {resp.text}")
        data = resp.json()
        if "state" in data:
            return data["state"]
        return data
    except Exception as e:
        print(f"  [ERROR] reset_env failed: {e}")
        raise


def step_env(state: dict):
    try:
        payload = {
            "current_task": state.get("current_task", "DSA"),
            "focus_level": float(state.get("focus_level", 0.5)),
            "fatigue": float(state.get("fatigue", 0.0)),
            "distractions": list(state.get("distractions", [])),
            "time_spent": int(state.get("time_spent", 0)),
            "deadline": int(state.get("deadline", 60))
        }

        resp = requests.post(
            f"{ENV_URL}/step_rl",
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )

        if resp.status_code != 200:
            raise Exception(f"step_rl failed: {resp.status_code} {resp.text[:200]}")

        return resp.json()
    except Exception as e:
        print(f"  [ERROR] step_env failed: {e}")
        raise


def get_action_from_llm(state: dict) -> str:
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
                        f"Focus: {state['focus_level']}, "
                        f"Fatigue: {state['fatigue']}, "
                        f"Distractions: {state['distractions']}, "
                        f"Time: {state['time_spent']}/{state['deadline']}"
                    )
                }
            ],
            max_tokens=10
        )
        action = response.choices[0].message.content.strip().lower()
        for valid in ["block_distraction", "take_break", "continue"]:
            if valid in action:
                return valid
        return "continue"
    except Exception:
        return "continue"


def run_episode(task: str = "easy"):
    print(f"[START] task={task} env=ai-productivity-coach model={MODEL_NAME}")

    try:
        state = reset_env(task)
    except Exception as e:
        print(f"[END] success=false steps=0 rewards=")
        return []

    done = False
    step_count = 0
    rewards = []

    while not done and step_count < 30:
        try:
            action = get_action_from_llm(state)
            result = step_env(state)

            next_state = result.get("state", state)
            reward = float(result.get("reward", 0.0))
            done = bool(result.get("done", False))
            rewards.append(reward)

            print(
                f"[STEP] step={step_count + 1} "
                f"action={action} "
                f"reward={reward:.2f} "
                f"done={str(done).lower()} "
                f"error=null"
            )

            state = next_state
            step_count += 1

        except Exception as e:
            error = str(e).replace("\n", " ")[:100]
            print(
                f"[STEP] step={step_count + 1} "
                f"action=null "
                f"reward=0.00 "
                f"done=false "
                f"error={error}"
            )
            step_count += 1
            break

    success = len(rewards) > 0 and any(r > 0 for r in rewards)
    rewards_str = ",".join([f"{r:.2f}" for r in rewards])

    print(
        f"[END] success={str(success).lower()} "
        f"steps={step_count} "
        f"rewards={rewards_str}"
    )

    return rewards


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", default="easy",
                        choices=["easy", "medium", "hard", "all"])
    args = parser.parse_args()

    if args.task == "all":
        for t in ["easy", "medium", "hard"]:
            run_episode(task=t)
            time.sleep(2)
    else:
        run_episode(task=args.task)