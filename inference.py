import requests
import time
from app.agent import FocusAgent

BASE_URL = "http://localhost:8000"

# 🔥 LOAD TRAINED AGENT
agent = FocusAgent()
agent.freeze()  # minimal exploration


def reset_env():
    return requests.post(f"{BASE_URL}/reset").json()


def step_env(action):
    return requests.post(
        f"{BASE_URL}/step_rl",
        json={"action": action}
    ).json()


def run_episode():
    print("[START] Running episode...")

    state = reset_env()["state"]
    done = False
    step_count = 0

    while not done:
        # 🔥 USE RL POLICY (IMPORTANT CHANGE)
        action_obj, reason = agent.decide(state, training=False)
        action = action_obj.action

        result = step_env(action)

        next_state = result["state"]
        reward = result["reward"]
        done = result["done"]

        print(f"[STEP {step_count}]")
        print("Action:", action)
        print("Reason:", reason)
        print("Reward:", reward)
        print("State:", next_state)
        print("-" * 30)

        state = next_state
        step_count += 1

        time.sleep(0.3)

    print("[END] Episode finished")


if __name__ == "__main__":
    run_episode()