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


# ── Helper: Centered Hero ─────────────────────────────────────────────────────
def _hero(quote: str) -> None:
    st.markdown(f"""
<div class="gg-hero">
  <div class="gg-hero-badge">
    <span>🤖</span> AI &nbsp;·&nbsp; Real-Time Pose Detection &nbsp;·&nbsp; Voice Coach
  </div>
  <div class="gg-hero-subtitle">AI Powered Real‑Time Personal Fitness Coach</div>
  <h1 class="gg-hero-title">Gym<span class="title-gradient">Guru</span></h1>
  <div class="gg-hero-tagline">Train Smarter with AI</div>
  <div class="gg-hero-quote">&ldquo;{quote}&rdquo;</div>
</div>
""", unsafe_allow_html=True)


# Login Card is styled directly via div[data-testid="stForm"] in style.css


# ── Helper: feature section ───────────────────────────────────────────────────
def _features() -> None:
    items = [
        ("🎯", "Know Your Form, Every Rep",
         "33 MediaPipe pose landmarks analyze every movement in real time "
         "and flag form errors before they become injuries."),
        ("🔊", "A Coach That Never Stops Watching",
         "Groq-powered LLM delivers live audio cues, set-by-set feedback "
         "and motivational calls mid-rep — hands-free."),
        ("📈", "See Your Progress, Session by Session",
         "Every rep, set and second is logged automatically. "
         "Your history grows every time you train."),
        ("🛡️", "Correct It Before It Hurts",
         "Real-time posture scoring catches back arch, knee collapse "
         "and swing errors the moment they happen."),
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
  <div class="gg-features-heading">Built for Serious Athletes. Accessible to Everyone.</div>
  <div class="gg-features-sub">
    Four capabilities working simultaneously so you can focus on the lift, not the laptop.
  </div>
  <div class="gg-features-grid">
    {cards_html}
  </div>
</div>
""", unsafe_allow_html=True)


# ── Helper: exercise list ─────────────────────────────────────────────────────
def _exercises() -> None:
    items = [
        ("🦵", "Squats"),
        ("💪", "Push-ups"),
        ("🏋️", "Biceps Curls"),
        ("🙌", "Shoulder Press"),
        ("🚶", "Lunges"),
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
  <div class="gg-exercises-label">AI-Tracked Exercises</div>
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
      <div class="gg-stat-icon">🏋️</div>
      <div class="gg-stat-value">5</div>
      <div class="gg-stat-label">Exercises</div>
    </div>
    <div class="gg-stat-col">
      <div class="gg-stat-icon">⚡</div>
      <div class="gg-stat-value">&lt;1s</div>
      <div class="gg-stat-label">Feedback</div>
    </div>
    <div class="gg-stat-col">
      <div class="gg-stat-icon">🔊</div>
      <div class="gg-stat-value">AI Coach</div>
      <div class="gg-stat-label">Voice Feedback</div>
    </div>
    <div class="gg-stat-col">
      <div class="gg-stat-icon">📅</div>
      <div class="gg-stat-value">∞</div>
      <div class="gg-stat-label">Sessions</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Helper: CTA Banner ────────────────────────────────────────────────────────
def _cta() -> None:
    st.markdown("""
<div class="gg-cta-banner">
  <div class="gg-cta-left">
    <div class="gg-cta-badge">Ready to transform?</div>
    <h2 class="gg-cta-title">Your Best Workout Starts Here</h2>
    <div class="gg-cta-subtitle">Join thousands of athletes training smarter with AI</div>
  </div>
  <div class="gg-cta-right">
    <a href="#login-card" class="gg-cta-btn">Start Your First Workout &rarr;</a>
    <div class="gg-cta-note">No sign up required</div>
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

    # 1 ── Full-bleed hero
    _hero(quote)

    # ── THE FORM — all keys preserved ────────────────────────────────────────
    with st.form("login_form", clear_on_submit=False):
        st.markdown("""
        <div class="gg-login-header" id="login-card">
          <div class="gg-login-title">👋 Welcome to GymGuru!</div>
          <div class="gg-login-desc">
            Pick a username and start training — your history is saved automatically.
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
            <span>🔒</span> Your workout data is stored locally and never shared.
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
