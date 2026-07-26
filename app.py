"""
app.py -- Voice Bot UI
Run with: streamlit run app.py
"""

import streamlit as st
import streamlit.components.v1 as components
from audio_recorder_streamlit import audio_recorder
import agent

st.set_page_config(page_title="VoiceBot", page_icon="🎙️", layout="centered")

##Styling
st.markdown(
    """
    <style>
    :root {
      --bg-0:#050f0e; --bg-1:#0a1f1c; --text:#e6fffa; --muted:#7fada6;
      --user:linear-gradient(135deg,#14b8a6,#2dd4bf);
      --agent-bg:rgba(45,212,191,0.07);
      --agent-border:rgba(45,212,191,0.18);
    }

    .stApp {
      background:
        radial-gradient(1200px 600px at 20% -10%, rgba(45,212,191,0.18), transparent 60%),
        radial-gradient(900px 500px at 90% 10%, rgba(20,184,166,0.16), transparent 60%),
        linear-gradient(180deg, var(--bg-1) 0%, var(--bg-0) 100%);
      color: var(--text);
    }

    .block-container {
      max-width: 760px;
      padding-top: 2.5rem;
      padding-bottom: 6rem;
    }

    h1 {
    text-align: center;
    font-family: Georgia, "Times New Roman", serif;
    font-size: 2.7rem !important;
    font-weight: 700 !important;
    letter-spacing: -1px;
    background: linear-gradient(90deg,#ffffff,#99f6e4);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.3rem !important;
    }

    .subtitle {
    text-align: center;
    font-family: "Poppins", sans-serif;
    font-size: 0.95rem;
    font-weight: 400;
    color: #99f6e4;
    letter-spacing: 0.5px;
    margin-bottom: 2.2rem;
    opacity:0.8,
    }

    .row {
      display:flex;
      margin:0.35rem 0;
      animation:fadeIn 0.35s ease;
    }

    .bubble {
      padding:0.85rem 1.1rem;
      border-radius:18px;
      max-width:78%;
      line-height:1.5;
      font-size:0.97rem;
      backdrop-filter:blur(12px);
      box-shadow:0 4px 24px rgba(0,0,0,0.25);
    }

    .user-bubble {
      background:var(--user);
      color:#fff;
      margin-left:auto;
      border-bottom-right-radius:6px;
    }

    .agent-bubble {
      background:var(--agent-bg);
      color:var(--text);
      margin-right:auto;
      border:1px solid var(--agent-border);
      border-bottom-left-radius:6px;
    }

    @keyframes fadeIn {
      from {
        opacity:0;
        transform:translateY(6px);
      }
      to {
        opacity:1;
        transform:translateY(0);
      }
    }

    .mic-wrap {
      display:flex;
      justify-content:center;
      align-items:center;
      margin:2.5rem auto 0.75rem;
      position:relative;
      width:100%;
      min-height:180px;
    }

    .mic-wrap::before {
      content:"";
      position:absolute;
      top:50%;
      left:50%;
      width:280px;
      height:280px;
      border-radius:50%;
      transform:translate(-50%, -50%) scale(0.9);
      background:radial-gradient(circle, rgba(45,212,191,0.4) 0%, rgba(45,212,191,0) 70%);
      animation:pulse 2.6s ease-in-out infinite;
      pointer-events:none;
      z-index:0;
      transition:background 0.25s ease;
    }

    @keyframes pulse {
      0%,100% {
        transform:translate(-50%, -50%) scale(0.9);
        opacity:0.6;
      }
      50% {
        transform:translate(-50%, -50%) scale(1.15);
        opacity:1;
      }
    }

    .mic-wrap.is-recording::before {
      width:300px;
      height:300px;
      background:radial-gradient(
        circle,
        rgba(94,234,212,0.55) 0%,
        rgba(94,234,212,0) 70%
      );
      animation:pulseRec 1.1s ease-in-out infinite;
    }

    @keyframes pulseRec {
      0%,100% {
        transform:translate(-50%, -50%) scale(0.9);
        opacity:0.65;
      }
      50% {
        transform:translate(-50%, -50%) scale(1.25);
        opacity:1;
      }
    }

    .mic-wrap iframe {
      z-index:2;
      background:transparent !important;
      border:none !important;
      box-shadow:none !important;
      width:150px !important;
      height:150px !important;
      display:block !important;
    }

    iframe {
      background:transparent !important;
      border:none !important;
    }

    div[data-testid="stCustomComponentV1"] {
      background:transparent !important;
    }

    div[data-testid="element-container"]:has(> div > iframe) {
      background:transparent !important;
    }

    .section-divider {
      border:none;
      height:1px;
      margin:2rem 0 0.5rem;
      background:linear-gradient(90deg, transparent, rgba(255,255,255,0.18), transparent);
    }

    .status-pill {
    text-align: center;
    font-family: "Poppins", sans-serif;
    font-size: 0.9rem;
    font-weight: 400;
    color: #99f6e4;
    letter-spacing: 0.3px;
    margin-top: 0.5rem;
    margin-bottom: 1.5rem;
    opacity: 0.75;
    }

    [data-testid="stAudio"] {
      display:none !important;
    }

    div:has(> [data-testid="stAudio"]) {
      display:none !important;
    }

    .clear-wrap {
      display:flex;
      justify-content:flex-end;
      margin-top:2rem;
    }

    div[data-testid="stButton"] > button {
      background: rgba(45, 212, 191, 0.12) !important;
      color: #99f6e4 !important;
      border: 1px solid rgba(45, 212, 191, 0.25) !important;
      border-radius: 12px !important;
      box-shadow: 0 4px 16px rgba(45, 212, 191, 0.12) !important;
      transition: all 0.25s ease !important;
    }

    div[data-testid="stButton"] > button:hover {
      background: rgba(45, 212, 191, 0.20) !important;
      border-color: rgba(45, 212, 191, 0.45) !important;
      color: #e6fffa !important;
      transform: translateY(-2px);
    }

    div[data-testid="stButton"] > button:active {
      transform: scale(0.97);
    }

    div[data-testid="stButton"] > button p {
      color: inherit !important;
    }

    #MainMenu,
    footer,
    header {
      visibility:hidden;
    }

    section[data-testid="stSidebar"] {
      display:none !important;
    }

    div[data-testid="collapsedControl"] {
      display:none !important;
    }

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
    "<div class='subtitle'>Powered by Streamlit • Groq • Whisper • Edge</div>",
    unsafe_allow_html=True,
)


for msg in st.session_state.history:
    role_class = "user-bubble" if msg["role"] == "user" else "agent-bubble"
    st.markdown(
        f"<div class='row'><div class='bubble {role_class}'>{msg['content']}</div></div>",
        unsafe_allow_html=True,
    )


st.markdown("<hr class='section-divider'>", unsafe_allow_html=True)


st.markdown("<div class='mic-wrap'>", unsafe_allow_html=True)

audio_bytes = audio_recorder(
    text="",
    recording_color="#5EEAD4",
    neutral_color="#2dd4bf",
    icon_size="4x",
    pause_threshold=99999.0,   
    sample_rate=16000,
    key=f"recorder_{st.session_state.turn_count}",
)

st.markdown("</div>", unsafe_allow_html=True)

components.html(
    """
    <script>
    const RECORDING_RGB = 'rgb(255, 91, 91)';

    function fixHostIframes() {
      try {
        const iframes = window.parent.document.querySelectorAll('iframe');
        const micWrap = window.parent.document.querySelector('.mic-wrap');
        let wrapCenter = null;

        if (micWrap) {
          const r = micWrap.getBoundingClientRect();
          wrapCenter = {
            x: r.left + r.width / 2,
            y: r.top + r.height / 2
          };
        }

        let isRecording = false;

        iframes.forEach((f) => {
          try {
            f.style.setProperty('background', 'transparent', 'important');
            f.style.setProperty('border', 'none', 'important');

            const doc = f.contentDocument;

            if (doc && doc.body) {
              doc.documentElement.style.setProperty('background', 'transparent', 'important');
              doc.body.style.setProperty('background', 'transparent', 'important');

              if (!doc.getElementById('__transparent_fix__')) {
                const style = doc.createElement('style');
                style.id = '__transparent_fix__';

                style.textContent = `
                  html, body {
                    background: transparent !important;
                    margin: 0 !important;
                    padding: 0 !important;
                    width: 100% !important;
                    height: 100% !important;
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                  }

                  span {
                    display: flex !important;
                    align-items: center !important;
                    justify-content: center !important;
                  }

                  button {
                    outline: none !important;
                    box-shadow: none !important;
                    -webkit-tap-highlight-color: transparent !important;
                  }

                  button:focus,
                  button:focus-visible,
                  button:active {
                    outline: none !important;
                    box-shadow: none !important;
                    border: none !important;
                  }
                `;

                doc.head.appendChild(style);
              }

              if (doc.querySelector('button') && wrapCenter) {
                const fw = f.offsetWidth || 150;
                const fh = f.offsetHeight || 150;

                f.style.setProperty('position', 'fixed', 'important');
                f.style.setProperty('left', (wrapCenter.x - fw / 2) + 'px', 'important');
                f.style.setProperty('top', (wrapCenter.y - fh / 2) + 'px', 'important');
                f.style.setProperty('z-index', '9999', 'important');

                const candidates = doc.querySelectorAll('svg, path, button');

                candidates.forEach((el) => {
                  if (window.getComputedStyle(el).color === RECORDING_RGB) {
                    isRecording = true;
                  }
                });
              }
            }
          } catch (e) {}
        });

        if (micWrap) {
          micWrap.classList.toggle('is-recording', isRecording);
        }

      } catch (e) {}
    }

    function debounce(fn, ms) {
    let t;
    return (...args) => {
        clearTimeout(t);
        t = setTimeout(() => fn(...args), ms);
    };
}

    const debouncedFix = debounce(fixHostIframes, 150);

    fixHostIframes();

    const micWrapEl = window.parent.document.querySelector('.mic-wrap');
    const observer = new MutationObserver(debouncedFix);
    observer.observe(micWrapEl || window.parent.document.body, {
         childList: true,
         subtree: true
});

window.parent.addEventListener('scroll', debouncedFix, true);
window.parent.addEventListener('resize', debouncedFix);
    </script>
    """,
    height=0,
)


st.markdown(
    "<div class='status-pill'>Click the microphone to start or stop recording!</div>",
    unsafe_allow_html=True,
)


if audio_bytes:
    audio_hash = hash(audio_bytes)
    if audio_hash != st.session_state.last_audio_hash:
        st.session_state.last_audio_hash = audio_hash

        if not agent.GROQ_API_KEY:
            st.error("Please set GROQ_API_KEY in your .env file before talking to the agent.")
        else:
            with st.spinner("Thinking…"):
                try:
                    # run_turn appends both the user's and the agent's turns
                    # to st.session_state.history in place, and returns the
                    # audio to play back.
                    result = agent.run_turn(audio_bytes, st.session_state.history)
                    st.session_state.pending_audio = result["assistant_audio"]
                except Exception as e:
                    st.error(f"Something went wrong: {e}")
                    st.session_state.pending_audio = None
            st.rerun()


if st.session_state.pending_audio:
    st.audio(st.session_state.pending_audio, format="audio/mp3", autoplay=True)
    st.session_state.pending_audio = None


st.markdown("<div class='clear-wrap'>", unsafe_allow_html=True)
col1, col2 = st.columns([4, 1])
with col2:
    if st.button("Clear Chat", key="clear_btn"):
        st.session_state.history = []
        st.session_state.pending_audio = None
        st.session_state.last_audio_hash = None
        st.session_state.turn_count += 1  
        st.rerun()
st.markdown("</div>", unsafe_allow_html=True)