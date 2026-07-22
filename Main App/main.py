"""
main.py — GymGuru Dashboard (Restructured Active Focus UI)
────────────────────────────────────────────────────────────────────
ALL logic is 100% unchanged:
  WebRTC key "exercise-analysis", all st.session_state keys,
  all widget keys, rep-counting, voice pipeline, persistence.
Only layout components and rendering functions are updated.
"""

import os
import time
import pandas as pd
import streamlit as st

from services.auth.login_wall import render_login_wall
from services.state.session_defaults import initial_session_defaults
from services.config.workout_config import EXERCISE_OPTIONS
from services.ui.style_loader import load_css, inject_local_font, inject_webrtc_styles
from services.persistence.exercise_repository import init_db, get_users_exercises
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from services.vision.exercise_video_processor import VideoProcessorClass
from services.tracking.metrics import sync_metrics_update
from groq import Groq
from services.coaching.llm import LLMCoach
from services.coaching.tts import TextToSpeech
from services.coaching.voice_pipeline import VoicePipeline, autoplay_audio
import base64


def _get_base64_logo() -> str:
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        logo_path = os.path.join(base_dir, "static", "logo.jpg")
        with open(logo_path, "rb") as f:
            return f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
    except Exception:
        return "/app/static/logo.jpg"


_LOGO_URI = _get_base64_logo()


# ── Top Header ────────────────────────────────────────────────────────────────
def _render_top_header(username: str) -> None:
    initial = username[0].upper() if username else "A"
    
    col_back, col_title = st.columns([1.5, 8])
    with col_back:
        st.markdown("<div style='height: 0.5rem;'></div>", unsafe_allow_html=True)
        if st.button("← Back to Home", key="back_to_home_btn", use_container_width=True):
            st.session_state.workout_started = False
            st.session_state.user_id = None
            st.session_state.username = None
            st.rerun()
            
    with col_title:
        st.markdown(f"""
<div class="dev-header" style="border-bottom: none; margin-bottom: 0; padding-bottom: 0;">
  <div>
    <h1 class="dev-header-title" style="margin-top: 0 !important;">Welcome back, <span class="dev-user-highlight">{username}</span> 👋</h1>
    <p class="dev-header-sub" style="margin-top: 0.1rem !important;">Today's Workout</p>
  </div>
  <div class="dev-user-badge">
    <div class="dev-user-avatar">{initial}</div>
    <span class="dev-user-name">{username}</span>
  </div>
</div>
""", unsafe_allow_html=True)
        
    st.markdown('<div style="border-bottom: 1px solid #30363D; margin-bottom: 1.5rem; margin-top: 0.5rem;"></div>', unsafe_allow_html=True)


# ── Stat Cards (First Row - ONLY actual metrics) ──────────────────────────────
def _render_stat_cards(user_id: int, workout_started: bool) -> None:
    rows = get_users_exercises(user_id) if user_id else []
    total_sessions = len(rows)

    ex_name = st.session_state.get("plan_exercise") or st.session_state.get("exercise_type") or "Squats"
    
    t_sets = st.session_state.get("target_sets", 3)
    s_done = st.session_state.get("sets_completed", 0)
    sets_val = f"{s_done} / {t_sets}"

    rps = st.session_state.get("reps_per_set", 10)
    cs_reps = st.session_state.get("current_set_reps", 0)
    reps_val = f"{cs_reps} / {rps}"

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
<div class="dev-stat-card">
  <div class="dev-stat-label">WORKOUT SESSIONS</div>
  <div class="dev-stat-value">{total_sessions}</div>
</div>
""", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
<div class="dev-stat-card">
  <div class="dev-stat-label">EXERCISE SELECTED</div>
  <div class="dev-stat-value">{ex_name}</div>
</div>
""", unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
<div class="dev-stat-card">
  <div class="dev-stat-label">CURRENT SET</div>
  <div class="dev-stat-value">{sets_val}</div>
</div>
""", unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
<div class="dev-stat-card">
  <div class="dev-stat-label">CURRENT REP</div>
  <div class="dev-stat-value">{reps_val}</div>
</div>
""", unsafe_allow_html=True)


# ── AI Coach Status Badges ────────────────────────────────────────────────────
def _get_ai_status(speaking: bool) -> tuple[str, str]:
    if speaking:
        return "Speaking", "status-speaking"
    elif st.session_state.get("workout_started", False):
        return "Listening", "status-listening"
    return "Idle", "status-idle"


def _get_posture_status(ex: str) -> tuple[str, str]:
    if not st.session_state.get("workout_started", False):
        return "Ready", "posture-ready"

    if ex == "Squats":
        depth = st.session_state.get("depth_status", "")
        if "Deep" in depth or "Good" in depth:
            return "Good form", "posture-good"
        elif depth:
            return depth, "posture-warning"
    elif ex == "Push-ups":
        align = st.session_state.get("body_alignment", "")
        if "Good" in align or "Straight" in align:
            return "Good form", "posture-good"
        elif align:
            return align, "posture-warning"
    elif ex == "Biceps Curls (Dumbbell)":
        swing = st.session_state.get("swing_status", "")
        if "No Swing" in swing or "Good" in swing:
            return "Good form", "posture-good"
        elif swing:
            return swing, "posture-warning"
    elif ex == "Shoulder Press":
        arch = st.session_state.get("back_arch_status", "")
        if "Good" in arch or "Neutral" in arch:
            return "Good form", "posture-good"
        elif arch:
            return arch, "posture-warning"
    elif ex == "Lunges":
        bal = st.session_state.get("balance_status", "")
        if "Good" in bal or "Balanced" in bal:
            return "Good form", "posture-good"
        elif bal:
            return bal, "posture-warning"

    return "Tracking active", "posture-good"


# ── Sidebar (Navigation & Logout Only) ────────────────────────────────────────
def _sidebar(workout_started: bool) -> None:
    with st.sidebar:
        # Brand
        st.markdown(f"""
<div class="dev-sidebar-brand">
  <img src="{_LOGO_URI}" class="dev-sidebar-logo" alt="GymGuru Logo" />
  <div>
    <div class="dev-sidebar-title">GymGuru</div>
    <div class="dev-sidebar-subtitle">AI Personal Fitness Coach</div>
  </div>
</div>
""", unsafe_allow_html=True)

        st.markdown('<div class="dev-sidebar-nav-title">NAVIGATION</div>', unsafe_allow_html=True)

        st.markdown("""
<div class="dev-nav-list">
  <div class="dev-nav-item active"><span class="dev-nav-icon">📊</span> Dashboard</div>
  <div class="dev-nav-item"><span class="dev-nav-icon">🏋️</span> Workout</div>
  <div class="dev-nav-item"><span class="dev-nav-icon">💪</span> Exercise</div>
  <div class="dev-nav-item"><span class="dev-nav-icon">📜</span> History</div>
  <div class="dev-nav-item"><span class="dev-nav-icon">🤖</span> AI Coach</div>
  <div class="dev-nav-item"><span class="dev-nav-icon">⚙️</span> Settings</div>
</div>
""", unsafe_allow_html=True)

        st.divider()

        # Space out and put Logout button at the bottom
        st.markdown("<div style='height: 15rem;'></div>", unsafe_allow_html=True)
        if st.button("🚪  Log Out", key="logout_btn", use_container_width=True):
            st.session_state["user_id"]  = None
            st.session_state["username"] = None
            st.session_state["workout_started"] = False
            st.rerun()


# ── Row 3: Workout Setup & Exercise Selection ─────────────────────────────────
def _render_workout_setup(workout_started: bool) -> None:
    st.markdown('<div class="dev-card-title" style="margin-top: 1.5rem; margin-bottom: 0.75rem;">Workout Setup</div>', unsafe_allow_html=True)
    
    with st.container(border=True):
        # 1. Chips selection row
        st.markdown('<div style="font-size: 0.85rem; color: #9CA3AF; margin-bottom: 0.5rem; font-weight: 600;">1. Select Exercise</div>', unsafe_allow_html=True)
        chip_items = [
            ("🏋️", "Squats"),
            ("🏃", "Push-ups"),
            ("💪", "Biceps Curls (Dumbbell)"),
            ("🙌", "Shoulder Press"),
            ("🚶", "Lunges"),
        ]

        def select_exercise(name):
            st.session_state["plan_exercise"] = name
            st.session_state["exercise_type"] = name

        active_ex = st.session_state.get("plan_exercise", "Squats")

        cols = st.columns(len(chip_items))
        for idx, (icon, name) in enumerate(chip_items):
            with cols[idx]:
                btn_type = "primary" if name == active_ex else "secondary"
                st.button(
                    f"{icon}  {name}",
                    key=f"chip_{idx}",
                    type=btn_type,
                    on_click=select_exercise,
                    args=(name,),
                    use_container_width=True,
                )
                
        st.markdown('<div style="margin-top: 0.75rem; margin-bottom: 0.75rem; border-top: 1px solid #30363D;"></div>', unsafe_allow_html=True)

        # 2. Sets and Reps selection
        st.markdown('<div style="font-size: 0.85rem; color: #9CA3AF; margin-bottom: 0.5rem; font-weight: 600;">2. Set Targets</div>', unsafe_allow_html=True)
        col_sets, col_reps = st.columns(2)
        with col_sets:
            plan_sets = st.number_input(
                "Sets Target", min_value=0, max_value=50, key="plan_sets", step=1
            )
        with col_reps:
            plan_reps = st.number_input(
                "Reps per Set Target", min_value=0, max_value=50, key="plan_reps", step=1
            )

        st.markdown('<div style="height: 0.5rem;"></div>', unsafe_allow_html=True)

        # 3. Start Workout button
        if not workout_started:
            start_btn = st.button("▶  Start Workout Session", key="setup_start_btn", type="primary", use_container_width=True)
            if start_btn:
                st.session_state.exercise_type  = active_ex
                st.session_state.target_sets    = int(plan_sets)
                st.session_state.reps_per_set   = int(plan_reps)
                st.session_state.reps           = 0
                st.session_state.workout_started = True
                st.session_state.set_cycle_started_at      = time.time()
                st.session_state.elapsed_seconds  = 0
                st.session_state.last_saved_sets_completed  = 0

                if st.session_state.voice_pipeline:
                    result = st.session_state.voice_pipeline.process_event(
                        event="workout_started",
                        exercise=active_ex,
                        metrics={},
                    )
                    if result:
                        st.session_state.audio_to_play   = result[0]
                        st.session_state.coach_feedback  = result[1]

                st.session_state.last_notified_sets_completed    = 0
                st.session_state.last_notified_workout_complete  = False
                st.rerun()
        else:
            stop_btn = st.button("⏹  Stop Workout Session", key="setup_stop_btn", use_container_width=True)
            if stop_btn:
                st.session_state.workout_started = False
                if st.session_state.voice_pipeline:
                    result = st.session_state.voice_pipeline.process_event(
                        event="workout_completed", exercise=active_ex, metrics={}
                    )
                    if result:
                        st.session_state.audio_to_play  = result[0]
                        st.session_state.coach_feedback = result[1]
                st.rerun()


# ── Workout History Table (Row 4) ─────────────────────────────────────────────
def _render_history_table(user_id: int) -> None:
    st.markdown('<div class="dev-card-title" style="margin: 1.5rem 0 0.75rem;">Workout History</div>', unsafe_allow_html=True)

    rows = get_users_exercises(user_id) if user_id else []
    if not rows:
        st.markdown("""
<div style="background: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 2rem; text-align: center; color: #9CA3AF; font-size: 0.88rem;">
  No workouts recorded yet. Start a session to log metrics into SQLite.
</div>
""", unsafe_allow_html=True)
        return

    arr = []
    for r in rows:
        row_dict = dict(r) if hasattr(r, "keys") else r
        created_at = row_dict.get("created_at", "")
        duration_sec = row_dict.get("time", 0)
        m = int(duration_sec // 60)
        s = int(duration_sec % 60)
        dur_str = f"{m}m {s}s" if m else f"{s}s"

        arr.append({
            "Date": created_at[:16] if created_at else "",
            "Exercise": row_dict.get("exercise_name", ""),
            "Sets": row_dict.get("sets", 0),
            "Reps": row_dict.get("reps", 0),
            "Duration": dur_str,
        })

    df = pd.DataFrame(arr)
    st.dataframe(df, use_container_width=True, hide_index=True)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(
        page_icon="🏋️",
        page_title="GymGuru — AI Fitness Coach",
        initial_sidebar_state="expanded",
        layout="wide",
    )

    load_css(os.path.join(os.getcwd(), "static", "style.css"))
    inject_local_font(os.path.join(os.getcwd(), "static", "AdobeClean.otf"), "AdobeClean")

    init_db()

    # Auth gate — login wall logic unchanged
    if not render_login_wall():
        return

    initial_session_defaults()

    # Voice pipeline init (logic unchanged)
    if "voice_pipeline" not in st.session_state:
        try:
            api_key = os.environ.get("GROQ_API_KEY", "")
            if not api_key and hasattr(st, "secrets") and "GROQ_API_KEY" in st.secrets:
                api_key = st.secrets["GROQ_API_KEY"]
            gc   = Groq(api_key=api_key)
            llm  = LLMCoach(gc)
            tts  = TextToSpeech()
            st.session_state.voice_pipeline = VoicePipeline(llm, tts)
        except Exception:
            st.session_state.voice_pipeline = None

    workout_started = st.session_state.get("workout_started", False)
    username = st.session_state.get("username", "Athlete")
    user_id = st.session_state.get("user_id", 0)

    # Sidebar
    _sidebar(workout_started)

    # Top Header
    _render_top_header(username)

    # First Row: 4 Stat Cards
    _render_stat_cards(user_id, workout_started)

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # Second Row: Camera (70%) & AI Coach (30%)
    col_left, col_right = st.columns([1.3, 1.0], gap="large")

    ex      = st.session_state.get("exercise_type", st.session_state.get("plan_exercise", "Squats"))
    t_sets  = st.session_state.get("target_sets", 3)
    rps     = st.session_state.get("reps_per_set", 10)
    s_done  = st.session_state.get("sets_completed", 0)
    cs_reps = st.session_state.get("current_set_reps", 0)
    with col_left:
        # Elapsed Timer calculation
        elapsed_sec = st.session_state.get("elapsed_seconds", 0)
        if workout_started and st.session_state.get("set_cycle_started_at"):
            elapsed_sec = int(time.time() - st.session_state.set_cycle_started_at)
            st.session_state.elapsed_seconds = elapsed_sec

        m = elapsed_sec // 60
        s = elapsed_sec % 60
        elapsed_str = f"{m:02d}:{s:02d}"

        # Top camera status banner
        st.markdown(f"""
<div style="background: #161B22; border: 1px solid #30363D; border-radius: 6px; padding: 0.75rem 1rem; margin-bottom: 0.75rem; display: flex; justify-content: space-between; align-items: center;">
  <div style="font-size: 1.15rem; font-weight: 800; color: #FFFFFF;">🎥 Live Camera — {ex}</div>
  <div style="display: flex; gap: 1.5rem; font-size: 0.88rem; color: #9CA3AF;">
    <span>Target: <strong>{t_sets} sets × {rps} reps</strong></span>
    <span>Timer: <strong style="font-family: var(--font-mono); color: #7C5CFF;">⏱ {elapsed_str}</strong></span>
  </div>
</div>
""", unsafe_allow_html=True)

        # Camera feed streamer or Offline placeholder
        if not workout_started:
            st.markdown("""
<div style="background: #161B22; border: 1px solid #30363D; border-radius: 6px; padding: 4.5rem 1.5rem; text-align: center; height: 320px; display: flex; flex-direction: column; justify-content: center; align-items: center; margin-bottom: 0.75rem;">
  <div style="font-size: 2.2rem; margin-bottom: 0.75rem; opacity: 0.5;">📷</div>
  <div style="font-size: 1.1rem; font-weight: 800; color: #FFFFFF; margin-bottom: 0.25rem;">Camera Preview Offline</div>
  <div style="font-size: 0.85rem; color: #9CA3AF; max-width: 320px; line-height: 1.5;">
    Please select an exercise, configure target sets/reps below, and click Start Workout.
  </div>
</div>
""", unsafe_allow_html=True)
        else:
            # WebRTC streamer — completely unchanged call & key
            context = webrtc_streamer(
                key="exercise-analysis",
                mode=WebRtcMode.SENDRECV,
                video_processor_factory=VideoProcessorClass,
                rtc_configuration={
                    "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
                },
                media_stream_constraints={"video": True, "audio": False},
                async_processing=True,
            )

            sync_metrics_update(context)

            if context.state.playing:
                time.sleep(0.25)
                st.rerun()

            inject_webrtc_styles()

        # Below camera metadata panel
        posture_text, posture_cls = _get_posture_status(ex)
        st.markdown(f"""
<div style="background: #161B22; border: 1px solid #30363D; border-radius: 6px; padding: 0.75rem 1rem; margin-bottom: 0.75rem; display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.5rem; text-align: center;">
  <div>
    <div style="font-size: 0.72rem; color: #9CA3AF; text-transform: uppercase; font-weight: 600;">Live Reps</div>
    <div style="font-size: 1.15rem; font-weight: 800; color: #FFFFFF; margin-top: 0.15rem;">{cs_reps} / {rps}</div>
  </div>
  <div>
    <div style="font-size: 0.72rem; color: #9CA3AF; text-transform: uppercase; font-weight: 600;">Current Set</div>
    <div style="font-size: 1.15rem; font-weight: 800; color: #FFFFFF; margin-top: 0.15rem;">{s_done} / {t_sets}</div>
  </div>
  <div>
    <div style="font-size: 0.72rem; color: #9CA3AF; text-transform: uppercase; font-weight: 600;">Current Form</div>
    <div style="font-size: 1.15rem; font-weight: 800; color: #FFFFFF; margin-top: 0.15rem;">{posture_text}</div>
  </div>
  <div>
    <div style="font-size: 0.72rem; color: #9CA3AF; text-transform: uppercase; font-weight: 600;">Pose Status</div>
    <div style="font-size: 1.15rem; font-weight: 800; color: {'#22C55E' if workout_started else '#9CA3AF'}; margin-top: 0.15rem;">{'● Tracking' if workout_started else '○ Offline'}</div>
  </div>
</div>
""", unsafe_allow_html=True)

        # Prominent camera layout buttons
        if not workout_started:
            start_btn = st.button("▶  Start Workout Session", key="cam_start_btn", type="primary", use_container_width=True)
            if start_btn:
                st.session_state.exercise_type  = st.session_state.get("plan_exercise", "Squats")
                st.session_state.target_sets    = int(st.session_state.get("plan_sets", 3))
                st.session_state.reps_per_set   = int(st.session_state.get("plan_reps", 10))
                st.session_state.reps           = 0
                st.session_state.workout_started = True
                st.session_state.set_cycle_started_at      = time.time()
                st.session_state.elapsed_seconds  = 0
                st.session_state.last_saved_sets_completed  = 0

                if st.session_state.voice_pipeline:
                    result = st.session_state.voice_pipeline.process_event(
                        event="workout_started",
                        exercise=st.session_state.exercise_type,
                        metrics={},
                    )
                    if result:
                        st.session_state.audio_to_play   = result[0]
                        st.session_state.coach_feedback  = result[1]

                st.session_state.last_notified_sets_completed    = 0
                st.session_state.last_notified_workout_complete  = False
                st.rerun()
        else:
            stop_btn = st.button("⏹  Stop Workout Session", key="cam_stop_btn", use_container_width=True)
            if stop_btn:
                st.session_state.workout_started = False
                if st.session_state.voice_pipeline:
                    result = st.session_state.voice_pipeline.process_event(
                        event="workout_completed", exercise=ex, metrics={}
                    )
                    if result:
                        st.session_state.audio_to_play  = result[0]
                        st.session_state.coach_feedback = result[1]
                st.rerun()

    with col_right:
        st.markdown('<div class="dev-card-title" style="margin-bottom: 0.75rem;">AI Coach</div>', unsafe_allow_html=True)

        is_speaking = bool(st.session_state.get("audio_to_play"))
        ai_status_text, ai_status_cls = _get_ai_status(is_speaking)
        posture_text, posture_cls = _get_posture_status(st.session_state.get("exercise_type", "Squats"))

        feedback = st.session_state.get("coach_feedback", "")
        if not feedback:
            feedback = "AI Coach is ready. Start a workout session to analyze posture and receive real-time voice guidance."

        status_dot = "🟢" if workout_started else "⚪"
        status_text = "Active" if workout_started else "Ready"
        voice_state = ai_status_text

        # Dynamic Form & Mistakes
        alignment_status = "Checking..." if workout_started else "N/A"
        mistakes_status = "None" if workout_started else "N/A"
        ex_active = st.session_state.get("exercise_type", "Squats")

        if workout_started:
            if ex_active == "Squats":
                alignment_status = st.session_state.get("depth_status", "N/A")
                if "Low" in alignment_status or "Check" in alignment_status:
                    mistakes_status = "Knee depth low"
            elif ex_active == "Push-ups":
                alignment_status = st.session_state.get("body_alignment", "N/A")
                if "Good" not in alignment_status:
                    mistakes_status = alignment_status
            elif ex_active == "Biceps Curls (Dumbbell)":
                alignment_status = st.session_state.get("swing_status", "N/A")
                if "Swing" in alignment_status:
                    mistakes_status = "Elbow swing"
            elif ex_active == "Shoulder Press":
                alignment_status = st.session_state.get("back_arch_status", "N/A")
                if "Arch" in alignment_status:
                    mistakes_status = "Back arched"
            elif ex_active == "Lunges":
                alignment_status = st.session_state.get("balance_status", "N/A")
                if "Good" not in alignment_status:
                    mistakes_status = alignment_status

        st.markdown(f"""
<div class="dev-card" style="margin-bottom: 1rem;">
  <div style="display: flex; flex-direction: column; gap: 0.65rem; margin-bottom: 1.25rem;">
    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #30363D; padding-bottom: 0.5rem;">
      <span style="font-size: 0.85rem; color: #9CA3AF; font-weight: 600;">Status</span>
      <span style="font-size: 0.88rem; font-weight: 700; color: #FFFFFF;">{status_dot} {status_text}</span>
    </div>
    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #30363D; padding-bottom: 0.5rem;">
      <span style="font-size: 0.85rem; color: #9CA3AF; font-weight: 600;">Voice Status</span>
      <span class="status-badge {ai_status_cls}">{voice_state}</span>
    </div>
    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #30363D; padding-bottom: 0.5rem;">
      <span style="font-size: 0.85rem; color: #9CA3AF; font-weight: 600;">Body Alignment</span>
      <span style="font-size: 0.85rem; font-weight: 700; color: #E6EDF3;">{alignment_status}</span>
    </div>
    <div style="display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #30363D; padding-bottom: 0.5rem;">
      <span style="font-size: 0.85rem; color: #9CA3AF; font-weight: 600;">Form Issues / Mistakes</span>
      <span style="font-size: 0.85rem; font-weight: 700; color: {'#F59E0B' if mistakes_status != 'None' and mistakes_status != 'N/A' else '#22C55E'};">{mistakes_status}</span>
    </div>
  </div>

  <div style="font-size: 0.72rem; color: #6E7681; font-weight: 700; text-transform: uppercase; margin-bottom: 0.4rem; letter-spacing: 0.05em;">LATEST FEEDBACK</div>
  <div style="font-size: 0.92rem; color: #E6EDF3; line-height: 1.5; background: #0D1117; border: 1px solid #30363D; border-radius: 6px; padding: 1rem;">
    "{feedback}"
  </div>
</div>
""", unsafe_allow_html=True)

        # Real-time metrics breakdown in right side
        if workout_started:
            st.markdown('<div class="dev-card-title" style="font-size: 0.88rem; margin-bottom: 0.5rem;">Real-Time Pose Metrics</div>', unsafe_allow_html=True)
            m_col1, m_col2, m_col3 = st.columns(3)

            if ex == "Squats":
                with m_col1:
                    st.metric("Knee Angle", f"{st.session_state.get('knee_angle', 0)}°")
                with m_col2:
                    st.metric("Back Angle", f"{st.session_state.get('back_angle', 0)}°")
                with m_col3:
                    st.metric("Depth", st.session_state.get("depth_status", "N/A"))

            elif ex == "Push-ups":
                with m_col1:
                    st.metric("Elbow Angle", f"{st.session_state.get('elbow_angle', 0)}°")
                with m_col2:
                    st.metric("Alignment", st.session_state.get("body_alignment", "N/A"))
                with m_col3:
                    st.metric("Hips", st.session_state.get("hip_status", "N/A"))

            elif ex == "Biceps Curls (Dumbbell)":
                with m_col1:
                    st.metric("Elbow Angle", f"{st.session_state.get('elbow_angle', 0)}°")
                with m_col2:
                    st.metric("Shoulder", st.session_state.get("shoulder_status", "N/A"))
                with m_col3:
                    st.metric("Swing", st.session_state.get("swing_status", "N/A"))

            elif ex == "Shoulder Press":
                with m_col1:
                    st.metric("Elbow Angle", f"{st.session_state.get('elbow_angle', 0)}°")
                with m_col2:
                    st.metric("Extension", st.session_state.get("extension_status", "N/A"))
                with m_col3:
                    st.metric("Back Arch", st.session_state.get("back_arch_status", "N/A"))

            elif ex == "Lunges":
                with m_col1:
                    st.metric("Front Knee", f"{st.session_state.get('front_knee_angle', 0)}°")
                with m_col2:
                    st.metric("Torso Angle", f"{st.session_state.get('torso_angle', 0)}°")
                with m_col3:
                    st.metric("Balance", st.session_state.get("balance_status", "N/A"))

    # Audio Autoplay (logic unchanged)
    if st.session_state.get("audio_to_play"):
        autoplay_audio(st.session_state.audio_to_play)

    # Third Row: Workout Setup (Exercise Chips, Target selectbox, Sets and Reps, Start)
    _render_workout_setup(workout_started)

    # Fourth Row: Workout History Table
    if isinstance(user_id, int):
        _render_history_table(user_id)

    # Bottom Footer
    st.markdown("""
<div class="dev-footer">
  <div class="dev-footer-copy">GymGuru &copy; 2025 &nbsp;·&nbsp; AI Fitness Coach &nbsp;·&nbsp; Data stored locally in SQLite</div>
  <div class="dev-tech-chips">
    <span class="dev-tech-chip">Python 3.11</span>
    <span class="dev-tech-chip">MediaPipe Pose</span>
    <span class="dev-tech-chip">OpenCV</span>
    <span class="dev-tech-chip">Groq LLaMA 3.3</span>
    <span class="dev-tech-chip">SQLite</span>
    <span class="dev-tech-chip">Streamlit</span>
  </div>
</div>
""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
