import random
from app.models import Observation, Action, Reward, TaskScore, EpisodeScore


class Task:
    def __init__(self, name, difficulty, deadline, reward_scale):
        self.name = name
        self.difficulty = difficulty
        self.deadline = deadline
        self.reward_scale = reward_scale


TASKS = {
    "easy": Task("Easy Task", 1, 60, 1.0),
    "medium": Task("Medium Task", 2, 50, 1.3),
    "hard": Task("Hard Task", 3, 40, 1.7),
}


class FocusEnv:
    def __init__(self):
        self.task = TASKS["easy"]
        self.history = []
        self.reset("easy")

    def reset(self, task_type="easy"):
        self.task = TASKS[task_type]
        self.current_task_type = task_type

        self.state_data = {
            "current_task": "DSA",
            "focus_level": 0.7,
            "fatigue": 0.0,
            "distractions": ["youtube", "whatsapp"],
            "time_spent": 0,
            "deadline": self.task.deadline
        }

        self.history = []
        return Observation(**self.state_data)

    # ✅ NEW — required by OpenEnv spec
    def state(self):
        return Observation(**self.state_data)

    def step(self, action: Action):
        reward = 0

        self.state_data["fatigue"] += 0.035
        self.state_data["fatigue"] = min(1.0, self.state_data["fatigue"])

        if action.action == "continue":
            boost = 0.04 * (1 - self.state_data["fatigue"])
            self.state_data["focus_level"] += boost

        elif action.action == "block_distraction":
            if action.target in self.state_data["distractions"]:
                self.state_data["distractions"].remove(action.target)
                self.state_data["focus_level"] += 0.05

        elif action.action == "take_break":
            self.state_data["fatigue"] -= 0.3
            self.state_data["fatigue"] = max(0.0, self.state_data["fatigue"])
            self.state_data["focus_level"] += 0.1

        time_ratio = self.state_data["time_spent"] / self.state_data["deadline"]

        if action.action == "continue":
            reward = self.state_data["focus_level"] * (2.2 + time_ratio)
            if len(self.state_data["distractions"]) > 0:
                reward -= 1.5
            if self.state_data["fatigue"] > 0.6:
                reward -= 1.2

        elif action.action == "block_distraction":
            reward = 3.0 - (0.4 * self.state_data["fatigue"])

        elif action.action == "take_break":
            reward = 0.6 + (self.state_data["fatigue"] * 1.2)
            if self.state_data["fatigue"] < 0.3:
                reward -= 1.0

        if len(self.state_data["distractions"]) == 0:
            reward += 0.5

        if self.state_data["deadline"] - self.state_data["time_spent"] < 10:
            reward -= 1.5

        self.state_data["focus_level"] -= 0.02
        self.state_data["focus_level"] -= (self.state_data["fatigue"] * 0.05)

        if random.random() < 0.12:
            if len(self.state_data["distractions"]) < 2:
                self.state_data["distractions"].append("instagram")
            self.state_data["focus_level"] -= 0.04

        self.state_data["time_spent"] += 5

        if self.state_data["time_spent"] > self.state_data["deadline"]:
            reward -= 3

        self.state_data["focus_level"] = max(0.02, min(1.0, self.state_data["focus_level"]))
        self.state_data["fatigue"] = max(0.0, min(1.0, self.state_data["fatigue"]))

        reward *= self.task.reward_scale

        self.history.append({
            "focus": self.state_data["focus_level"],
            "reward": reward,
            "distractions": self.state_data["distractions"].copy()
        })

        done = self.state_data["time_spent"] >= self.state_data["deadline"]

        return Observation(**self.state_data), Reward(value=reward), done, {}

    # ✅ NEW — per-task grader (scores 0.0 to 1.0)
    def grade(self, agent, task_type="easy"):
        self.reset(task_type)
        state_dict = self.state().dict()
        done = False
        total_reward = 0
        total_focus = 0
        steps = 0

        while not done and steps < 50:
            action, _ = agent.decide(state_dict, training=False)
            next_obs, reward, done, _ = self.step(action)
            next_dict = next_obs.dict()
            total_reward += reward.value
            total_focus += next_dict["focus_level"]
            state_dict = next_dict
            steps += 1

        avg_focus = total_focus / max(steps, 1)

        # difficulty penalty — harder tasks need higher focus to score same
        difficulty_factor = {"easy": 0.0, "medium": 0.05, "hard": 0.12}
        penalty = difficulty_factor.get(task_type, 0.0)

        score = round(
            min(1.0, max(0.0,
                avg_focus * 0.6 + (total_reward / max(steps, 1)) * 0.1 - penalty
            )), 4
        )

        grade = "A" if score > 0.75 else "B" if score > 0.5 else "C"

        return TaskScore(
            task=task_type,
            score=score,
            grade=grade,
            avg_focus=round(avg_focus, 4),
            total_reward=round(total_reward, 4),
            steps=steps
        )