# 🧠 AI Productivity Coach (RL-Based)

A Reinforcement Learning-based AI system that helps users optimize focus, reduce distractions, and manage fatigue dynamically.

---

## 🚀 Features

- Reinforcement Learning Agent (Q-Learning)
- Real-world productivity simulation environment
- Dynamic reward system (focus, fatigue, distractions)
- FastAPI backend
- Interactive frontend (HTML/CSS/JS)
- Dockerized deployment

---

## 🧠 Environment

### Observation Space
- focus_level (0–1)
- fatigue (0–1)
- distractions (list)
- time_spent
- deadline

### Action Space
- continue
- take_break
- block_distraction

---

## 🎯 Reward Design

- Positive reward for focus improvement
- Penalty for fatigue and distractions
- Bonus for clean environment (no distractions)
- Time pressure penalty near deadline

---

## 🔌 API Endpoints

- /reset → Initialize environment  
- /step_rl → Run RL step (returns state, reward, done)  
- /step → UI-based AI advice  

---

## ▶️ Run Locally

Run the backend server:
uvicorn app.main:app --reload

---

## 🐳 Run with Docker

Build and run the project using Docker:
docker build -t focusforge .
docker run -p 8000:8000 focusforge

---

## 🧪 Run Inference

Run the RL agent using:
python inference.py

---

## 📊 Evaluation

Score range: 0 → 1

Based on:
- Average focus
- Total reward
- Distractions

---

## 📁 Project Structure

focusforge/
│
├── app/
│   ├── main.py
│   ├── env.py
│   ├── agent.py
│   ├── models.py
│
├── inference.py
├── openenv.yaml
├── requirements.txt
├── Dockerfile
├── README.md

---

## 👨‍💻 Author

Apurv