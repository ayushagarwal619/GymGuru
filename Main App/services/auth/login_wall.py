"""
login_wall.py — GymGuru Landing / Login Page (v2 Complete Product Showcase)
────────────────────────────────────────────────────────────────────
Auth logic is 100% unchanged:  get_or_create_user(), session_state
keys "user_id" / "username", form key "login_form" — preserved.
"""

import base64
import os
import random
import streamlit as st
from services.persistence.exercise_repository import get_or_create_user

def _get_base64_logo() -> str:
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        logo_path = os.path.join(base_dir, "static", "logo.jpg")
        with open(logo_path, "rb") as f:
            return f"data:image/jpeg;base64,{base64.b64encode(f.read()).decode()}"
    except Exception:
        return "/app/static/logo.jpg"

_LOGO_URI = _get_base64_logo()


# ── Section 1: Sticky Navbar ──────────────────────────────────────────────────
def _navbar() -> None:
    html = f"""
<header class="gg-navbar">
  <div class="gg-navbar-container">
    <a href="#" class="gg-navbar-brand">
      <img src="{_LOGO_URI}" class="gg-navbar-logo-img" alt="GymGuru Logo">
      <span class="gg-navbar-title">GymGuru</span>
    </a>
    <div class="gg-navbar-menu">
      <a href="#exercises" class="gg-navbar-link">Exercises</a>
      <a href="#how-it-works" class="gg-navbar-link">Workflow</a>
      <a href="#features" class="gg-navbar-link">Features</a>
      <a href="#technology" class="gg-navbar-link">Technology</a>
      <a href="https://github.com" target="_blank" class="gg-navbar-link">GitHub</a>
    </div>
    <div class="gg-navbar-cta">
      <a href="#login-card" class="gg-navbar-btn">Start Training</a>
    </div>
  </div>
</header>
"""
    st.markdown(html.replace('\n', ''), unsafe_allow_html=True)


# ── Section 2: Large Hero (Left text column) ──────────────────────────────────
def _hero_left() -> None:
    html = """
<div class="gg-hero-left animated-fade-in">
  <div class="gg-hero-badge">
    <span>🤖</span> AI POWERED FITNESS COACH
  </div>
  <h1 class="gg-hero-title">Gym<span class="title-gradient">Guru</span></h1>
  <div class="gg-hero-subtitle">Your AI Coach. Your Best Training Partner.</div>
  
  <p class="gg-hero-p">
    Experience real-time posture analysis, rep counting, and voice feedback guided by MediaPipe computer vision and Groq AI directly on your browser.
  </p>
  
  <div class="gg-hero-actions">
    <a href="#login-card" class="gg-btn-primary">Start Training</a>
    <a href="#exercises" class="gg-btn-secondary">Learn More</a>
  </div>
</div>
"""
    st.markdown(html.replace('\n', ''), unsafe_allow_html=True)


# ── Section 3: Centered Motivational Quotes ────────────────────────────────────
def _quotes() -> None:
    html = """
<div class="gg-quote-section">
  <div class="gg-quote-container">
    <div class="gg-quote-icon">“</div>
    <div class="quote-slider-text"></div>
  </div>
</div>
"""
    st.markdown(html.replace('\n', ''), unsafe_allow_html=True)


# ── Section 4: Supported Exercises (High Priority) ───────────────────────────
def _exercises() -> None:
    items = [
        {
            "icon": "🏋️",
            "name": "Squats",
            "desc": "Perfect your knee angle and lower back alignment.",
            "muscles": "Quads, Glutes, Hamstrings",
            "difficulty": "Beginner",
            "ai": "Yes"
        },
        {
            "icon": "🏃",
            "name": "Push-ups",
            "desc": "Optimize chest depth and straight-back form.",
            "muscles": "Chest, Triceps, Anterior Deltoids",
            "difficulty": "Intermediate",
            "ai": "Yes"
        },
        {
            "icon": "💪",
            "name": "Biceps Curls (Dumbbell)",
            "desc": "Avoid arm swing and elbow travel.",
            "muscles": "Biceps Brachii, Brachialis",
            "difficulty": "Beginner",
            "ai": "Yes"
        },
        {
            "icon": "🙌",
            "name": "Shoulder Press",
            "desc": "Analyze overhead extension and spine arching.",
            "muscles": "Deltoids, Upper Pectorals, Triceps",
            "difficulty": "Intermediate",
            "ai": "Yes"
        },
        {
            "icon": "🚶",
            "name": "Lunges",
            "desc": "Maintain balance and proper step distance.",
            "muscles": "Quads, Glutes, Calves",
            "difficulty": "Beginner",
            "ai": "Yes"
        }
    ]

    cards_html = "".join(f"""
<div class="gg-exercise-card-modern">
  <div class="gg-ex-badge-ai">🤖 AI SUPPORTED</div>
  <div class="gg-ex-icon-modern">{item["icon"]}</div>
  <h3 class="gg-ex-name-modern">{item["name"]}</h3>
  <p class="gg-ex-desc-modern">{item["desc"]}</p>
  <div class="gg-ex-details-modern">
    <div class="gg-ex-detail-row">
      <span class="detail-label">Target:</span>
      <span class="detail-value">{item["muscles"]}</span>
    </div>
    <div class="gg-ex-detail-row">
      <span class="detail-label">Difficulty:</span>
      <span class="detail-value text-accent">{item["difficulty"]}</span>
    </div>
  </div>
</div>
""" for item in items)

    html = f"""
<div class="gg-section" id="exercises">
  <div class="gg-section-label">PRODUCT SHOWCASE</div>
  <h2 class="gg-section-title">Supported Exercises</h2>
  <p class="gg-section-subtitle-text">Train with real-time pose classification models calibrated for exact posture tracking.</p>
  <div class="gg-exercises-showcase-grid">{cards_html}</div>
</div>
"""
    st.markdown(html.replace('\n', ''), unsafe_allow_html=True)


# ── Section 5: How GymGuru Works (Timeline) ──────────────────────────────────
def _timeline() -> None:
    steps = [
        {"num": "1", "title": "Secure Login", "desc": "Enter your username to access your local SQLite records."},
        {"num": "2", "title": "Select Exercise", "desc": "Choose your training target and set set/rep objectives."},
        {"num": "3", "title": "Start Camera", "desc": "Allow webcam access to initialize the browser WebRTC stream."},
        {"num": "4", "title": "AI Detects Pose", "desc": "MediaPipe scans 33 joint landmarks in real-time."},
        {"num": "5", "title": "Voice Feedback", "desc": "Groq LLaMA 3.3 delivers instant audio coaching guidance."},
        {"num": "6", "title": "Workout Saved", "desc": "Your sets, reps, and durations are logged into SQLite database."}
    ]

    items_html = "".join(f"""
<div class="gg-timeline-item">
  <div class="gg-timeline-badge-wrap">
    <div class="gg-timeline-badge">{step["num"]}</div>
    <div class="gg-timeline-connector"></div>
  </div>
  <h4 class="gg-timeline-step-title">{step["title"]}</h4>
  <p class="gg-timeline-step-desc">{step["desc"]}</p>
</div>
""" for step in steps)

    html = f"""
<div class="gg-section" id="how-it-works">
  <div class="gg-section-label">WORKFLOW</div>
  <h2 class="gg-section-title">How GymGuru Works</h2>
  <p class="gg-section-subtitle-text">A frictionless bridge from setup to live audio form coaching.</p>
  <div class="gg-timeline-grid-modern">
    {items_html}
  </div>
</div>
"""
    st.markdown(html.replace('\n', ''), unsafe_allow_html=True)


# ── Section 6: Core Features ──────────────────────────────────────────────────
def _features() -> None:
    items = [
        ("🎯", "Real-Time Pose Detection", "33 MediaPipe landmarks analyze your body movements instantly inside your browser."),
        ("🔢", "Automatic Rep Counting", "Accurately logs repetitions and tracks sets using relative joint angles."),
        ("🔊", "AI Voice Coach", "Voice updates powered by Groq LLaMA 3.3 keep you corrected and motivated."),
        ("🛡️", "Live Form Correction", "Instant alerts warn you of improper back arches, incorrect depths, or elbow swings."),
        ("📜", "Workout History", "Logs date, sets, reps, and workout duration for every training session."),
        ("🗄️", "SQLite Local Storage", "Your training records remain private and saved on your local machine database.")
    ]

    cards_html = "".join(f"""
<div class="gg-feature-card-v2">
  <div class="gg-feature-icon-v2">{icon}</div>
  <h3 class="gg-feature-title-v2">{title}</h3>
  <p class="gg-feature-desc-v2">{desc}</p>
</div>
""" for icon, title, desc in items)

    html = f"""
<div class="gg-section" id="features">
  <div class="gg-section-label">CORE CAPABILITIES</div>
  <h2 class="gg-section-title">Core Features</h2>
  <div class="gg-features-grid-v2">{cards_html}</div>
</div>
"""
    st.markdown(html.replace('\n', ''), unsafe_allow_html=True)


# ── Section 7: Technology Badges ──────────────────────────────────────────────
def _technology() -> None:
    html = """
<div class="gg-section" id="technology" style="padding-top: 1rem; padding-bottom: 1rem;">
  <div class="gg-section-label">BUILT WITH</div>
  <div style="display: flex; gap: 0.75rem; justify-content: center; flex-wrap: wrap; margin-top: 1rem;">
    <span class="gg-tech-badge">Python 3.11</span>
    <span class="gg-tech-badge">MediaPipe Pose</span>
    <span class="gg-tech-badge">OpenCV</span>
    <span class="gg-tech-badge">Groq LLaMA 3.3</span>
    <span class="gg-tech-badge">SQLite</span>
    <span class="gg-tech-badge">Streamlit</span>
    <span class="gg-tech-badge">WebRTC</span>
  </div>
</div>
"""
    st.markdown(html.replace('\n', ''), unsafe_allow_html=True)


# ── Section 8: Comparison Grid ───────────────────────────────────────────────
def _comparison() -> None:
    st.markdown('<div class="gg-section"><div class="gg-section-label">WHY GYMGURU</div><h2 class="gg-section-title">Traditional Apps vs GymGuru</h2></div>', unsafe_allow_html=True)
    
    col_trad, col_gg = st.columns(2, gap="large")
    with col_trad:
        st.markdown("""
<div class="dev-comp-card traditional">
  <div class="dev-comp-header">TRADITIONAL APPS</div>
  <div class="dev-comp-item">❌ Manual Rep Counting</div>
  <div class="dev-comp-item">❌ No Form Correction</div>
  <div class="dev-comp-item">❌ Generic Video Tutorials</div>
</div>
""", unsafe_allow_html=True)
        
    with col_gg:
        st.markdown("""
<div class="dev-comp-card gymguru">
  <div class="dev-comp-header highlight">GYMGURU</div>
  <div class="dev-comp-item highlight-cell">✅ Automatic AI Counting</div>
  <div class="dev-comp-item highlight-cell">✅ Live Form Correction</div>
  <div class="dev-comp-item highlight-cell">✅ Personalized Voice Coaching</div>
</div>
""", unsafe_allow_html=True)


# ── Section 9: Ready to Start (CTA) ──────────────────────────────────────────
def _cta_ready() -> None:
    html = """
<div class="gg-section" style="padding-top: 2rem; padding-bottom: 2rem;">
  <div class="gg-cta-card-v2">
    <h2 class="gg-cta-title-v2">Ready to Start?</h2>
    <p class="gg-cta-desc-v2">Log in at the top to access your real-time training dashboard.</p>
    <a href="#login-card" class="gg-cta-btn-v2">Start Training Now →</a>
  </div>
</div>
"""
    st.markdown(html.replace('\n', ''), unsafe_allow_html=True)


# ── Section 10: Professional Footer ───────────────────────────────────────────
def _footer() -> None:
    html = f"""
<footer class="gg-footer-modern">
  <div class="gg-footer-content-modern">
    <div class="gg-footer-logo-row">
      <img src="{_LOGO_URI}" class="gg-footer-logo-modern" alt="GymGuru Logo">
      <div class="gg-footer-brand-modern">GymGuru</div>
    </div>
    <div class="gg-footer-desc-modern">AI-Powered Personal Fitness Coach</div>
    <div class="gg-footer-links-modern">
      <a href="https://github.com" target="_blank" class="gg-footer-link-modern">GitHub</a>
      <span class="gg-footer-sep-modern">·</span>
      <a href="#" class="gg-footer-link-modern">Privacy Policy</a>
      <span class="gg-footer-sep-modern">·</span>
      <a href="#" class="gg-footer-link-modern">Terms of Service</a>
    </div>
    <div class="gg-footer-copy-modern">&copy; 2025 GymGuru. All rights reserved.</div>
  </div>
</footer>
"""
    st.markdown(html.replace('\n', ''), unsafe_allow_html=True)


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

    # Inject dark athlete background only on the login wall
    st.markdown("""
    <style>
    .stApp {
        background-image: linear-gradient(180deg, rgba(11, 13, 18, 0.94) 0%, rgba(19, 23, 34, 0.88) 50%, rgba(11, 13, 18, 0.96) 100%), 
                          url('https://images.unsplash.com/photo-1534438327276-14e5300c3a48?q=80&w=1600') !important;
        background-size: cover !important;
        background-position: center !important;
        background-repeat: no-repeat !important;
        background-attachment: fixed !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # 1. Sticky Navbar
    _navbar()

    # 2. Hero Column + Login Card (unified top section)
    col1, col2 = st.columns([1.2, 1], gap="large")

    with col1:
        _hero_left()

    with col2:
        # Floating circles container wrapper
        st.markdown('<div class="gg-hero-right-container">', unsafe_allow_html=True)
        
        with st.form("login_form", clear_on_submit=False):
            st.markdown(f"""
            <div class="gg-login-header" id="login-card">
              <div class="gg-login-title">👋 Welcome to GymGuru</div>
              <div class="gg-login-desc">
                Log in to synchronize your local SQLite records.
              </div>
            </div>
            """, unsafe_allow_html=True)

            username = st.text_input(
                "Username",
                placeholder="Enter your username",
                help="Your workout history will be saved automatically.",
            )

            submit = st.form_submit_button(
                "Start Training  →",
                use_container_width=True,
            )

            st.markdown("""
            <div class="gg-login-footer">
              <div class="gg-privacy-note">
                <span>🔒</span> Your data is stored locally and stays private.
              </div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown('</div>', unsafe_allow_html=True)

    if submit:
        if not username.strip():
            st.error("Username cannot be empty.")
            return False
        user = get_or_create_user(username.strip())
        st.session_state["user_id"]  = user["id"]
        st.session_state["username"] = user["username"]
        st.rerun()

    # 3. Centered Quotes Slider
    _quotes()

    # 4. Supported Exercises Grid
    _exercises()

    # 5. Workflow Timeline
    _timeline()

    # 6. Core Features Grid
    _features()

    # 7. Technology Badges
    _technology()

    # 8. Comparison Grid
    _comparison()

    # 9. CTA Ready Card
    _cta_ready()

    # 10. Footer
    _footer()

    return False
