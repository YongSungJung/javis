import os
import requests
import streamlit as st
from voice_input import voice_input

# =========================================================
# 설정
# =========================================================
def get_setting(name: str, default: str) -> str:
    value = os.environ.get(name)
    if value:
        return value
    try:
        return str(st.secrets.get(name, default))
    except Exception:
        return default


HF_TOKEN = get_setting("HF_TOKEN", "")
HF_ROUTER_URL = "https://router.huggingface.co/v1/chat/completions"
MODEL_NAME = get_setting("HF_MODEL", "Qwen/Qwen2.5-72B-Instruct")

SYSTEM_PROMPT = (
    "당신은 '자비스'라는 이름의 인공지능 비서입니다. "
    "정중하고 간결하며 신뢰감 있는 어조로 한국어로 답변하세요. "
    "불확실한 내용은 추측하지 말고 모른다고 밝히세요."
)

st.set_page_config(page_title="J.A.R.V.I.S.", page_icon="🤖", layout="wide")

st.markdown(
    """
    <style>
    :root { color-scheme: dark; }
    .stApp {
        color: #efffff;
        background: transparent;
        isolation: isolate;
    }
    html, body, #root { background: #06151b; }
    .stApp::before, .stApp::after {
        content: "";
        position: fixed;
        inset: 0;
        z-index: -1;
        pointer-events: none;
    }
    .stApp::before {
        opacity: .82;
        background:
            radial-gradient(ellipse at 18% 24%, rgba(26, 188, 190, .25), transparent 38%),
            radial-gradient(ellipse at 82% 72%, rgba(217, 145, 71, .14), transparent 34%),
            linear-gradient(rgba(99, 222, 222, .055) 1px, transparent 1px),
            linear-gradient(90deg, rgba(99, 222, 222, .055) 1px, transparent 1px),
            linear-gradient(145deg, #071a20, #0a242a 52%, #101d20);
        background-size: auto, auto, 48px 48px, 48px 48px, auto;
        animation: hud-drift 28s ease-in-out infinite alternate;
    }
    .stApp::after {
        opacity: .42;
        background: linear-gradient(180deg, transparent 0%, rgba(140, 255, 250, .08) 48%, transparent 100%);
        background-size: 100% 220px;
        animation: hud-scan 12s linear infinite;
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stAppViewContainer"] { background: transparent; }
    .block-container { position: relative; z-index: 1; max-width: 1120px; padding-top: 1rem; padding-bottom: 2rem; }
    iframe[title*="jarvis_voice_input"] {
        width: 100% !important;
        max-width: 100% !important;
        min-height: 330px !important;
        border: 0;
    }
    .ambient-reactor {
        position: fixed;
        z-index: -1;
        top: 50%;
        left: 50%;
        width: min(92vw, 82vh, 820px);
        aspect-ratio: 1;
        transform: translate(-50%, -50%);
        pointer-events: none;
        opacity: .52;
        filter: drop-shadow(0 0 30px rgba(63, 231, 219, .2));
    }
    .ambient-reactor > span { position: absolute; display: block; border-radius: 50%; }
    .reactor-halo {
        inset: 14%;
        background: radial-gradient(circle, rgba(106, 255, 235, .2), rgba(35, 180, 178, .08) 42%, transparent 72%);
        animation: reactor-breathe 5s ease-in-out infinite;
    }
    .reactor-frame {
        inset: 4%;
        border: 1px solid rgba(164, 255, 247, .48);
        box-shadow: inset 0 0 34px rgba(67, 231, 221, .08), 0 0 24px rgba(67, 231, 221, .12);
    }
    .reactor-segments {
        inset: 1%;
        background: repeating-conic-gradient(from 0deg, rgba(139, 255, 245, .9) 0deg 1deg, transparent 1deg 9deg);
        -webkit-mask: radial-gradient(circle, transparent 0 81%, #000 82% 85%, transparent 86%);
        mask: radial-gradient(circle, transparent 0 81%, #000 82% 85%, transparent 86%);
        animation: reactor-spin 48s linear infinite;
    }
    .reactor-orbit {
        inset: 15%;
        border: 1px dashed rgba(231, 194, 125, .76);
        transform: rotate(-18deg) scaleY(.78);
        animation: reactor-counterspin 34s linear infinite;
    }
    .reactor-ring {
        inset: 25%;
        border: 1px solid rgba(146, 255, 246, .72);
        box-shadow: 0 0 20px rgba(61, 231, 219, .22), inset 0 0 20px rgba(61, 231, 219, .1);
    }
    .reactor-core-ring {
        inset: 28%;
        background: repeating-conic-gradient(from 4deg, rgba(212, 255, 247, .8) 0deg 1deg, transparent 1deg 18deg);
        -webkit-mask: radial-gradient(circle, transparent 0 83%, #000 84% 91%, transparent 92%);
        mask: radial-gradient(circle, transparent 0 83%, #000 84% 91%, transparent 92%);
        animation: reactor-counterspin 26s linear infinite;
    }
    .reactor-core {
        inset: 37%;
        border: 1px solid rgba(232, 255, 251, .94);
        background: radial-gradient(circle at 35% 30%, #fff 0, #cffff4 10%, #67edda 28%, #1d9d9e 58%, #092b35 100%);
        box-shadow: 0 0 28px rgba(103, 255, 234, .9), 0 0 100px rgba(43, 214, 207, .48), inset -12px -16px 28px rgba(0, 0, 0, .56);
        animation: reactor-breathe 3.4s ease-in-out infinite;
    }
    .reactor-pupil {
        inset: 46%;
        border: 1px solid rgba(242, 255, 252, .95);
        background: radial-gradient(circle, #fff 0 18%, rgba(216, 255, 246, .8) 19% 35%, transparent 70%);
        box-shadow: 0 0 22px rgba(233, 255, 250, .95);
    }
    [data-testid="stChatMessage"] {
        background: transparent !important;
        border: 0 !important;
        border-bottom: 1px solid rgba(147, 226, 220, .16) !important;
        border-radius: 0 !important;
        padding: .8rem 0;
    }
    [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] {
        color: #efffff;
        font-size: 1.02rem;
        line-height: 1.75;
    }
    [data-testid="stCaptionContainer"] { color: #c3e5e4; }
    [data-testid="stChatInput"] {
        background: rgba(5, 23, 29, .78);
        border: 1px solid rgba(112, 231, 222, .55);
        border-radius: 4px;
        box-shadow: 0 0 22px rgba(69, 218, 209, .09);
    }
    @keyframes hud-drift {
        from { background-position: 0 0, 0 0, 0 0, 0 0, 0 0; }
        to { background-position: 8% -5%, -7% 9%, 24px 24px, 24px 24px, 0 0; }
    }
    @keyframes hud-scan {
        from { background-position: 0 -220px; }
        to { background-position: 0 calc(100vh + 220px); }
    }
    @keyframes reactor-spin { to { transform: rotate(360deg); } }
    @keyframes reactor-counterspin { to { rotate: -360deg; } }
    @keyframes reactor-breathe { 0%, 100% { opacity: .7; scale: .97; } 50% { opacity: 1; scale: 1.03; } }
    @media (prefers-reduced-motion: reduce) {
        .stApp::before, .stApp::after { animation: none; }
        .reactor-segments, .reactor-orbit, .reactor-core-ring, .reactor-core, .reactor-halo { animation: none; }
    }
    @media (max-width: 640px) {
        .block-container { padding: .5rem .75rem 1.25rem; }
        iframe[title*="jarvis_voice_input"] { min-height: 330px !important; }
        [data-testid="stChatMessage"] [data-testid="stMarkdownContainer"] { font-size: 1rem; }
        .ambient-reactor { width: min(92vw, 76vh, 820px); opacity: .42; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="ambient-reactor" aria-hidden="true">
        <span class="reactor-halo"></span>
        <span class="reactor-frame"></span>
        <span class="reactor-segments"></span>
        <span class="reactor-orbit"></span>
        <span class="reactor-ring"></span>
        <span class="reactor-core-ring"></span>
        <span class="reactor-core"></span>
        <span class="reactor-pupil"></span>
    </div>
    """,
    unsafe_allow_html=True,
)

if "messages" not in st.session_state:
    st.session_state.messages = []
if "system_active" not in st.session_state:
    st.session_state.system_active = False
if "last_voice_event_id" not in st.session_state:
    st.session_state.last_voice_event_id = None
if "speech_id" not in st.session_state:
    st.session_state.speech_id = 0
if "speech_text" not in st.session_state:
    st.session_state.speech_text = ""


def ask_jarvis(user_text: str) -> str:
    if not HF_TOKEN:
        return "⚠️ HF_TOKEN이 설정되지 않았습니다. 환경 변수 또는 Hugging Face Space Secret에 등록해 주세요."

    body = {
        "model": MODEL_NAME,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}]
        + st.session_state.messages
        + [{"role": "user", "content": user_text}],
        "max_tokens": 512,
        "temperature": 0.6,
    }
    headers = {"Authorization": f"Bearer {HF_TOKEN}", "Content-Type": "application/json"}

    try:
        resp = requests.post(HF_ROUTER_URL, headers=headers, json=body, timeout=60)
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError as e:
        try:
            detail = resp.json().get("error", {}).get("message", resp.text)
        except ValueError:
            detail = resp.text
        return f"⚠️ 허깅페이스 API 호출 실패 ({resp.status_code}): {detail}"
    except requests.exceptions.RequestException as e:
        return f"⚠️ 허깅페이스 API 호출 실패: {e}"
    except (KeyError, IndexError):
        return "⚠️ 허깅페이스 API 응답 형식이 예상과 다릅니다."


voice_result = voice_input(
    language="ko-KR",
    active=st.session_state.system_active,
    speech_text=st.session_state.speech_text,
    speech_id=st.session_state.speech_id,
    key="jarvis_console",
)

user_input = None
if isinstance(voice_result, dict):
    event_id = voice_result.get("id")
    if event_id != st.session_state.last_voice_event_id:
        st.session_state.last_voice_event_id = event_id
        event_type = voice_result.get("type")
        if event_type == "start" and not st.session_state.system_active:
            st.session_state.system_active = True
            st.session_state.messages.append({
                "role": "assistant",
                "content": "시스템이 활성화되었습니다. 호출어 '자비스'를 기다립니다.",
            })
        elif event_type == "stop" and st.session_state.system_active:
            st.session_state.system_active = False
            st.session_state.messages.append({
                "role": "assistant",
                "content": "자비스 시스템을 종료했습니다.",
            })
        elif event_type == "wake" and st.session_state.system_active:
            wake_text = voice_result.get("text", "자비스")
            st.session_state.messages.append({"role": "user", "content": wake_text})
            st.session_state.messages.append({
                "role": "assistant",
                "content": "무엇을 도와드릴까요?",
            })
        elif event_type == "command" and st.session_state.system_active:
            user_input = voice_result.get("text", "").strip()

st.markdown("### 대화 기록")
if not st.session_state.messages:
    st.caption("시작 버튼을 누른 뒤 '자비스'라고 부르면 대화가 시작됩니다.")
for msg in st.session_state.messages:
    with st.chat_message("user" if msg["role"] == "user" else "assistant"):
        st.write(msg["content"])

typed_text = st.chat_input("음성 인식이 어려우면 여기에 입력하세요")
user_input = user_input or typed_text

if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.spinner("생각하는 중…"):
        reply = ask_jarvis(user_input)
    st.session_state.messages.append({"role": "assistant", "content": reply})
    st.session_state.speech_text = reply
    st.session_state.speech_id += 1
    st.rerun()