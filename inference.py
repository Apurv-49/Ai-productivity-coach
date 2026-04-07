import requests
import os
import time

API_BASE_URL = os.getenv("API_BASE_URL", "https://router.huggingface.co/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "Qwen/Qwen2.5-72B-Instruct")
HF_TOKEN = os.getenv("HF_TOKEN", "")
ENV_URL = os.getenv("ENV_URL", "https://apurv255-ai-productivity-coach.hf.space")


def reset_env(task="easy"):
    resp = requests.post(f"{ENV_URL}/reset", json={"task": task}, timeout=30)
    resp.raise_for_status()
    data = resp.json()
    return data.get("state", data)


def step_env(state):
    resp = requests.post(f"{ENV_URL}/step_rl", json=state, timeout=30)
    resp.raise_for_status()
    return resp.json()


def get_action_from_llm(state):
    try:
        response = requests.post(
            f"{API_BASE_URL}/chat/completions",
            headers={
                "Authorization": f"Bearer {HF_TOKEN}",
                "Content-Type": "application/json"
            },
            json={
                "model": MODEL_NAME,
                "messages": [
                    {
                        "role": "system",
                        "content": "Reply ONLY: continue, take_break, block_distraction"
                    },
                    {
                        "role": "user",
                        "content": str(state)
                    }
                ],
                "max_tokens": 10
            },
            timeout=30
        )

        data = response.json()
        action = data["choices"][0]["message"]["content"].lower()

        for a in ["continue", "take_break", "block_distraction"]:
            if a in action:
                return a

        return "continue"

    except Exception:
        return "continue"


def run_episode(task="easy"):
    print(f"[START] task={task}")

    try:
        state = reset_env(task)
    except Exception:
        print("[END] success=false steps=0 rewards=")
        return

    done = False
    step = 0
    rewards = []

    while not done and step < 30:
        try:
            action = get_action_from_llm(state)
            result = step_env(state)

            state = result.get("state", state)
            reward = float(result.get("reward", 0))
            done = result.get("done", False)

            rewards.append(reward)

            print(f"[STEP] step={step+1} action={action} reward={reward:.2f} done={done} error=null")

            step += 1

        except Exception as e:
            print(f"[STEP] step={step+1} action=null reward=0 done=false error={str(e)[:50]}")
            break

    success = any(r > 0 for r in rewards)
    rewards_str = ",".join([f"{r:.2f}" for r in rewards])

    print(f"[END] success={str(success).lower()} steps={step} rewards={rewards_str}")


if __name__ == "__main__":
    run_episode()