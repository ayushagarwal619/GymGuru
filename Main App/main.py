"""
main.py — GymGuru Dashboard  (VISUAL REDESIGN ONLY)
────────────────────────────────────────────────────────────────────
ALL logic is 100% unchanged:
  WebRTC key "exercise-analysis", all st.session_state keys,
  all widget keys, rep-counting, voice pipeline, persistence.
Only HTML/CSS wrappers and helper render functions are new.
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


# ── Section label helper ──────────────────────────────────────────────────────
def _section(label: str) -> None:
    st.markdown(f"""
<div class="gg-section-row">
  <span class="gg-section-lbl">{label}</span>
  <div class="gg-section-line"></div>
</div>
""", unsafe_allow_html=True)


# ── AI Coach card ─────────────────────────────────────────────────────────────
def _coach_card(feedback: str, speaking: bool) -> None:
    pulse = "speaking" if speaking else ""
    st.markdown(f"""
<div class="gg-coach-card">
  <div class="gg-coach-av {pulse}">🤖</div>
  <div style="flex:1;min-width:0;">
    <div class="gg-coach-tag">AI Coach &nbsp;·&nbsp; GymGuru</div>
    <div class="gg-coach-msg">{feedback}</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Workout history (premium cards) ──────────────────────────────────────────
def _render_history(user_id: int) -> None:
    _section("Workout History")

    rows = get_users_exercises(user_id)
    arr = [
        {
            "Exercise": r["exercise_name"],
            "Reps":     r["reps"],
            "Sets":     r["sets"],
            "Time":     r["time"],
            "Date":     r["created_at"],
        }
        for r in rows
    ]
    df = pd.DataFrame(arr)

    if df.empty:
        st.markdown("""
<div style="text-align:center;padding:3rem 1rem;color:#475569;font-size:0.9rem;">
  No sessions logged yet — complete a workout to see history here.
</div>
""", unsafe_allow_html=True)
        return

    df["Date"] = pd.to_datetime(df["Date"]).dt.date
    agg = (
        df.groupby(["Exercise", "Date"])
        .agg(Reps=("Reps","sum"), Sets=("Sets","sum"), Time=("Time","sum"))
        .reset_index()
        .sort_values("Date", ascending=False)
    )

    for _, row in agg.iterrows():
        m = int(row["Time"] // 60)
        s = int(row["Time"] % 60)
        dur = f"{m}m {s}s" if m else f"{s}s"
        st.markdown(f"""
<div class="gg-hist-card">
  <div>
    <div class="gg-hist-name">{row['Exercise']}</div>
    <div class="gg-hist-date">{row['Date']}</div>
  </div>
  <div class="gg-hist-badges">
    <span class="gg-badge">{int(row['Reps'])} reps</span>
    <span class="gg-badge gg-badge-g">{int(row['Sets'])} sets</span>
    <span class="gg-badge gg-badge-p">⏱ {dur}</span>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Sidebar ───────────────────────────────────────────────────────────────────
def _sidebar(workout_started: bool) -> None:
    with st.sidebar:
        # Brand
        st.markdown("""
<div style="display:flex;align-items:center;gap:0.6rem;padding:0.5rem 0 1.25rem;">
  <span style="font-size:1.5rem;">🏋️</span>
  <div>
    <div style="font-size:1rem;font-weight:900;color:#fff;letter-spacing:-0.03em;">GymGuru</div>
    <div style="font-size:0.62rem;color:#475569;text-transform:uppercase;letter-spacing:0.1em;">
      AI Fitness Coach
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

        if st.session_state.get("username"):
            st.markdown(f"""
<div style="background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.18);
     border-radius:8px;padding:0.5rem 0.8rem;margin-bottom:1rem;
     font-size:0.8rem;color:#94A3B8;">
  👤 &nbsp;<strong style="color:#fff;">{st.session_state.username}</strong>
</div>
""", unsafe_allow_html=True)

        st.divider()

        # Workout plan label
        st.markdown("""
<div class="gg-section-row" style="margin-top:0;margin-bottom:0.75rem;">
  <span class="gg-section-lbl">Workout Plan</span>
  <div class="gg-section-line"></div>
</div>
""", unsafe_allow_html=True)

        if not workout_started:
            # ── All widget keys are unchanged ─────────────────────────────
            plan_exercise = st.selectbox(
                "Exercise", options=EXERCISE_OPTIONS, key="plan_exercise"
            )
            plan_sets = st.number_input(
                "Sets", min_value=0, max_value=50, key="plan_sets", step=1
            )
            plan_reps = st.number_input(
                "Reps per Set", min_value=0, max_value=50, key="plan_reps", step=1
            )
            st.markdown("<div style='height:0.4rem'></div>", unsafe_allow_html=True)

            start_session_button = st.button(
                "▶  Start Workout",
                use_container_width=True,
                key="start_session_button",
            )

            if start_session_button:
                st.session_state.exercise_type  = plan_exercise
                st.session_state.target_sets    = int(plan_sets)
                st.session_state.reps_per_set   = int(plan_reps)
                st.session_state.reps           = 0
                st.session_state.workout_started = True
                st.session_state.set_cycle_started_at      = time.time()
                st.session_state.last_saved_sets_completed  = 0

                if st.session_state.voice_pipeline:
                    result = st.session_state.voice_pipeline.process_event(
                        event="workout_started",
                        exercise=plan_exercise,
                        metrics={},
                    )
                    if result:
                        st.session_state.audio_to_play   = result[0]
                        st.session_state.coach_feedback  = result[1]

                st.session_state.last_notified_sets_completed    = 0
                st.session_state.last_notified_workout_complete  = False
                st.rerun()

        else:
            ex   = st.session_state.get("exercise_type")
            sets = st.session_state.get("target_sets")
            reps = st.session_state.get("reps_per_set")

            st.markdown(f"""
<div style="background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.2);
     border-radius:10px;padding:0.8rem 1rem;margin-bottom:0.9rem;">
  <div style="font-size:0.65rem;color:#475569;text-transform:uppercase;
              letter-spacing:0.1em;margin-bottom:0.25rem;">Active Session</div>
  <div style="font-size:1rem;font-weight:800;color:#fff;">{ex}</div>
  <div style="font-size:0.75rem;color:#94A3B8;margin-top:0.15rem;">
    {sets} sets &nbsp;·&nbsp; {reps} reps
  </div>
</div>
""", unsafe_allow_html=True)

            end_session_button = st.button(
                "⏹  End Workout",
                key="end_session_button",
                use_container_width=True,
            )

            if end_session_button:
                st.session_state.workout_started = False
                if st.session_state.voice_pipeline:
                    result = st.session_state.voice_pipeline.process_event(
                        event="workout_completed", exercise=ex, metrics={}
                    )
                    if result:
                        st.session_state.audio_to_play  = result[0]
                        st.session_state.coach_feedback = result[1]
                st.rerun()

        # ── Live metrics during workout ────────────────────────────────────
        if workout_started:
            st.divider()
            st.markdown("""
<div class="gg-section-row" style="margin-top:0;margin-bottom:0.75rem;">
  <span class="gg-section-lbl">Live Progress</span>
  <div class="gg-section-line"></div>
</div>
""", unsafe_allow_html=True)

            ex      = st.session_state.get("exercise_type")
            t_reps  = st.session_state.get("reps")
            cs_reps = st.session_state.get("current_set_reps")
            rps     = st.session_state.get("reps_per_set")
            s_done  = st.session_state.get("sets_completed")
            t_sets  = st.session_state.get("target_sets")

            st.metric("Total Reps",     t_reps)
            st.metric("Set Reps",       f"{cs_reps} / {rps}")
            st.metric("Sets Completed", f"{s_done} / {t_sets}")

            st.divider()

            # Exercise-specific metrics — all session_state keys unchanged
            if ex == "Squats":
                st.markdown("""<div class="gg-section-row" style="margin-top:0;"><span class="gg-section-lbl">Squat Metrics</span><div class="gg-section-line"></div></div>""", unsafe_allow_html=True)
                st.metric("Knee Angle",  f"{st.session_state.knee_angle}°")
                st.metric("Back Angle",  f"{st.session_state.back_angle}°")
                st.metric("Depth",       st.session_state.depth_status)

            elif ex == "Push-ups":
                st.markdown("""<div class="gg-section-row" style="margin-top:0;"><span class="gg-section-lbl">Push-up Metrics</span><div class="gg-section-line"></div></div>""", unsafe_allow_html=True)
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Alignment",   st.session_state.body_alignment)
                st.metric("Hips",        st.session_state.hip_status)

            elif ex == "Biceps Curls (Dumbbell)":
                st.markdown("""<div class="gg-section-row" style="margin-top:0;"><span class="gg-section-lbl">Curl Metrics</span><div class="gg-section-line"></div></div>""", unsafe_allow_html=True)
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Shoulder",    st.session_state.shoulder_status)
                st.metric("Swing",       st.session_state.swing_status)

            elif ex == "Shoulder Press":
                st.markdown("""<div class="gg-section-row" style="margin-top:0;"><span class="gg-section-lbl">Press Metrics</span><div class="gg-section-line"></div></div>""", unsafe_allow_html=True)
                st.metric("Elbow Angle", f"{st.session_state.elbow_angle}°")
                st.metric("Extension",   st.session_state.extension_status)
                st.metric("Back Arch",   st.session_state.back_arch_status)

            elif ex == "Lunges":
                st.markdown("""<div class="gg-section-row" style="margin-top:0;"><span class="gg-section-lbl">Lunge Metrics</span><div class="gg-section-line"></div></div>""", unsafe_allow_html=True)
                st.metric("Front Knee",  f"{st.session_state.front_knee_angle}°")
                st.metric("Torso",       f"{st.session_state.torso_angle}°")
                st.metric("Balance",     st.session_state.balance_status)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    st.set_page_config(
        page_icon="🏋️",
        page_title="GymGuru — AI Fitness Coach",
        initial_sidebar_state="expanded",
        layout="wide",
    )

    # CSS + font (calls unchanged)
    load_css(os.path.join(os.getcwd(), "static", "style.css"))
    inject_local_font(os.path.join(os.getcwd(), "static", "AdobeClean.otf"), "AdobeClean")

    init_db()

    # Auth gate — unchanged logic
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

    # Sidebar
    _sidebar(workout_started)

    # ── Dashboard header ──────────────────────────────────────────────────
    live_html = ""
    if workout_started:
        live_html = """
  <span class="gg-live-pill">
    <span class="gg-live-dot"></span>Live
  </span>"""

    st.markdown(f"""
<div class="gg-dash-header gg-fadeup">
  <div class="gg-dash-brand">
    <span style="font-size:1.8rem;">🏋️</span>
    <span class="gg-dash-wordmark">GymGuru</span>
    {live_html}
  </div>
  <div class="gg-dash-sub">
    AI Powered Real‑Time Personal Fitness Coach &nbsp;·&nbsp; Train Smarter with AI
  </div>
</div>
""", unsafe_allow_html=True)

    # ── Audio autoplay (logic unchanged) ─────────────────────────────────
    if st.session_state.get("audio_to_play"):
        autoplay_audio(st.session_state.audio_to_play)

    # ── AI Coach card ─────────────────────────────────────────────────────
    feedback = st.session_state.get("coach_feedback", "")
    if feedback:
        _section("AI Coach")
        _coach_card(feedback, is_speaking=True)

    # ── Camera feed / placeholder ─────────────────────────────────────────
    if not workout_started:
        st.markdown("""
<div class="gg-placeholder gg-fadeup2">
  <div class="gg-placeholder-icon">🎯</div>
  <div class="gg-placeholder-title">Ready When You Are</div>
  <div class="gg-placeholder-body">
    Choose your exercise, sets and reps in the sidebar,
    then hit <strong style="color:#fff;">Start Workout</strong>
    to activate the camera and AI coach.
  </div>
</div>
""", unsafe_allow_html=True)

    else:
        _section("Camera Feed")

        # WebRTC — completely unchanged call, key unchanged
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

        # Metrics sync (logic unchanged)
        sync_metrics_update(context)

        # Rerun loop (logic unchanged)
        if context.state.playing:
            time.sleep(0.25)
            st.rerun()

        inject_webrtc_styles()

    st.divider()

    # ── Workout history ───────────────────────────────────────────────────
    user_id = st.session_state.get("user_id", 0)
    if isinstance(user_id, int):
        _render_history(user_id)

    # ── Footer ────────────────────────────────────────────────────────────
    techs = [
        ("🐍","Python"), ("🖐","MediaPipe"), ("📷","OpenCV"),
        ("🤖","Groq"),   ("🗄","SQLite"),    ("⚡","Streamlit"),
    ]
    chips = "".join(
        f'<div class="gg-tech-chip"><span>{i}</span>{n}</div>'
        for i, n in techs
    )
    st.markdown(f"""
<div class="gg-footer">
  <div class="gg-footer-copy">GymGuru &copy; 2024 &nbsp;·&nbsp; All workout data stored locally</div>
  <div class="gg-tech-row">{chips}</div>
</div>
""", unsafe_allow_html=True)


if __name__ == "__main__":
    main()
