from app.env import FocusEnv
from app.models import Action
from app.grader import grade_episode

NUM_EPISODES = 5
all_scores = []

for episode in range(NUM_EPISODES):
    print(f"\n========== EPISODE {episode+1} ==========")

    env = FocusEnv()
    obs = env.reset("hard")
    print("Initial State:", obs)

    step_count = 0
    done = False
    last_action = None

    while not done:
        state = env.state()
        time_left = state["deadline"] - state["time_spent"]

        distractions = state["distractions"]
        focus = state["focus_level"]
        fatigue = state["fatigue"]

        # 🧠 ELITE DECISION LOGIC

        # 1️⃣ ENDGAME (MOST IMPORTANT)
        if time_left <= 15:
            if len(distractions) > 0:
                action_type = "block_distraction"
            else:
                action_type = "continue"

        # 2️⃣ FATIGUE CONTROL
        elif fatigue > 0.5:
            action_type = "take_break"

        # 3️⃣ DISTRACTION HANDLING (NO DOUBLE BLOCK)
        elif len(distractions) > 0:
            if last_action != "block_distraction":
                action_type = "block_distraction"
            else:
                action_type = "continue"

        # 4️⃣ FOCUS BUILDING
        elif focus < 0.7:
            action_type = "continue"

        # 5️⃣ DEFAULT
        else:
            action_type = "continue"

        # 🎯 CREATE ACTION
        if action_type == "block_distraction":
            target = distractions[0] if distractions else "youtube"
            action = Action(action=action_type, target=target)
        else:
            action = Action(action=action_type)

        # 🔥 STEP
        obs, reward, done, _ = env.step(action)

        print(f"\nStep {step_count}")
        print("Action:", action_type)
        print("State:", obs)
        print("Reward:", reward)
        print("Done:", done)

        last_action = action_type
        step_count += 1

    score = grade_episode(env.history, env.task)
    all_scores.append(score)

    print(f"\n🔥 EPISODE {episode+1} SCORE:", score)


# 🔥 FINAL RESULT
avg_score = sum(all_scores) / len(all_scores)

print("\n==============================")
print("🔥 FINAL AVERAGE SCORE:", avg_score)
print("==============================")