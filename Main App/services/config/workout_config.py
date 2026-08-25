import os
import json
import time
import base64
import urllib.request
from typing import Dict, Any, List, Optional
import streamlit as st

EXERCISE_OPTIONS=[
    "Squats",
    "Push-ups",
    "Biceps Curls (Dumbbell)",
    "Shoulder Press",
    "Lunges"
]


POSE_CONNECTIONS = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),       # Shoulders & Arms
    (11, 23), (12, 24), (23, 24),                           # Torso / Hips
    (23, 25), (24, 26), (25, 27), (26, 28), (27, 29), (28, 30), (29, 31), (30, 32), (27, 31), (28, 32)  # Legs
]


METRICS_FIELDS = {
    "Squats": {
        "knee_angle": 0,
        "back_angle": 0,
        "depth_status": "N/A",
    },
    "Push-ups": {
        "elbow_angle": 0,
        "body_alignment": "N/A",
        "hip_status": "N/A",
    },
    "Biceps Curls (Dumbbell)": {
        "elbow_angle": 0,
        "shoulder_status": "N/A",
        "swing_status": "N/A",
    },
    "Shoulder Press": {
        "elbow_angle": 0,
        "extension_status": "N/A",
        "back_arch_status": "N/A",
    },
    "Lunges": {
        "front_knee_angle": 0,
        "torso_angle": 0,
        "balance_status": "N/A",
    },
}


PROMPT = (
    "You are Apna AI Coach, a professional AI gym trainer monitoring a user's workout via live camera.\n\n"
    "### Your Role\n"
    "Provide around 10-15 words, high-energy coaching cues. You speak these aloud, so they must be natural and encouraging.\n\n"
    "### Input Format\n"
    "You receive updates in the format: 'Event: [state] Form Issue: [description]'.\n"
    "- 'Event': workout_started, set_completed, workout_completed, no_pose_detected, ongoing_form_check.\n"
    "- 'Form Issue': A technical description of a pose error (if any).\n\n"
    "### Guidelines\n"
    "1. Provide feedback in natural, short sentences. Avoid overly brief or fragmented responses.\n"
    "2. NO generic greetings or redundant questions. Focus on the workout.\n"
    "3. Use the second person (e.g., 'Straighten your back' instead of 'The user should straighten their back').\n"
    "4. Maintain a professional coaching tone and prioritize safety.\n\n"
    "### Scenario Response Styles\n"
    "- 'workout_started' -> A motivating and sharp command to begin.\n"
    "- 'workout_completed' -> A warm and encouraging closing for the session.\n"
    "- 'set_completed' -> Direct praise for finishing the set.\n"
    "- 'no_pose_detected' -> A clear instruction for the user to reposition within the camera frame.\n"
    "- 'ongoing_form_check' + Form Issue -> A precise, supportive correction for the detected error.\n"
    "- 'ongoing_form_check' (No Issue) -> Brief, energetic words of encouragement.\n"
)


_TWILIO_CACHE: Dict[str, Any] = {"timestamp": 0.0, "servers": []}
_METERED_CACHE: Dict[str, Any] = {"timestamp": 0.0, "servers": []}


def _get_secret_or_env(key: str, default: str = "") -> Any:
    try:
        if hasattr(st, "secrets") and key in st.secrets:
            val = st.secrets[key]
            if isinstance(val, (dict, list)):
                return val
            return str(val)
    except Exception:
        pass
    return os.environ.get(key, default)


def _get_twilio_ice_servers(account_sid: str, auth_token: str) -> List[Dict[str, Any]]:
    global _TWILIO_CACHE
    now = time.time()
    if _TWILIO_CACHE["servers"] and (now - _TWILIO_CACHE["timestamp"]) < 3600:
        return _TWILIO_CACHE["servers"]

    try:
        url = f"https://api.twilio.com/2010-04-01/Accounts/{account_sid}/Tokens.json"
        auth_str = f"{account_sid}:{auth_token}"
        encoded_auth = base64.b64encode(auth_str.encode()).decode()
        req = urllib.request.Request(
            url,
            data=b"",
            headers={"Authorization": f"Basic {encoded_auth}"},
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status in (200, 201):
                data = json.loads(resp.read().decode())
                raw_servers = data.get("ice_servers", [])
                formatted = []
                for s in raw_servers:
                    entry: Dict[str, Any] = {"urls": s.get("urls") or s.get("url")}
                    if "username" in s:
                        entry["username"] = s["username"]
                    if "credential" in s:
                        entry["credential"] = s["credential"]
                    formatted.append(entry)
                _TWILIO_CACHE = {"timestamp": now, "servers": formatted}
                return formatted
    except Exception:
        pass
    return []


def _get_metered_ice_servers(api_key: str, domain: str = "") -> List[Dict[str, Any]]:
    global _METERED_CACHE
    now = time.time()
    if _METERED_CACHE["servers"] and (now - _METERED_CACHE["timestamp"]) < 3600:
        return _METERED_CACHE["servers"]

    try:
        subdomain = domain.strip() if domain and domain.strip() else "openrelay"
        url = f"https://{subdomain}.metered.ca/api/v1/turn/credentials?apiKey={api_key.strip()}"
        req = urllib.request.Request(url, headers={"User-Agent": "GymGuru/1.0"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode())
                if isinstance(data, list):
                    _METERED_CACHE = {"timestamp": now, "servers": data}
                    return data
    except Exception:
        pass
    return []


def _get_hf_turn_servers(token: str) -> List[Dict[str, Any]]:
    try:
        from streamlit_webrtc.credentials import get_hf_ice_servers
        servers = get_hf_ice_servers(token)
        return [
            {
                "urls": s["urls"],
                "username": s.get("username"),
                "credential": s.get("credential"),
            }
            for s in servers
            if "urls" in s
        ]
    except Exception:
        pass
    return []


def get_safe_rtc_summary(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Returns non-sensitive metadata for diagnostics (zero credentials/secrets).
    """
    ice_servers = config.get("iceServers", [])
    protocols = set()
    stun_count = 0
    turn_count = 0
    for server in ice_servers:
        urls = server.get("urls", [])
        if isinstance(urls, str):
            urls = [urls]
        for url in urls:
            proto = url.split(":")[0].lower() if ":" in url else "unknown"
            protocols.add(proto)
            if "turn" in proto:
                turn_count += 1
            elif "stun" in proto:
                stun_count += 1
    return {
        "total_ice_server_entries": len(ice_servers),
        "has_turn": turn_count > 0,
        "protocols": sorted(list(protocols)),
        "stun_url_count": stun_count,
        "turn_url_count": turn_count,
    }


def get_rtc_configuration() -> Dict[str, Any]:
    """
    Builds production WebRTC RTCConfiguration with multi-STUN fallback
    and secure environment-driven TURN support (Render / Cloud / Localhost).
    """
    # 1. Full RTC_CONFIGURATION JSON or dict in secrets/env
    raw_rtc = _get_secret_or_env("RTC_CONFIGURATION")
    if raw_rtc:
        try:
            parsed = json.loads(raw_rtc) if isinstance(raw_rtc, str) else raw_rtc
            if isinstance(parsed, dict) and "iceServers" in parsed:
                return parsed
        except Exception:
            pass

    ice_servers: List[Dict[str, Any]] = []

    # 2. Raw ICE_SERVERS list or JSON in secrets/env
    raw_ice = _get_secret_or_env("ICE_SERVERS")
    if raw_ice:
        try:
            parsed = json.loads(raw_ice) if isinstance(raw_ice, str) else raw_ice
            if isinstance(parsed, list):
                ice_servers.extend(parsed)
        except Exception:
            pass

    # 3. Twilio STUN/TURN credentials if provided
    twilio_sid = _get_secret_or_env("TWILIO_ACCOUNT_SID")
    twilio_token = _get_secret_or_env("TWILIO_AUTH_TOKEN")
    if twilio_sid and twilio_token:
        tw_servers = _get_twilio_ice_servers(str(twilio_sid), str(twilio_token))
        if tw_servers:
            ice_servers.extend(tw_servers)

    # 4. Metered / OpenRelay credentials if provided
    metered_key = _get_secret_or_env("METERED_API_KEY") or _get_secret_or_env("OPENRELAY_API_KEY")
    metered_dom = _get_secret_or_env("METERED_DOMAIN") or _get_secret_or_env("OPENRELAY_DOMAIN")
    if metered_key:
        m_servers = _get_metered_ice_servers(str(metered_key), str(metered_dom))
        if m_servers:
            ice_servers.extend(m_servers)

    # 5. Hugging Face token if provided
    hf_token = _get_secret_or_env("HF_TOKEN") or _get_secret_or_env("HUGGINGFACE_TOKEN")
    if hf_token:
        hf_servers = _get_hf_turn_servers(str(hf_token))
        if hf_servers:
            ice_servers.extend(hf_servers)

    # 6. Standard TURN environment variables (Render / Coturn / Metered / Xirsys)
    turn_url = (
        _get_secret_or_env("TURN_SERVER")
        or _get_secret_or_env("TURN_URL")
        or _get_secret_or_env("TURN_URLS")
    )
    turn_user = _get_secret_or_env("TURN_USERNAME") or _get_secret_or_env("TURN_USER")
    turn_cred = (
        _get_secret_or_env("TURN_PASSWORD")
        or _get_secret_or_env("TURN_CREDENTIAL")
        or _get_secret_or_env("TURN_SECRET")
        or _get_secret_or_env("TURN_PASS")
    )

    if turn_url:
        if isinstance(turn_url, str):
            urls = [u.strip() for u in turn_url.split(",") if u.strip()]
        else:
            urls = turn_url
        turn_entry: Dict[str, Any] = {"urls": urls}
        if turn_user:
            turn_entry["username"] = str(turn_user)
        if turn_cred:
            turn_entry["credential"] = str(turn_cred)
        ice_servers.append(turn_entry)

    # 7. Production Google & Cloudflare STUN fallback servers
    default_stuns = [
        "stun:stun.l.google.com:19302",
        "stun:stun1.l.google.com:19302",
        "stun:stun2.l.google.com:19302",
        "stun:stun3.l.google.com:19302",
        "stun:stun4.l.google.com:19302",
        "stun:stun.cloudflare.com:3478",
        "stun:openrelay.metered.ca:80",
    ]
    ice_servers.append({"urls": default_stuns})

    return {"iceServers": ice_servers}
