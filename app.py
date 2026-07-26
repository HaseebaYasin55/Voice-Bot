import streamlit as st
import agent

st.set_page_config(page_title="VoiceBot", page_icon="🎙️", layout="centered")

##styling
st.markdown(
    """
    <style>
    :root {
      --bg-0:#050f0e; --bg-1:#0a1f1c; --text:#e6fffa; --muted:#7fada6;
      --user:linear-gradient(135deg,#14b8a6,#2dd4bf);
      --agent-bg:rgba(45,212,191,0.07);
      --agent-border:rgba(45,212,191,0.18);
      --accent:#2dd4bf;
    }
    .stApp {
      background:
        radial-gradient(1200px 600px at 20% -10%, rgba(45,212,191,0.18), transparent 60%),
        radial-gradient(900px 500px at 90% 10%, rgba(20,184,166,0.16), transparent 60%),
        linear-gradient(180deg, var(--bg-1) 0%, var(--bg-0) 100%);
      color: var(--text);
    }
    .block-container { max-width: 760px; padding-top: 2.5rem; padding-bottom: 6rem; }

    h1 {
      text-align:center; font-weight:800 !important; letter-spacing:-1px;
      font-size:2.4rem !important; margin-bottom:0.3rem !important;
      background: linear-gradient(90deg,#fff 0%,#99f6e4 100%);
      -webkit-background-clip:text; -webkit-text-fill-color:transparent; background-clip:text;
    }
    .subtitle { text-align:center; color:var(--muted); margin-bottom:2.5rem; font-size:0.98rem; }

    .row { display:flex; margin:0.35rem 0; animation:fadeIn 0.35s ease; }
    .bubble {
      padding:0.85rem 1.1rem; border-radius:18px; max-width:78%; line-height:1.5;
      font-size:0.97rem; backdrop-filter:blur(12px); box-shadow:0 4px 24px rgba(0,0,0,0.25);
    }
    .user-bubble { background:var(--user); color:#fff; margin-left:auto; border-bottom-right-radius:6px; }
    .agent-bubble { background:var(--agent-bg); color:var(--text); margin-right:auto;
      border:1px solid var(--agent-border); border-bottom-left-radius:6px; }
    @keyframes fadeIn { from{opacity:0; transform:translateY(6px);} to{opacity:1; transform:translateY(0);} }

    /* Divider between the conversation and the recorder area */
    .section-divider {
      border: none; height: 1px; margin: 2rem 0 1.25rem;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,0.18), transparent);
    }

    /* --- Voice recorder theming ---
       .st-key-voice_recorder is the class Streamlit auto-generates from
       key="voice_recorder" on st.audio_input below. This is more reliable
       than data-testid selectors alone, since it won't break if Streamlit
       renames its internal component classes in a future version. We pair
       it with data-testid="stAudioInput" as a belt-and-braces fallback. */
    [class*="st-key-voice_recorder"] div[data-testid="stAudioInput"],
    div[data-testid="stAudioInput"] {
      background: linear-gradient(135deg, rgba(20,184,166,0.14), rgba(10,31,28,0.9)) !important;
      border: 1px solid var(--agent-border) !important;
      border-radius: 18px !important;
      box-shadow: 0 4px 24px rgba(0,0,0,0.3) !important;
    }
    /* Buttons (mic / play / delete) inside the recorder */
    [class*="st-key-voice_recorder"] button,
    div[data-testid="stAudioInput"] button {
      background: transparent !important;
      color: var(--accent) !important;
    }
    [class*="st-key-voice_recorder"] button svg,
    div[data-testid="stAudioInput"] button svg {
      fill: var(--accent) !important;
      color: var(--accent) !important;
    }
    /* Waveform / progress bar + timer text -- broad descendant catch since
       the exact internal class names for these aren't publicly documented
       and can change between Streamlit releases. */
    [class*="st-key-voice_recorder"] canvas,
    div[data-testid="stAudioInput"] canvas {
      filter: hue-rotate(150deg) saturate(1.6) brightness(1.1) !important;
    }
    [class*="st-key-voice_recorder"] span,
    [class*="st-key-voice_recorder"] p,
    div[data-testid="stAudioInput"] span,
    div[data-testid="stAudioInput"] p {
      color: var(--text) !important;
    }

    .status-pill { text-align:center; color:var(--muted); font-size:0.85rem;
      margin-top:0.75rem; margin-bottom:1.5rem; letter-spacing:0.2px; }

    /* Agent's spoken reply plays automatically but has no visible player --
       the chat bubble above already shows the text of what was said.
       (testid is on the <audio> element itself, not a wrapping div) */
    [data-testid="stAudio"] { display: none !important; }
    div:has(> [data-testid="stAudio"]) { display: none !important; }

    /* Clear button bottom-right -- keyed class .st-key-clear_btn from
       key="clear_btn" on the st.button below, plus a testid fallback. */
    .clear-wrap { display:flex; justify-content:flex-end; margin-top: 2rem; }
    .st-key-clear_btn button,
    .clear-wrap button[data-testid="stBaseButton"] {
      background: rgba(45,212,191,0.08) !important; color: var(--muted) !important;
      border:1px solid rgba(45,212,191,0.25) !important; border-radius:10px !important;
      padding:0.45rem 1rem !important; font-size:0.85rem !important; font-weight:500 !important;
      width:auto !important; transition:all 0.2s ease !important;
    }
    .st-key-clear_btn button:hover,
    .clear-wrap button[data-testid="stBaseButton"]:hover {
      background: rgba(45,212,191,0.18) !important; color:#99f6e4 !important;
      border-color: rgba(45,212,191,0.5) !important;
    }
    .st-key-clear_btn button p,
    .clear-wrap button[data-testid="stBaseButton"] p { color: inherit !important; }

    /* Hide streamlit chrome + sidebar */
    #MainMenu, footer, header { visibility: hidden; }
    section[data-testid="stSidebar"] { display: none !important; }
    div[data-testid="collapsedControl"] { display: none !important; }
    </style>
    """,
    unsafe_allow_html=True,
)


if "history" not in st.session_state:
    st.session_state.history = []       
if "pending_audio" not in st.session_state:
    st.session_state.pending_audio = None
if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None
if "turn_count" not in st.session_state:
    st.session_state.turn_count = 0


st.markdown("<h1>VoiceBot</h1>", unsafe_allow_html=True)
st.markdown(
    "<div class='subtitle'>Tap the mic, speak naturally — I'll listen and reply.</div>",
    unsafe_allow_html=True,
)


for msg in st.session_state.history:
    role_class = "user-bubble" if msg["role"] == "user" else "agent-bubble"
    st.markdown(
        f"<div class='row'><div class='bubble {role_class}'>{msg['content']}</div></div>",
        unsafe_allow_html=True,
    )


st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)

audio_value = st.audio_input(
    "Record a voice message",
    label_visibility="collapsed",
    key=f"voice_recorder_{st.session_state.turn_count}",
)

st.markdown(
    "<div class='status-pill'>Click to record · click again to stop</div>",
    unsafe_allow_html=True,
)

audio_bytes = audio_value.getvalue() if audio_value is not None else None

if audio_bytes:
    audio_hash = hash(audio_bytes)
    if audio_hash != st.session_state.last_audio_hash:
        st.session_state.last_audio_hash = audio_hash

        if not agent.GROQ_API_KEY:
            st.error("Please set GROQ_API_KEY in your .env file before talking to the agent.")
        else:
            with st.spinner("Thinking…"):
                try:
                    result = agent.run_turn(audio_bytes, st.session_state.history)
                    st.session_state.pending_audio = result["assistant_audio"]
                    st.session_state.turn_count += 1  # forces a fresh mic widget next turn
                    st.rerun()
                except Exception as e:
                    import traceback
                    print(traceback.format_exc())
                    st.session_state.pending_audio = None
                    st.session_state.last_audio_hash = None  
                    st.error(f"Something went wrong: {e}")

if st.session_state.pending_audio:
    st.audio(st.session_state.pending_audio, format="audio/mp3", autoplay=True)
    st.session_state.pending_audio = None


st.markdown("<div class='clear-wrap'>", unsafe_allow_html=True)
col1, col2 = st.columns([4, 1])
with col2:
    if st.button("Clear", key="clear_btn"):
        st.session_state.history = []
        st.session_state.pending_audio = None
        st.session_state.last_audio_hash = None
        st.session_state.turn_count += 1  
        st.rerun()
st.markdown("</div>", unsafe_allow_html=True)