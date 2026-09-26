import os
import requests
import streamlit as st
from streamlit.errors import StreamlitSecretNotFoundError
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
    except StreamlitSecretNotFoundError:
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
        color: #e9f5f8;
        background:
            linear-gradient(180deg, rgba(3, 9, 15, .40), rgba(3, 9, 15, .86)),
            url("https://i.pinimg.com/736x/ed/86/af/ed86af6ae5769fb3c72f82c959f0d422.jpg") center 35% / cover fixed;
    }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stAppViewContainer"] { background: rgba(3, 9, 15, .42); }
    .block-container { max-width: 1120px; padding-top: 1rem; padding-bottom: 2rem; }
    iframe[title*="jarvis_voice_input"] { min-height: 420px !important; }
    [data-testid="stChatMessage"] {
        background: rgba(6, 19, 27, .78);
        border: 1px solid rgba(103, 219, 231, .18);
        border-radius: 8px;
        backdrop-filter: blur(12px);
    }
    [data-testid="stChatInput"] { background: rgba(6, 19, 27, .9); }
    @media (max-width: 640px) {
        .block-container { padding: .5rem .75rem 1.25rem; }
        iframe[title*="jarvis_voice_input"] { min-height: 380px !important; }
    }
    </style>
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