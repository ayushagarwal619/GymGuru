<div align="center">

# 🏋️ GymGuru
### AI-Powered Real-Time Personal Fitness Coach

Real-time posture correction, rep counting, intelligent voice coaching, and workout analytics powered by Computer Vision and Generative AI.

<br>

![Python](https://img.shields.io/badge/Python-3.11-blue?style=for-the-badge)
![Streamlit](https://img.shields.io/badge/Streamlit-App-red?style=for-the-badge)
![MediaPipe](https://img.shields.io/badge/MediaPipe-Pose-green?style=for-the-badge)
![OpenCV](https://img.shields.io/badge/OpenCV-Computer%20Vision-blue?style=for-the-badge)
![Groq](https://img.shields.io/badge/Groq-AI-orange?style=for-the-badge)
![License](https://img.shields.io/badge/License-MIT-black?style=for-the-badge)

</div>

<br>

---

<div align="center">

## 📖 Overview

</div>

GymGuru is an AI-powered virtual fitness trainer that analyzes your workout in real-time using Computer Vision.

Instead of simply counting repetitions, GymGuru continuously monitors body posture, evaluates exercise form, detects mistakes, and provides intelligent AI-generated voice coaching during workouts.

The application runs through a modern browser using Streamlit and WebRTC, making professional workout guidance accessible without expensive hardware.

---

<div align="center">

## ✨ Features

### 🎯 Real-Time Pose Detection

</div>

- Live webcam tracking via `streamlit-webrtc`
- 33-point body landmark detection with MediaPipe's `PoseLandmarker`
- Real-time joint-angle calculation and movement analysis
- Skeleton overlay drawn directly on the video feed

<br>

<div align="center">

### 🏋 Supported Exercises

</div>

<div align="center">

✅ Squats &nbsp;&nbsp;|&nbsp;&nbsp; ✅ Push-ups &nbsp;&nbsp;|&nbsp;&nbsp; ✅ Biceps Curl (Dumbbell) &nbsp;&nbsp;|&nbsp;&nbsp; ✅ Shoulder Press &nbsp;&nbsp;|&nbsp;&nbsp; ✅ Lunges

</div>

<br>

Each exercise has its own custom detector class built on a shared `BaseExercise` abstraction (angle math + rep state machine).

<br>

<div align="center">

### 🔢 Intelligent Rep Counter

</div>

Automatically tracks:

- Repetitions (per exercise-specific `up`/`down` angle thresholds)
- Current Set Reps
- Sets Completed vs. Target Sets
- Total Workout Duration (time per set cycle)

<br>

<div align="center">

### 🧠 AI Form Analysis

GymGuru continuously monitors:

| Exercise | Metrics Tracked |
|:---:|:---:|
| **Squats** | Knee angle, back angle, squat depth |
| **Push-ups** | Elbow angle, body alignment, hip sag/pike |
| **Biceps Curl** | Elbow angle, shoulder stability, swing detection |
| **Shoulder Press** | Elbow angle, arm extension, back arch |
| **Lunges** | Front knee angle, torso angle, balance |

</div>

<br>

<div align="center">

### 🤖 AI Voice Coach

</div>

Integrated with **Groq's LLaMA 3.3 70B** model to provide dynamic, natural-language coaching, converted to audio via `gTTS` and auto-played in-browser.

Feedback is generated for key events:

- `workout_started` → motivating kickoff cue
- `set_completed` → praise + rest prompt
- `ongoing_form_check` → real-time corrections when an issue is detected
- `no_pose_detected` → prompts you to step back into frame
- `workout_completed` → closing encouragement

Voice cues are rate-limited so the coach doesn't talk over itself.

<br>

<div align="center">

### 👤 User Authentication

</div>

Lightweight username-based login system (no password) that:

- Creates or retrieves a user record in SQLite
- Scopes workout history to that user
- Persists the session across reruns via `st.session_state`

<br>

<div align="center">

### 📊 Workout History

</div>

Automatically stores and aggregates:

- Exercise Name
- Total Reps
- Sets Completed
- Workout Duration (seconds)
- Date

History is grouped by exercise + date and displayed in a clean table after every session.

---

<div align="center">

## 🛠 Tech Stack

| Category | Technology |
|:---:|:---:|
| Language | Python 3.11 |
| Frontend | Streamlit |
| Computer Vision | OpenCV (headless) |
| Pose Estimation | MediaPipe Pose Landmarker |
| AI Coaching | Groq LLM (LLaMA 3.3 70B Versatile) |
| Voice Output | gTTS |
| Real-Time Streaming | streamlit-webrtc |
| Data Analysis | Pandas |
| Database | SQLite |

</div>

---

<div align="center">

## 🏗 Project Architecture

</div>

```
gym-guru/
│
├── LandingPage/                 # Static marketing site (HTML/CSS)
│   ├── index.html
│   ├── style.css
│   └── fonts/, IMGs/, videos/
│
└── Main App/                    # Streamlit application
    ├── main.py                  # App entry point
    ├── requirements.txt
    ├── packages.txt             # System-level deps (Streamlit Cloud)
    ├── core/
    │   └── base_exercise.py     # Angle math + detector contract
    ├── detectors/                # Per-exercise rep & form logic
    │   ├── squat.py
    │   ├── pushup.py
    │   ├── biceps_curl.py
    │   ├── shoulder_press.py
    │   └── lunges.py
    ├── services/
    │   ├── auth/                 # Login wall
    │   ├── coaching/              # LLM coach, TTS, voice pipeline
    │   ├── config/                 # Exercise options, prompts, pose graph
    │   ├── persistence/            # SQLite repository layer
    │   ├── state/                  # Session defaults
    │   ├── tracking/                # Metrics sync (video → UI → DB)
    │   ├── ui/                     # Custom CSS/font injection
    │   └── vision/                  # WebRTC video processor
    ├── static/style.css          # Streamlit theme overrides
    └── ml_models/                 # MediaPipe pose_landmarker model file
```

---

<div align="center">

## ⚙️ Installation

</div>

Clone the repository:

```bash
git clone https://github.com/ayushagarwal619/GymGuru.git
cd "GymGuru/Main App"
```

Create a virtual environment (using `uv`, recommended):

```bash
pip install uv
uv venv
source .venv/bin/activate      # macOS/Linux
.venv\Scripts\activate         # Windows
```

Install dependencies:

```bash
uv pip install -r requirements.txt
```

> ⚠️ Run these commands from inside `Main App/` — that's where `main.py` and `requirements.txt` live.

<div align="center">

### System Dependencies (Linux / Streamlit Cloud)

</div>

Already declared in `packages.txt`:

```
libgl1
libglib2.0-0t64
libsm6
libxext6
```

Run the application:

```bash
streamlit run main.py
```

---

<div align="center">

## 🔑 Environment Variables

</div>

Create a `.env` file inside `Main App/`:

```
GROQ_API_KEY=your_groq_api_key
```

Or, if deploying on Streamlit Cloud, add it under **App Settings → Secrets**:

```toml
GROQ_API_KEY = "YOUR_API_KEY"
```

---

<div align="center">

## 🚀 Workflow

```
User Login
      │
      ▼
Select Exercise, Sets & Reps
      │
      ▼
Start Camera (WebRTC)
      │
      ▼
MediaPipe Pose Detection
      │
      ▼
Exercise Detector (angle calc)
      │
      ▼
Rep Counter + Form Status
      │
      ▼
Metrics Synced to Session State
      │
      ▼
AI Coach (Groq) → Voice Feedback (gTTS)
      │
      ▼
Set/Workout Completion Saved to SQLite
      │
      ▼
Workout History Displayed
```

</div>

---

<div align="center">

## 🎯 Future Improvements

</div>

- More exercises (deadlifts, planks, jumping jacks)
- Personal workout planner
- Calorie estimation
- BMI calculator
- AI-driven exercise recommendations
- AI diet planner
- Mobile application
- Smartwatch integration
- Multi-person tracking
- Leaderboards
- Cloud synchronization of workout history

---

<div align="center">

## 💡 Why GymGuru?

</div>

Unlike traditional rep counters, GymGuru combines:

- Computer Vision
- Artificial Intelligence
- Real-Time Voice Coaching
- Automated Form Correction
- Persistent Workout Analytics

into a single, browser-based virtual personal trainer — no wearables, no extra hardware.

---

<div align="center">

## 🤝 Contributing

</div>

Contributions are welcome!

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

<div align="center">

## ⭐ Support

If you found this project useful, please consider giving it a ⭐ on GitHub.

It helps the project grow and motivates further development.

</div>

---

<div align="center">

## 📄 License

Distributed under the **MIT License**. See `LICENSE` for more information.

</div>

---

<div align="center">

### 🏋️ Train Smarter with AI

</div>
