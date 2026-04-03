from app.models import Action
import random
import json


class FocusAgent:
    def __init__(self):
        self.q_table = {}
        self.actions = ["continue", "take_break", "block_distraction"]

        self.alpha = 0.1
        self.gamma = 0.9
        self.epsilon = 0.4

        self.load_q_table()

    # 🔥 STATE GENERALIZATION
    def get_state_key(self, state):
        focus = round(state["focus_level"], 1)
        fatigue = round(state["fatigue"], 1)
        distractions = len(state["distractions"])
        time_ratio = round(state["time_spent"] / state["deadline"], 1)

        return (focus, fatigue, distractions, time_ratio)

    # 🤖 DECISION
    def decide(self, state, training=True):
        state_key = self.get_state_key(state)

        if state_key not in self.q_table:
            self.q_table[state_key] = {a: 0 for a in self.actions}

        if training and random.random() < self.epsilon:
            action_type = random.choice(self.actions)
            reason = "Exploring"
        else:
            q_vals = self.q_table[state_key]
            max_q = max(q_vals.values())

            best_actions = [a for a, q in q_vals.items() if q == max_q]
            action_type = random.choice(best_actions)

            reason = "Exploiting learned policy"

        if action_type == "block_distraction":
            target = state["distractions"][0] if state["distractions"] else "youtube"
            action = Action(action=action_type, target=target)
        else:
            action = Action(action=action_type)

        return action, reason

    # 🧠 UPDATE
    def update(self, prev_state, action, reward, next_state):
        s = self.get_state_key(prev_state)
        ns = self.get_state_key(next_state)

        if s not in self.q_table:
            self.q_table[s] = {a: 0 for a in self.actions}

        if ns not in self.q_table:
            self.q_table[ns] = {a: 0 for a in self.actions}

        current_q = self.q_table[s][action]
        max_next_q = max(self.q_table[ns].values())

        new_q = current_q + self.alpha * (
            reward + self.gamma * max_next_q - current_q
        )

        self.q_table[s][action] = new_q

        # 🔥 FASTER DECAY
        self.epsilon = max(0.05, self.epsilon * 0.992)

    # 🏋️ TRAIN
    def train(self, env, episodes=300):
        print(f"Training for {episodes} episodes...")

        for episode in range(episodes):
            state = env.reset()
            state_dict = state.dict()
            done = False
            steps = 0

            while not done and steps < 50:
                action, _ = self.decide(state_dict, training=True)
                next_state, reward, done, _ = env.step(action)

                next_state_dict = next_state.dict()

                self.update(
                    prev_state=state_dict,
                    action=action.action,
                    reward=reward.value,
                    next_state=next_state_dict
                )

                state_dict = next_state_dict
                steps += 1

            if episode % 50 == 0:
                print(f"  Episode {episode}/{episodes} | epsilon={self.epsilon:.3f}")

        self.save_q_table()
        print("Training complete. Q-table saved.")

    # 📊 SCORE
    def get_score(self, env):
        state = env.reset()
        state_dict = state.dict()
        done = False
        total_reward = 0
        total_focus = 0
        total_distractions = 0
        steps = 0

        self.freeze()

        while not done and steps < 50:
            action, _ = self.decide(state_dict, training=False)
            next_state, reward, done, _ = env.step(action)

            next_state_dict = next_state.dict()
            total_reward += reward.value
            total_focus += next_state_dict["focus_level"]
            total_distractions += len(next_state_dict["distractions"])
            state_dict = next_state_dict
            steps += 1

        avg_focus = total_focus / max(steps, 1)
        score = round(min(1.0, max(0.0, avg_focus * 0.6 + (total_reward / max(steps, 1)) * 0.4)), 4)

        return {
            "score": score,
            "avg_focus": round(avg_focus, 4),
            "total_reward": round(total_reward, 4),
            "total_distractions": total_distractions,
            "steps": steps,
            "grade": "A" if score > 0.75 else "B" if score > 0.5 else "C"
        }

    # 🔥 KEEP SMALL EXPLORATION
    def freeze(self):
        self.epsilon = 0.05

    # 💾 SAVE
    def save_q_table(self):
        serializable_q = {str(k): v for k, v in self.q_table.items()}
        with open("q_table.json", "w") as f:
            json.dump(serializable_q, f)

    # 📂 LOAD
    def load_q_table(self):
        try:
            with open("q_table.json", "r") as f:
                raw_q = json.load(f)

                self.q_table = {}
                for k, v in raw_q.items():
                    key = tuple(map(float, k.strip("()").split(", ")))
                    self.q_table[key] = v
        except:
            self.q_table = {}