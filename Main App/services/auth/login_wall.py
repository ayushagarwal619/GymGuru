"""
login_wall.py — GymGuru Landing / Login Page  (VISUAL REDESIGN ONLY)
────────────────────────────────────────────────────────────────────
Auth logic is 100% unchanged:  get_or_create_user(), session_state
keys "user_id" / "username", form key "login_form" — all preserved.
Only HTML wrappers and helper functions are new.
"""

import random
import streamlit as st
from services.persistence.exercise_repository import get_or_create_user

# ── Motivational quotes (one per page-load) ───────────────────────────────────
_QUOTES = [
    "Train Smarter. Not Harder.",
    "Every Rep Counts.",
    "Discipline Beats Motivation.",
    "The Best Project You'll Ever Work On Is Yourself.",
    "Strong Mind. Strong Body.",
    "One Rep Closer.",
    "Know Exactly What to Lift.",
    "Your Form Is Your Foundation.",
    "Push Past Yesterday's Limits.",
    "Consistency Is The Secret Weapon.",
]


# ── Helper: Navbar ───────────────────────────────────────────────────────────
def _navbar() -> None:
    st.markdown("""
<header class="gg-navbar">
  <div class="gg-navbar-container">
    <a href="#" class="gg-navbar-brand">
      <span class="gg-navbar-logo">🏋️</span>
      <span class="gg-navbar-title">GymGuru</span>
    </a>
    <div class="gg-navbar-menu">
      <a href="#features" class="gg-navbar-link">Features</a>
      <a href="#how-it-works" class="gg-navbar-link">How It Works</a>
      <a href="#about" class="gg-navbar-link">About</a>
    </div>
    <div class="gg-navbar-cta">
      <a href="#login-card" class="gg-navbar-btn">Get Started &rarr;</a>
    </div>
  </div>
</header>
""", unsafe_allow_html=True)


# ── Helper: Hero Column ───────────────────────────────────────────────────────
def _hero() -> None:
    st.markdown("""
<div class="gg-hero-left">
  <div class="gg-hero-badge">
    <span>🤖</span> AI POWERED FITNESS COACH
  </div>
  <h1 class="gg-hero-title">Gym<span class="title-gradient">Guru</span></h1>
  <div class="gg-hero-subtitle">Your AI Coach. Your Best Training Partner.</div>
  
  <div class="gg-hero-benefits">
    <div class="gg-benefit-row">
      <div class="gg-benefit-icon-wrap">🧍</div>
      <div class="gg-benefit-content">
        <div class="gg-benefit-title">Real-time Posture Correction</div>
        <div class="gg-benefit-desc">33 MediaPipe landmarks analyze your every move and help you train with perfect form.</div>
      </div>
    </div>
    <div class="gg-benefit-row">
      <div class="gg-benefit-icon-wrap">🔊</div>
      <div class="gg-benefit-content">
        <div class="gg-benefit-title">AI Voice Coaching</div>
        <div class="gg-benefit-desc">Groq-powered live voice feedback keeps you motivated and on track.</div>
      </div>
    </div>
    <div class="gg-benefit-row">
      <div class="gg-benefit-icon-wrap">📈</div>
      <div class="gg-benefit-content">
        <div class="gg-benefit-title">Automatic Workout Tracking</div>
        <div class="gg-benefit-desc">Every rep, set and second is logged automatically. Track progress, stay consistent, get stronger.</div>
      </div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# Login Card is styled directly via div[data-testid="stForm"] in style.css


# ── Helper: feature section ───────────────────────────────────────────────────
def _features() -> None:
    items = [
        ("🎯", "Perfect Your Form",
         "33 MediaPipe landmarks analyze every rep in real time to detect posture mistakes."),
        ("🔊", "AI Voice Coach",
         "Groq-powered voice coaching delivers live feedback and keeps you motivated."),
        ("📈", "Track Every Workout",
         "Automatically save reps, sets, and duration to monitor your progress over time."),
        ("🛡️", "Prevent Injuries",
         "Detect common mistakes instantly and train safely with real-time form corrections."),
    ]
    
    cards_html = "".join(f"""
    <div class="gg-feature-card">
      <div class="gg-feature-icon">{icon}</div>
      <div class="gg-feature-title">{title}</div>
      <div class="gg-feature-desc">{desc}</div>
    </div>
""" for icon, title, desc in items)

    st.markdown(f"""
<div id="features">
  <div class="gg-features-heading">Why GymGuru?</div>
  <div class="gg-features-grid">
    {cards_html}
  </div>
</div>
""", unsafe_allow_html=True)


# ── Helper: exercise list ─────────────────────────────────────────────────────
def _exercises() -> None:
    items = [
        ("🏋️", "Squats"),
        ("🏃", "Push-ups"),
        ("🧗", "Pull-ups"),
        ("🏋️", "Deadlifts"),
        ("💪", "Bench Press"),
        ("🙌", "Shoulder Press"),
        ("🚶", "Lunges"),
        ("🧘", "Plank"),
    ]
    cards = "".join(
        f'<div class="gg-exercise-chip">'
        f'<span class="gg-exercise-icon">{e}</span>'
        f'<span class="gg-exercise-name">{n}</span>'
        f'</div>'
        for e, n in items
    )
    st.markdown(f"""
<div class="gg-exercises-section" id="how-it-works">
  <div class="gg-exercises-label">Popular Exercises</div>
  <div class="gg-exercises-grid">{cards}</div>
</div>
""", unsafe_allow_html=True)


def _stats() -> None:
    st.markdown("""
<div class="gg-stats-card" id="about">
  <div class="gg-stats-grid">
    <div class="gg-stat-col">
      <div class="gg-stat-icon">🏃</div>
      <div class="gg-stat-value">33</div>
      <div class="gg-stat-label">Pose Landmarks</div>
    </div>
    <div class="gg-stat-col">
      <div class="gg-stat-icon">⚡</div>
      <div class="gg-stat-value">5</div>
      <div class="gg-stat-label">AI Models</div>
    </div>
    <div class="gg-stat-col">
      <div class="gg-stat-icon">⏱️</div>
      <div class="gg-stat-value">&lt;1s</div>
      <div class="gg-stat-label">Response Time</div>
    </div>
    <div class="gg-stat-col">
      <div class="gg-stat-icon">🧠</div>
      <div class="gg-stat-value">AI Coach</div>
      <div class="gg-stat-label">Powered by Groq</div>
    </div>
    <div class="gg-stat-col">
      <div class="gg-stat-icon">🗄️</div>
      <div class="gg-stat-value">∞</div>
      <div class="gg-stat-label">Possibilities</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Helper: CTA Banner ────────────────────────────────────────────────────────
def _cta() -> None:
    st.markdown("""
<div class="gg-cta-banner">
  <div class="gg-cta-left">
    <h2 class="gg-cta-title">Ready to start?</h2>
    <div class="gg-cta-subtitle">Your AI coach is waiting.</div>
  </div>
  <div class="gg-cta-right">
    <a href="#login-card" class="gg-cta-btn">Start Training &rarr;</a>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Helper: footer ────────────────────────────────────────────────────────────
def _footer() -> None:
    techs = [
        ("🐍", "Python"), ("🖐", "MediaPipe"), ("📷", "OpenCV"),
        ("🤖", "Groq"), ("🗄", "SQLite"), ("⚡", "Streamlit"),
    ]
    chips = "".join(
        f'<div class="gg-tech-chip"><span>{i}</span>{n}</div>'
        for i, n in techs
    )
    st.markdown(f"""
<div class="gg-footer">
  <div class="gg-footer-grid">
    <div class="gg-footer-col">
      <div class="gg-footer-logo-wrap">
        <span class="gg-footer-logo">🏋️</span>
        <span class="gg-footer-brand">GymGuru</span>
      </div>
      <div class="gg-footer-desc">
        AI Powered Real-Time Personal Fitness Coach that helps you train smarter, safer, and stronger every day.
      </div>
    </div>
    <div class="gg-footer-col">
      <div class="gg-footer-title">Quick Links</div>
      <a href="#features" class="gg-footer-link">Features</a>
      <a href="#how-it-works" class="gg-footer-link">How It Works</a>
      <a href="#about" class="gg-footer-link">About</a>
    </div>
    <div class="gg-footer-col">
      <div class="gg-footer-title">Connect</div>
      <a href="https://github.com" target="_blank" class="gg-footer-link">GitHub</a>
      <a href="#" class="gg-footer-link">Documentation</a>
      <a href="#" class="gg-footer-link">Support</a>
    </div>
  </div>
  <div class="gg-tech-row">
    {chips}
  </div>
  <div class="gg-footer-bottom">
    <div class="gg-footer-copy">&copy; 2024 GymGuru. All rights reserved.</div>
    <div class="gg-footer-heart">Built with <span>&hearts;</span> and AI</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Public entry-point (called by main.py) ────────────────────────────────────
def render_login_wall() -> bool:
    """
    Returns True  → user already authenticated, show dashboard.
    Returns False → render login/landing page.

    AUTH LOGIC UNCHANGED:
      - get_or_create_user()
      - st.session_state["user_id"]
      - st.session_state["username"]
      - st.form("login_form")
    """
    if st.session_state.get("user_id") is not None:
        return True

    quote = random.choice(_QUOTES)

    # 0 ── Navbar
    _navbar()

    # 1 ── Hero + Login Card columns (unified top section)
    col1, col2 = st.columns([1.2, 1], gap="large")

    with col1:
        _hero()

    with col2:
        # ── THE FORM — all keys preserved ────────────────────────────────────────
        with st.form("login_form", clear_on_submit=False):
            st.markdown("""
            <div class="gg-login-header" id="login-card">
              <div class="gg-login-title">👋 Welcome to GymGuru!</div>
              <div class="gg-login-desc">
                Enter your username to continue your fitness journey.
              </div>
            </div>
            """, unsafe_allow_html=True)

            username = st.text_input(
                "👤  Username",
                placeholder="e.g. alexsmith",
                help="Your workout history will be saved automatically.",
            )

            submit = st.form_submit_button(
                "Start Training  &rarr;",
                use_container_width=True,
            )

            st.markdown("""
            <div class="gg-login-footer">
              <div class="gg-privacy-note">
                <span>🔒</span> Your data is stored locally and stays private.
              </div>
            </div>
            """, unsafe_allow_html=True)

    if submit:
        if not username.strip():
            st.error("Username cannot be empty.")
            return False
        user = get_or_create_user(username.strip())   # ← auth logic unchanged
        st.session_state["user_id"]  = user["id"]
        st.session_state["username"] = user["username"]
        st.rerun()

    # 3 ── Features
    _features()

    # 4 ── Exercise list
    _exercises()

    # 5 ── Stats strip
    _stats()

    # 5.5 ── CTA Banner
    _cta()

    # 6 ── Footer
    _footer()

    return False
