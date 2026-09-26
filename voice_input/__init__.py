import os

import streamlit.components.v1 as components


_component_path = os.path.join(os.path.dirname(__file__), "frontend")
_voice_input = components.declare_component("jarvis_voice_input", path=_component_path)


def voice_input(language="ko-KR", active=False, speech_text="", speech_id=0, key=None):
    return _voice_input(
        language=language,
        active=active,
        speech_text=speech_text,
        speech_id=speech_id,
        default=None,
        key=key,
    )