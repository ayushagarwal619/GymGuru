"""
main.py — GymGuru Dashboard (Functionality Stabilization Phase)
────────────────────────────────────────────────────────────────────
Stabilized workout engine, timer, rep counting, live angles,
detector resets, AI coach pipeline, and SQLite persistence.
Layout, styling, and UI aesthetics remain 100% untouched.
"""

import os
import time
import base64
import pandas as pd
import streamlit as st

from services.auth.login_wall import render_login_wall
from services.state.session_defaults import initial_session_defaults
from services.config.workout_config import EXERCISE_OPTIONS, METRICS_FIELDS, get_rtc_configuration
from services.ui.style_loader import load_css, inject_local_font, inject_webrtc_styles
from services.persistence.exercise_repository import init_db, get_users_exercises
from streamlit_webrtc import webrtc_streamer, WebRtcMode
from services.vision.exercise_video_processor import VideoProcessorClass
from services.tracking.metrics import sync_metrics_update
from groq import Groq
from services.coaching.llm import LLMCoach
from services.coaching.tts import TextToSpeech
from services.coaching.voice_pipeline import VoicePipeline, autoplay_audio


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
            st.session_state.elapsed_seconds = 0
            st.session_state.reps = 0
            st.session_state.sets_completed = 0
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


def _start_workout_session() -> None:
    ex = st.session_state.get("plan_exercise") or st.session_state.get("exercise_type") or "Squats"
    target_sets = int(st.session_state.get("plan_sets", 3))
    reps_per_set = int(st.session_state.get("plan_reps", 10))

    now_ts = time.time()
    st.session_state.exercise_type = ex
    st.session_state.plan_exercise = ex
    st.session_state.target_sets = target_sets
    st.session_state.reps_per_set = reps_per_set
    st.session_state.reps = 0
    st.session_state.sets_completed = 0
    st.session_state.current_set_reps = 0
    st.session_state.workout_started = True
    st.session_state.scroll_to_camera = True
    st.session_state.workout_completed = False
    st.session_state.workout_start_time = 0.0
    st.session_state.set_cycle_started_at = 0.0
    st.session_state.elapsed_seconds = 0
    st.session_state.last_saved_sets_completed = 0
    st.session_state.last_notified_sets_completed = 0
    st.session_state.last_notified_workout_complete = False

    fields = METRICS_FIELDS.get(ex, {})
    for k, v in fields.items():
        st.session_state[k] = v

    if st.session_state.get("voice_pipeline"):
        try:
            result = st.session_state.voice_pipeline.process_event(
                event="workout_started",
                exercise=ex,
                metrics={},
            )
            if result:
                st.session_state.audio_to_play = result[0]
                st.session_state.coach_feedback = result[1]
        except Exception:
            st.session_state.coach_feedback = f"Workout session started for {ex}. AI Coach is analyzing form."
    else:
        st.session_state.coach_feedback = f"Workout session started for {ex}. AI Coach is ready."


def _stop_workout_session() -> None:
    st.session_state.workout_started = False
    start_time = st.session_state.get("workout_start_time", 0.0)
    if isinstance(start_time, (int, float)) and start_time > 0.0:
        try:
            st.session_state.elapsed_seconds = int(time.time() - start_time)
        except Exception:
            pass
    st.session_state.workout_start_time = 0.0
    ex = st.session_state.get("exercise_type", "Squats")
    if st.session_state.get("voice_pipeline"):
        try:
            result = st.session_state.voice_pipeline.process_event(
                event="workout_completed", exercise=ex, metrics={}
            )
            if result:
                st.session_state.audio_to_play = result[0]
                st.session_state.coach_feedback = result[1]
        except Exception:
            st.session_state.coach_feedback = f"Workout session completed for {ex}."


# ── Stat Cards (First Row - ONLY actual metrics) ──────────────────────────────
def _render_stat_cards(user_id: int, workout_started: bool) -> None:
    rows = get_users_exercises(user_id) if user_id else []
    total_sessions = len(rows)

    ex_name = st.session_state.get("plan_exercise") or st.session_state.get("exercise_type") or "Squats"
    
    t_sets = st.session_state.get("target_sets", 3)
    s_done = st.session_state.get("sets_completed", 0)
    rps = st.session_state.get("reps_per_set", 10)
    cs_reps = st.session_state.get("current_set_reps", 0)

    if st.session_state.get("workout_completed", False):
        sets_val = f"{t_sets} / {t_sets} ✓"
        reps_val = f"{rps} / {rps} ✓"
    else:
        sets_val = f"{s_done} / {t_sets}"
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
def _get_ai_status(speaking: bool, is_playing: bool = False) -> tuple[str, str]:
    if speaking:
        return "Speaking", "status-speaking"
    elif st.session_state.get("workout_started", False):
        if is_playing:
            return "Listening", "status-listening"
        return "Connecting", "status-idle"
    elif st.session_state.get("workout_completed", False):
        return "Complete", "status-listening"
    return "Idle", "status-idle"


def _get_posture_status(ex: str, is_playing: bool = True) -> tuple[str, str]:
    if st.session_state.get("workout_completed", False):
        return "Completed", "posture-good"
    if not st.session_state.get("workout_started", False):
        return "Ready", "posture-ready"
    if not is_playing:
        return "Connecting...", "posture-ready"

    if ex == "Squats":
        depth = st.session_state.get("depth_status", "N/A")
        if depth in ["GOOD DEPTH", "STANDING"]:
            return depth, "posture-good"
        elif depth != "N/A":
            return depth, "posture-warning"
    elif ex == "Push-ups":
        align = st.session_state.get("body_alignment", "N/A")
        hip = st.session_state.get("hip_status", "N/A")
        if align == "Straight" and hip == "LEVEL":
            return "Good form", "posture-good"
        elif align != "N/A" or hip != "N/A":
            return f"{align} | {hip}", "posture-warning"
    elif ex == "Biceps Curls (Dumbbell)":
        swing = st.session_state.get("swing_status", "N/A")
        shoulder = st.session_state.get("shoulder_status", "N/A")
        if swing == "NO SWING" and shoulder == "STABLE":
            return "Good form", "posture-good"
        elif swing != "N/A" or shoulder != "N/A":
            return f"{swing} | {shoulder}", "posture-warning"
    elif ex == "Shoulder Press":
        arch = st.session_state.get("back_arch_status", "N/A")
        ext = st.session_state.get("extension_status", "N/A")
        if arch == "Neutral" and ext in ["FULL EXTENSION", "NEARLY EXTENDED"]:
            return "Good form", "posture-good"
        elif arch != "N/A":
            return f"{ext} | {arch}", "posture-warning"
    elif ex == "Lunges":
        bal = st.session_state.get("balance_status", "N/A")
        if bal == "BALANCED":
            return "Good form", "posture-good"
        elif bal != "N/A":
            return bal, "posture-warning"

    return "Tracking active", "posture-good"


# ── Sidebar ───────────────────────────────────────────────────────────────────
def _sidebar(workout_started: bool) -> None:
    with st.sidebar:
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
        st.markdown("<div style='height: 15rem;'></div>", unsafe_allow_html=True)

        if st.button("🚪  Log Out", key="logout_btn", use_container_width=True):
            st.session_state["user_id"]  = None
            st.session_state["username"] = None
            st.session_state["workout_started"] = False
            st.session_state["workout_completed"] = False
            st.session_state["elapsed_seconds"] = 0
            st.rerun()


# ── Row 3: Workout Setup & Exercise Selection ─────────────────────────────────
def _render_workout_setup(workout_started: bool) -> None:
    st.markdown('<div class="dev-card-title" style="margin-top: 1.5rem; margin-bottom: 0.75rem;">Workout Setup</div>', unsafe_allow_html=True)
    
    with st.container(border=True):
        st.markdown('<div style="font-size: 0.85rem; color: #9CA3AF; margin-bottom: 0.5rem; font-weight: 600;">1. Select Exercise</div>', unsafe_allow_html=True)
        chip_items = [
            ("🏋️", "Squats"),
            ("🏃", "Push-ups"),
            ("💪", "Biceps Curls (Dumbbell)"),
            ("🙌", "Shoulder Press"),
            ("🚶", "Lunges"),
        ]

        def select_exercise(name):
            if st.session_state.get("plan_exercise") != name:
                st.session_state["plan_exercise"] = name
                st.session_state["exercise_type"] = name
                st.session_state["reps"] = 0
                st.session_state["sets_completed"] = 0
                st.session_state["current_set_reps"] = 0
                st.session_state["elapsed_seconds"] = 0
                st.session_state["workout_started"] = False
                st.session_state["workout_completed"] = False
                st.session_state["workout_start_time"] = 0.0
                st.session_state["set_cycle_started_at"] = 0.0
                st.session_state["last_saved_sets_completed"] = 0
                st.session_state["last_notified_workout_complete"] = False

                fields = METRICS_FIELDS.get(name, {})
                for k, v in fields.items():
                    st.session_state[k] = v

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

        st.markdown('<div style="font-size: 0.85rem; color: #9CA3AF; margin-bottom: 0.5rem; font-weight: 600;">2. Set Targets</div>', unsafe_allow_html=True)
        col_sets, col_reps = st.columns(2)
        with col_sets:
            plan_sets = st.number_input(
                "Sets Target", min_value=1, max_value=50, key="plan_sets", step=1
            )
        with col_reps:
            plan_reps = st.number_input(
                "Reps per Set Target", min_value=1, max_value=50, key="plan_reps", step=1
            )

        st.markdown('<div style="height: 0.5rem;"></div>', unsafe_allow_html=True)

        if not workout_started:
            st.button("▶  Start Workout Session", key="setup_start_btn", type="primary", on_click=_start_workout_session, use_container_width=True)
        else:
            st.button("⏹  Stop Workout Session", key="setup_stop_btn", on_click=_stop_workout_session, use_container_width=True)


# ── Workout History Table (Row 4) ─────────────────────────────────────────────
def _render_history_table(user_id: int) -> None:
    col_hdr, col_exp = st.columns([3, 1])
    with col_hdr:
        st.markdown('<div class="dev-card-title" style="margin: 1.5rem 0 0.75rem;">Workout History</div>', unsafe_allow_html=True)

    rows = get_users_exercises(user_id) if user_id else []

    if rows:
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
        with col_exp:
            st.markdown('<div style="height: 1.5rem;"></div>', unsafe_allow_html=True)
            csv_data = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Export CSV",
                data=csv_data,
                file_name=f"gymguru_workout_history.csv",
                mime="text/csv",
                key="export_csv_btn",
                use_container_width=True,
            )
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        with col_exp:
            st.markdown('<div style="height: 1.5rem;"></div>', unsafe_allow_html=True)
            st.button("📥 Export CSV", key="export_csv_disabled", disabled=True, use_container_width=True)
        st.markdown("""
<div style="background: #161B22; border: 1px solid #30363D; border-radius: 8px; padding: 2rem; text-align: center; color: #9CA3AF; font-size: 0.88rem;">
  No workouts recorded yet. Start a session to log metrics into SQLite.
</div>
""", unsafe_allow_html=True)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(
        page_icon="🏋️",
        page_title="GymGuru — AI Fitness Coach",
        initial_sidebar_state="collapsed",
        layout="wide",
    )

    base_dir = os.path.dirname(os.abspath(__file__)) if hasattr(os, 'abspath') else os.path.dirname(__file__)
    load_css(os.path.join(base_dir, "static", "style.css"))
    inject_local_font(os.path.join(base_dir, "static", "AdobeClean.otf"), "AdobeClean")

    init_db()

    if not render_login_wall():
        return

    initial_session_defaults()

    if "voice_pipeline" not in st.session_state or st.session_state.voice_pipeline is None:
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

    # Top Header
    _render_top_header(username)

    # First Row: 4 Stat Cards
    _render_stat_cards(user_id, workout_started)

    st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)

    # Second Row: Camera (68%) & AI Coach (32%)
    col_left, col_right = st.columns([2.1, 1.0], gap="large")

    ex      = st.session_state.get("exercise_type", st.session_state.get("plan_exercise", "Squats"))
    t_sets  = st.session_state.get("target_sets", 3)
    rps     = st.session_state.get("reps_per_set", 10)
    s_done  = st.session_state.get("sets_completed", 0)
    cs_reps = st.session_state.get("current_set_reps", 0)

    with col_left:
        # Reliable timer computation
        elapsed_sec = st.session_state.get("elapsed_seconds", 0)
        if workout_started and st.session_state.get("workout_start_time", 0.0) > 0.0:
            elapsed_sec = int(time.time() - st.session_state.workout_start_time)
            st.session_state.elapsed_seconds = elapsed_sec

        m = elapsed_sec // 60
        s = elapsed_sec % 60
        elapsed_str = f"{m:02d}:{s:02d}"

        # Top camera status banner
        st.markdown(f"""
<div id="live-camera-section" style="background: #161B22; border: 1px solid #30363D; border-radius: 6px; padding: 0.75rem 1rem; margin-bottom: 0.75rem; display: flex; justify-content: space-between; align-items: center;">
  <div style="font-size: 1.15rem; font-weight: 800; color: #FFFFFF;">🎥 Live Camera — {ex}</div>
  <div style="display: flex; gap: 1.5rem; font-size: 0.88rem; color: #9CA3AF;">
    <span>Target: <strong>{t_sets} sets × {rps} reps</strong></span>
    <span>Timer: <strong style="font-family: var(--font-mono); color: #7C5CFF;">⏱ {elapsed_str}</strong></span>
  </div>
</div>
""", unsafe_allow_html=True)

        if st.session_state.get("scroll_to_camera", False):
            st.markdown("""
<img src="x" onerror="try { const doc = window.parent ? window.parent.document : document; const el = doc.getElementById('live-camera-section') || document.getElementById('live-camera-section'); if (el) { el.scrollIntoView({ behavior: 'smooth', block: 'start' }); } else { window.scrollTo({ top: 0, behavior: 'smooth' }); } } catch(e) { window.scrollTo({ top: 0, behavior: 'smooth' }); }" style="display:none;">
""", unsafe_allow_html=True)
            st.session_state.scroll_to_camera = False

        is_playing = False
        if st.session_state.get("workout_completed", False) and not workout_started:
            st.markdown(f"""
<div style="background: linear-gradient(135deg, rgba(34, 197, 94, 0.18) 0%, rgba(13, 17, 23, 0.85) 100%); border: 1px solid #22C55E; border-radius: 6px; padding: 1rem 1.25rem; margin-bottom: 0.75rem; display: flex; justify-content: space-between; align-items: center;">
  <div>
    <div style="font-size: 1.15rem; font-weight: 800; color: #22C55E;">🎉 Workout Completed!</div>
    <div style="font-size: 0.85rem; color: #E6EDF3; margin-top: 0.25rem;">Great job! Reached target of <strong>{t_sets} sets × {rps} reps</strong> for <strong>{ex}</strong>.</div>
  </div>
  <div style="text-align: right;">
    <div style="font-size: 0.75rem; color: #9CA3AF; text-transform: uppercase; font-weight: 600;">Total Duration</div>
    <div style="font-size: 1.2rem; font-weight: 800; color: #FFFFFF; font-family: var(--font-mono);">⏱ {elapsed_str}</div>
  </div>
</div>
""", unsafe_allow_html=True)
        elif not workout_started:
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
            context = webrtc_streamer(
                key="exercise-analysis",
                mode=WebRtcMode.SENDRECV,
                video_processor_factory=VideoProcessorClass,
                rtc_configuration=get_rtc_configuration(),
                media_stream_constraints={"video": True, "audio": False},
                async_processing=True,
            )

            inject_webrtc_styles()
            sync_metrics_update(context)

            is_playing = bool(context and hasattr(context, "state") and context.state.playing)
            if context.state.playing:
                time.sleep(0.25)
                st.rerun()

        posture_text, posture_cls = _get_posture_status(ex, is_playing)

        if workout_started:
            pose_status_str = "● Tracking" if is_playing else "◌ Connecting..."
            pose_status_color = "#22C55E" if is_playing else "#F59E0B"
        else:
            pose_status_str = "○ Offline"
            pose_status_color = "#9CA3AF"

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
    <div style="font-size: 1.15rem; font-weight: 800; color: {pose_status_color}; margin-top: 0.15rem;">{pose_status_str}</div>
  </div>
</div>
""", unsafe_allow_html=True)

        if not workout_started:
            st.button("▶  Start Workout Session", key="cam_start_btn", type="primary", on_click=_start_workout_session, use_container_width=True)
        else:
            st.button("⏹  Stop Workout Session", key="cam_stop_btn", on_click=_stop_workout_session, use_container_width=True)

    with col_right:
        st.markdown('<div class="dev-card-title" style="margin-bottom: 0.75rem;">AI Coach</div>', unsafe_allow_html=True)

        is_speaking = bool(st.session_state.get("audio_to_play"))
        ai_status_text, ai_status_cls = _get_ai_status(is_speaking, is_playing)
        posture_text, posture_cls = _get_posture_status(st.session_state.get("exercise_type", "Squats"), is_playing)

        feedback = st.session_state.get("coach_feedback", "")
        if not feedback:
            feedback = "AI Coach is ready. Start a workout session to analyze posture and receive real-time voice guidance."

        status_dot = "🟢" if (workout_started and is_playing) else ("🟡" if workout_started else "⚪")
        status_text = "Active" if (workout_started and is_playing) else ("Connecting..." if workout_started else "Ready")
        voice_state = ai_status_text

        alignment_status = "Waiting for camera..." if (workout_started and not is_playing) else ("Checking..." if workout_started else "N/A")
        mistakes_status = "None" if workout_started else "N/A"
        ex_active = st.session_state.get("exercise_type", "Squats")

        if workout_started and is_playing:
            if ex_active == "Squats":
                alignment_status = st.session_state.get("depth_status", "N/A")
                if alignment_status == "TOO HIGH":
                    mistakes_status = "Squat depth too high"
            elif ex_active == "Push-ups":
                alignment_status = st.session_state.get("body_alignment", "N/A")
                hip_align = st.session_state.get("hip_status", "N/A")
                if alignment_status != "Straight" or hip_align != "LEVEL":
                    mistakes_status = f"{alignment_status} / {hip_align}"
            elif ex_active == "Biceps Curls (Dumbbell)":
                alignment_status = st.session_state.get("swing_status", "N/A")
                sh_align = st.session_state.get("shoulder_status", "N/A")
                if alignment_status == "SWINGING" or sh_align == "ELBOW DRIFTING":
                    mistakes_status = f"{alignment_status} / {sh_align}"
            elif ex_active == "Shoulder Press":
                alignment_status = st.session_state.get("back_arch_status", "N/A")
                ext_align = st.session_state.get("extension_status", "N/A")
                if alignment_status == "Excessive Arch":
                    mistakes_status = "Excessive back arch"
            elif ex_active == "Lunges":
                alignment_status = st.session_state.get("balance_status", "N/A")
                if alignment_status == "OFF BALANCE":
                    mistakes_status = "Off balance"

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
      <span style="font-size: 0.85rem; font-weight: 700; color: {'#F59E0B' if mistakes_status not in ['None', 'N/A'] else '#22C55E'};">{mistakes_status}</span>
    </div>
  </div>

  <div style="font-size: 0.72rem; color: #6E7681; font-weight: 700; text-transform: uppercase; margin-bottom: 0.4rem; letter-spacing: 0.05em;">LATEST FEEDBACK</div>
  <div style="font-size: 0.92rem; color: #E6EDF3; line-height: 1.5; background: #0D1117; border: 1px solid #30363D; border-radius: 6px; padding: 1rem;">
    "{feedback}"
  </div>
</div>
""", unsafe_allow_html=True)

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

    if st.session_state.get("audio_to_play"):
        autoplay_audio(st.session_state.audio_to_play)
        st.session_state.audio_to_play = None

    _render_workout_setup(workout_started)

    if isinstance(user_id, int):
        _render_history_table(user_id)

    st.markdown("""
<div class="dev-footer">
  <div class="dev-footer-copy">GymGuru &copy; 2026 &nbsp;·&nbsp; AI Fitness Coach &nbsp;·&nbsp; Data stored locally in SQLite</div>
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
