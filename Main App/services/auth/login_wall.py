"""
login_wall.py — GymGuru Landing / Login Page (Reference-Matched Design v3)
────────────────────────────────────────────────────────────────────
Auth logic is 100% unchanged:  get_or_create_user(), session_state
keys "user_id" / "username", form key "login_form" — preserved.
"""

import base64
import os
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


# ── Section 1: Navbar v3 ──────────────────────────────────────────────────────
def _navbar() -> None:
    html = f"""
<header class="gg-navbar-v3">
  <div class="gg-nav-inner">
    <a href="#" class="gg-nav-brand">
      <img src="{_LOGO_URI}" class="gg-nav-logo-img" alt="GymGuru Logo">
      <span class="gg-nav-brand-text">Gym<span>Guru</span></span>
    </a>
    <nav class="gg-nav-links">
      <a href="#exercises" class="gg-nav-link-item">Exercises</a>
      <a href="#how-it-works" class="gg-nav-link-item">Workflow</a>
      <a href="#features" class="gg-nav-link-item">Features</a>
      <a href="#technology" class="gg-nav-link-item">Technology</a>
      <a href="#about" class="gg-nav-link-item">About</a>
    </nav>
    <a href="#login-card" class="gg-nav-btn">Start Training →</a>
  </div>
</header>
"""
    st.markdown(html.replace('\n', ''), unsafe_allow_html=True)


# ── Section 2: Hero Left Column v3 ───────────────────────────────────────────
def _hero_left() -> None:
    html = """
<div class="gg-hero-left-v3">
  <div class="gg-hero-badge-v3">
    <span>✨</span> AI POWERED FITNESS COACH
  </div>
  <h1 class="gg-hero-h1-v3">
    Train Smarter.<br>
    Get <span class="purple-accent">Stronger.</span>
  </h1>
  <p class="gg-hero-p-v3">
    Real-time AI posture correction, rep counting, and voice coaching to help you train with perfect form and maximum results.
  </p>
  
  <div class="gg-hero-btns-v3">
    <a href="#login-card" class="gg-hero-btn-primary">Start Training →</a>
    <a href="#exercises" class="gg-hero-btn-secondary">Learn More</a>
  </div>
  
  <div class="gg-hero-trust-strip">
    <div class="trust-item-pill"><span>★</span> AI Coach</div>
    <div class="trust-item-pill"><span>⚡</span> Real-time Feedback</div>
    <div class="trust-item-pill"><span>🔒</span> Privacy Focused</div>
    <div class="trust-item-pill"><span>👥</span> Trusted by 1000+ users</div>
  </div>
</div>
"""
    st.markdown(html.replace('\n', ''), unsafe_allow_html=True)


# ── Section 3: Quote Section v3 ──────────────────────────────────────────────
def _quotes() -> None:
    html = """
<div class="gg-quote-card-v3">
  <span class="gg-quote-qmark">“</span>
  <h2 class="gg-quote-text-v3">Discipline Beats Motivation.</h2>
  <span class="gg-quote-qmark">”</span>
  <div class="gg-quote-dots">
    <div class="gg-quote-dot"></div>
    <div class="gg-quote-dot"></div>
    <div class="gg-quote-dot active"></div>
    <div class="gg-quote-dot"></div>
    <div class="gg-quote-dot"></div>
  </div>
</div>
"""
    st.markdown(html.replace('\n', ''), unsafe_allow_html=True)


# ── Section 4: Supported Exercises Grid v3 ───────────────────────────────────
def _exercises() -> None:
    exercises_data = [
        {
            "class": "squats",
            "icon": "🏋️",
            "title": "Squats",
            "badge": "Lower Body",
            "badge_color": "purple",
            "bullets": ["Knee Tracking", "Depth Analysis", "Back Alignment", "Glute Activation"],
            "diff_class": "filled-purple",
            "filled": 1
        },
        {
            "class": "pushups",
            "icon": "🏃",
            "title": "Push-ups",
            "badge": "Upper Body",
            "badge_color": "amber",
            "bullets": ["Depth Tracking", "Elbow Angle", "Spine Alignment", "Chest Activation"],
            "diff_class": "filled-amber",
            "filled": 2
        },
        {
            "class": "biceps",
            "icon": "💪",
            "title": "Biceps Curl",
            "badge": "Arms",
            "badge_color": "gold",
            "bullets": ["Elbow Tracking", "Range of Motion", "Form Analysis", "Muscle Activation"],
            "diff_class": "filled-gold",
            "filled": 2
        },
        {
            "class": "shoulder",
            "icon": "🙌",
            "title": "Shoulder Press",
            "badge": "Shoulders",
            "badge_color": "teal",
            "bullets": ["Overhead Tracking", "Spine Alignment", "Elbow Position", "Shoulder Stability"],
            "diff_class": "filled-teal",
            "filled": 2
        },
        {
            "class": "lunges",
            "icon": "🚶",
            "title": "Lunges",
            "badge": "Lower Body",
            "badge_color": "pink",
            "bullets": ["Knee Alignment", "Step Distance", "Balance Tracking", "Posture Analysis"],
            "diff_class": "filled-pink",
            "filled": 3
        }
    ]

    cards_html = []
    for ex in exercises_data:
        dots = ""
        for i in range(3):
            if i < ex["filled"]:
                dots += f'<div class="diff-dot {ex["diff_class"]}"></div>'
            else:
                dots += '<div class="diff-dot"></div>'

        bullets_html = "".join([f'<li>&bull; {b}</li>' for b in ex["bullets"]])

        card = f"""
<div class="gg-exercise-card-ref {ex["class"]}">
  <div class="gg-ex-icon-img-ref">{ex["icon"]}</div>
  <h3 class="gg-ex-title-ref">{ex["title"]}</h3>
  <span class="gg-ex-badge-ref {ex["badge_color"]}">{ex["badge"]}</span>
  <ul class="gg-ex-bullet-list-ref">
    {bullets_html}
  </ul>
  <div class="gg-ex-diff-row-ref">
    <span>Difficulty</span>
    <div class="gg-diff-dots">{dots}</div>
  </div>
</div>
"""
        cards_html.append(card)

    cards_str = "".join(cards_html)

    html = f"""
<div class="gg-landing-v3-root" id="exercises" style="padding-top: 4rem;">
  <div class="gg-section-header-v3">
    <div class="gg-section-label-v3">TRAIN WITH AI</div>
    <h2 class="gg-section-title-v3">Supported Exercises</h2>
    <p class="gg-section-desc-v3">AI analyzes your form in real-time for maximum results</p>
  </div>
  <div class="gg-exercises-grid-ref">
    {cards_str}
  </div>
</div>
"""
    st.markdown(html.replace('\n', ''), unsafe_allow_html=True)


# ── Section 5: How GymGuru Works Timeline v3 ─────────────────────────────────
def _timeline() -> None:
    steps = [
        {"num": "1", "icon": "🔒", "title": "Secure Login", "desc": "Access your personal dashboard"},
        {"num": "2", "icon": "🎯", "title": "Select Exercise", "desc": "Choose your training target & set goals"},
        {"num": "3", "icon": "📷", "title": "Start Camera", "desc": "Grant access for real-time streaming"},
        {"num": "4", "icon": "🦾", "title": "AI Detects Pose", "desc": "MediaPipe tracks 33 key points"},
        {"num": "5", "icon": "🔊", "title": "Voice Feedback", "desc": "AI coach gives instant voice guidance"},
        {"num": "6", "icon": "💾", "title": "Workout Saved", "desc": "Your progress is logged in local database"}
    ]

    nodes_html = "".join([f"""
<div class="gg-timeline-step-node">
  <div class="gg-step-circle-ref">
    <span class="gg-step-icon-ref">{step["icon"]}</span>
    <span class="gg-step-num-tag">{step["num"]}</span>
  </div>
  <h4 class="gg-step-title-ref">{step["title"]}</h4>
  <p class="gg-step-desc-ref">{step["desc"]}</p>
</div>
""" for step in steps])

    html = f"""
<div class="gg-landing-v3-root" id="how-it-works" style="padding-top: 5rem;">
  <div class="gg-section-header-v3">
    <div class="gg-section-label-v3">EASY • SMART • EFFECTIVE</div>
    <h2 class="gg-section-title-v3">How GymGuru Works</h2>
  </div>
  <div class="gg-timeline-track-ref">
    {nodes_html}
  </div>
</div>
"""
    st.markdown(html.replace('\n', ''), unsafe_allow_html=True)


# ── Section 6: Core Features Grid v3 ─────────────────────────────────────────
def _features() -> None:
    features = [
        ("🎯", "Real-Time Pose Detection", "33 MediaPipe landmarks track your every movement."),
        ("🔢", "Automatic Rep Counting", "Accurate reps using joint angles and smart algorithms."),
        ("🔊", "AI Voice Coach", "Groq LLaMA 3.3 voice gives you real-time motivation."),
        ("🛡️", "Form Correction", "Instant feedback to fix your posture and avoid injuries."),
        ("📜", "Workout History", "Logs sets, reps, duration & performance automatically."),
        ("🗄️", "SQLite Database", "All data stored securely on your local machine.")
    ]

    cards_html = "".join([f"""
<div class="gg-feature-card-ref">
  <div class="gg-feature-icon-box">{f[0]}</div>
  <h3 class="gg-feature-title-ref">{f[1]}</h3>
  <p class="gg-feature-desc-ref">{f[2]}</p>
</div>
""" for f in features])

    html = f"""
<div class="gg-landing-v3-root" id="features" style="padding-top: 5rem;">
  <div class="gg-section-header-v3">
    <div class="gg-section-label-v3">POWERED BY AI</div>
    <h2 class="gg-section-title-v3">Core Features</h2>
  </div>
  <div class="gg-features-grid-ref">
    {cards_html}
  </div>
</div>
"""
    st.markdown(html.replace('\n', ''), unsafe_allow_html=True)


# ── Section 7: Built with Modern Technology v3 ───────────────────────────────
def _technology() -> None:
    html = """
<div class="gg-landing-v3-root" id="technology" style="padding-top: 5rem;">
  <div class="gg-section-header-v3" style="margin-bottom: 1.5rem;">
    <div class="gg-section-label-v3">BUILT WITH MODERN TECHNOLOGY</div>
  </div>
  <div class="gg-tech-pills-row-ref">
    <div class="gg-tech-pill-ref">🐍 Python 3.11</div>
    <div class="gg-tech-pill-ref">⚙️ MediaPipe Pose</div>
    <div class="gg-tech-pill-ref">👁️ OpenCV</div>
    <div class="gg-tech-pill-ref">🤖 Groq LLaMA 3.3</div>
    <div class="gg-tech-pill-ref">🗄️ SQLite</div>
    <div class="gg-tech-pill-ref">🎈 Streamlit</div>
    <div class="gg-tech-pill-ref">📹 WebRTC</div>
  </div>
</div>
"""
    st.markdown(html.replace('\n', ''), unsafe_allow_html=True)


# ── Section 8: Traditional Apps vs GymGuru v3 ────────────────────────────────
def _comparison() -> None:
    st.markdown("""
<div class="gg-landing-v3-root" style="padding-top: 5rem;">
  <div class="gg-section-header-v3">
    <div class="gg-section-label-v3">WHY GYMGURU</div>
    <h2 class="gg-section-title-v3">Traditional Apps vs GymGuru</h2>
  </div>
</div>
""", unsafe_allow_html=True)

    col_trad, col_gg = st.columns(2, gap="large")

    with col_trad:
        st.markdown("""
<div class="gg-comp-card-ref">
  <div class="gg-comp-card-header">Traditional Fitness Apps</div>
  <div class="gg-comp-card-body">
    <div class="gg-comp-card-row bad">❌ Manual Rep Counting</div>
    <div class="gg-comp-card-row bad">❌ No Real-time Form Correction</div>
    <div class="gg-comp-card-row bad">❌ Generic Video Workouts</div>
    <div class="gg-comp-card-row bad">❌ No Personalized Guidance</div>
  </div>
</div>
""", unsafe_allow_html=True)

    with col_gg:
        st.markdown("""
<div class="gg-comp-card-ref gymguru-card">
  <div class="gg-comp-card-header gymguru-header">GymGuru</div>
  <div class="gg-comp-card-body">
    <div class="gg-comp-card-row good">✅ Automatic AI Rep Counting</div>
    <div class="gg-comp-card-row good">✅ Live Form Correction</div>
    <div class="gg-comp-card-row good">✅ Personalized Voice Coaching</div>
    <div class="gg-comp-card-row good">✅ Smart AI Guidance</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ── Section 9: Ready to Transform CTA Banner v3 ───────────────────────────────
def _cta_ready() -> None:
    html = """
<div class="gg-landing-v3-root">
  <div class="gg-cta-banner-ref">
    <h2 class="gg-cta-title-ref">Ready to transform your fitness journey?</h2>
    <p class="gg-cta-desc-ref">Join GymGuru and experience AI-powered training like never before.</p>
    <a href="#login-card" class="gg-cta-btn-ref">Start Training Now →</a>
  </div>
</div>
"""
    st.markdown(html.replace('\n', ''), unsafe_allow_html=True)


# ── Section 10: Multi-column Footer v3 ────────────────────────────────────────
def _footer() -> None:
    html = f"""
<footer class="gg-footer-v3">
  <div class="gg-footer-grid-v3">
    <div>
      <div class="gg-nav-brand" style="margin-bottom: 0.75rem;">
        <img src="{_LOGO_URI}" class="gg-nav-logo-img" alt="GymGuru Logo">
        <span class="gg-nav-brand-text">Gym<span>Guru</span></span>
      </div>
      <p style="font-size: 0.85rem; color: #9CA3AF; line-height: 1.5; margin: 0; max-width: 320px;">
        AI-Powered Personal Fitness Coach.<br>
        Your AI Coach. Your Best Training Partner.
      </p>
    </div>
    
    <div>
      <div class="gg-footer-col-title">Quick Links</div>
      <ul class="gg-footer-links-list">
        <li><a href="#exercises">Exercises</a></li>
        <li><a href="#how-it-works">Workflow</a></li>
        <li><a href="#features">Features</a></li>
        <li><a href="#technology">Technology</a></li>
        <li><a href="#about">About</a></li>
      </ul>
    </div>
    
    <div>
      <div class="gg-footer-col-title">Legal</div>
      <ul class="gg-footer-links-list">
        <li><a href="#">Privacy Policy</a></li>
        <li><a href="#">Terms of Service</a></li>
        <li><a href="https://github.com" target="_blank">GitHub Repository</a></li>
      </ul>
    </div>
    
    <div>
      <div class="gg-footer-col-title">Technology</div>
      <ul class="gg-footer-links-list">
        <li><a href="#">MediaPipe Pose</a></li>
        <li><a href="#">Groq LLaMA 3.3</a></li>
        <li><a href="#">Streamlit & WebRTC</a></li>
        <li><a href="#">SQLite Persistence</a></li>
      </ul>
    </div>
  </div>
  
  <div class="gg-footer-bottom-v3">
    <div>&copy; 2025 GymGuru. All rights reserved.</div>
    <div class="gg-footer-socials">
      <a href="https://github.com" target="_blank">🌐</a>
      <a href="#">𝕏</a>
      <a href="#">📸</a>
      <a href="#">💬</a>
    </div>
  </div>
</footer>
"""
    st.markdown(html.replace('\n', ''), unsafe_allow_html=True)


# ── Public entry-point (called by main.py) ────────────────────────────────────
def render_login_wall() -> bool:
    if st.session_state.get("user_id") is not None:
        return True

    # Background styling for reference-matched landing page
    st.markdown("""
    <style>
    .stApp {
        background-color: #0D1117 !important;
        background-image: linear-gradient(180deg, rgba(13, 17, 23, 0.92) 0%, rgba(19, 23, 34, 0.85) 50%, rgba(13, 17, 23, 0.95) 100%), 
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

    # Master Content Container for Hero
    st.markdown('<div class="gg-landing-v3-root">', unsafe_allow_html=True)

    # 2. Hero Section (Left info + Right Login card)
    col1, col2 = st.columns([1.25, 1], gap="large")

    with col1:
        _hero_left()

    with col2:
        with st.form("login_form", clear_on_submit=False):
            st.markdown("""
            <div class="gg-login-card-v3" id="login-card">
              <div class="gg-login-title">Welcome back! 👋</div>
              <div class="gg-login-desc">
                Log in to continue your fitness journey.
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
            <div style="margin-top: 1rem; text-align: center; font-size: 0.78rem; color: #9CA3AF;">
              🔒 Your data is stored locally and stays private.
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

    # 3. Quote Section
    _quotes()

    # 4. Supported Exercises
    _exercises()

    # 5. Workflow Timeline
    _timeline()

    # 6. Core Features
    _features()

    # 7. Technology Badges
    _technology()

    # 8. Comparison Grid
    _comparison()

    # 9. CTA Ready Banner
    _cta_ready()

    # 10. Footer
    _footer()

    return False
