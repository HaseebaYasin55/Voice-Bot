"""
app.py -- Voice Agent UI
Run with: streamlit run app.py
"""

import streamlit as st
import streamlit.components.v1 as components
from audio_recorder_streamlit import audio_recorder
import agent

st.set_page_config(page_title="Voice A", page_icon="🎙️", layout="centered")

##styling
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

    /* Mic — single soft glow, mic icon locked to its exact center */
    .mic-wrap { display:flex; justify-content:center; align-items:center; margin:2.5rem auto 0.75rem; position:relative; width:100%; min-height:180px; }

    .mic-wrap::before {
      content:""; position:absolute; top:50%; left:50%;
      width:230px; height:230px; border-radius:50%;
      transform: translate(-50%, -50%) scale(0.9);
      background:radial-gradient(circle, rgba(45,212,191,0.4) 0%, rgba(45,212,191,0) 70%);
      animation:pulse 2.6s ease-in-out infinite; pointer-events:none; z-index:0;
      transition: background 0.25s ease;
    }
    @keyframes pulse {
      0%,100% { transform: translate(-50%, -50%) scale(0.9); opacity:0.6; }
      50%     { transform: translate(-50%, -50%) scale(1.15); opacity:1; }
    }

    /* Recording state: glow switches to red so it's unmistakable that the
       mic is actively listening. Toggled via JS (see script below), since
       the mic component doesn't report its recording state to Python. */
    .mic-wrap.is-recording::before {
      width: 250px; height: 250px;
      background: radial-gradient(circle, rgba(255,80,80,0.5) 0%, rgba(255,80,80,0) 70%);
      animation: pulseRec 1.1s ease-in-out infinite;
    }
    @keyframes pulseRec {
      0%,100% { transform: translate(-50%, -50%) scale(0.9); opacity:0.65; }
      50%     { transform: translate(-50%, -50%) scale(1.25); opacity:1; }
    }

    .mic-wrap iframe {
      z-index:2;
      background:transparent !important;
      border:none !important;
      box-shadow:none !important;
      width:110px !important; height:110px !important;
      display:block !important;
    }
    /* Streamlit wraps every custom component (mic recorder AND the voice-
       message waveform widget) in an iframe/div that defaults to a white
       box -- strip that for all of them */
    iframe { background:transparent !important; border:none !important; }
    div[data-testid="stCustomComponentV1"] { background:transparent !important; }
    div[data-testid="element-container"]:has(> div > iframe) { background:transparent !important; }

    /* Divider between the conversation and the recorder/voice-note area */
    .section-divider {
      border: none; height: 1px; margin: 2rem 0 0.5rem;
      background: linear-gradient(90deg, transparent, rgba(255,255,255,0.18), transparent);
    }

    .status-pill { text-align:center; color:var(--muted); font-size:0.85rem;
      margin-top:0.5rem; margin-bottom:1.5rem; letter-spacing:0.2px; }

    /* Agent's spoken reply plays automatically but has no visible player --
       the chat bubble above already shows the text of what was said.
       (testid is on the <audio> element itself, not a wrapping div) */
    [data-testid="stAudio"] { display: none !important; }
    div:has(> [data-testid="stAudio"]) { display: none !important; }

    /* Clear button bottom-right */
    .clear-wrap { display:flex; justify-content:flex-end; margin-top: 2rem; }
    .clear-wrap button[data-testid="stBaseButton"] {
      background: rgba(45,212,191,0.08) !important; color: var(--muted) !important;
      border:1px solid rgba(45,212,191,0.25) !important; border-radius:10px !important;
      padding:0.45rem 1rem !important; font-size:0.85rem !important; font-weight:500 !important;
      width:auto !important; transition:all 0.2s ease !important;
    }
    .clear-wrap button[data-testid="stBaseButton"]:hover {
      background: rgba(45,212,191,0.18) !important; color:#99f6e4 !important;
      border-color: rgba(45,212,191,0.5) !important;
    }
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
    st.session_state.history = []          # list of {"role": "user"/"assistant", "content": str}
                                            # (this exact shape is what agent.run_turn expects)
if "pending_audio" not in st.session_state:
    st.session_state.pending_audio = None
if "last_audio_hash" not in st.session_state:
    st.session_state.last_audio_hash = None
if "turn_count" not in st.session_state:
    st.session_state.turn_count = 0


st.markdown("<h1>Voice Agent</h1>", unsafe_allow_html=True)
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

st.markdown("<div class='mic-wrap'>", unsafe_allow_html=True)

audio_bytes = audio_recorder(
    text="",
    recording_color="#ff5b5b",
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
    const RECORDING_RGB = 'rgb(255, 91, 91)';  // matches recording_color="#ff5b5b"

    function fixHostIframes() {
      try {
        const iframes = window.parent.document.querySelectorAll('iframe');
        const micWrap = window.parent.document.querySelector('.mic-wrap');
        let wrapCenter = null;
        if (micWrap) {
          const r = micWrap.getBoundingClientRect();
          wrapCenter = { x: r.left + r.width / 2, y: r.top + r.height / 2 };
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
                    margin: 0 !important; padding: 0 !important;
                    width: 100% !important; height: 100% !important;
                    display: flex !important; align-items: center !important; justify-content: center !important;
                  }
                  span { display:flex !important; align-items:center !important; justify-content:center !important; }
                  button {
                    outline: none !important;
                    box-shadow: none !important;
                    -webkit-tap-highlight-color: transparent !important;
                  }
                  button:focus, button:focus-visible, button:active {
                    outline: none !important;
                    box-shadow: none !important;
                    border: none !important;
                  }
                `;
                doc.head.appendChild(style);
              }

              // This is the mic-recorder iframe specifically (it contains a
              // <button>). Its iframe may not truly be a DOM descendant of
              // .mic-wrap (Streamlit renders each st.markdown/widget call as
              // a separate sibling element), so CSS-only centering against
              // .mic-wrap can't be trusted. Instead we measure the glow
              // circle's real on-screen position and pin this iframe exactly
              // to that point every cycle.
              if (doc.querySelector('button') && wrapCenter) {
                const fw = f.offsetWidth || 110;
                const fh = f.offsetHeight || 110;
                f.style.setProperty('position', 'fixed', 'important');
                f.style.setProperty('left', (wrapCenter.x - fw / 2) + 'px', 'important');
                f.style.setProperty('top', (wrapCenter.y - fh / 2) + 'px', 'important');
                f.style.setProperty('z-index', '9999', 'important');

                // Detect recording state: the mic icon's color switches to
                // recording_color while actively recording.
                const candidates = doc.querySelectorAll('svg, path, button');
                candidates.forEach((el) => {
                  if (window.getComputedStyle(el).color === RECORDING_RGB) {
                    isRecording = true;
                  }
                });
              }
            }
          } catch (e) { /* cross-origin or not-yet-loaded, skip */ }
        });

        if (micWrap) {
          micWrap.classList.toggle('is-recording', isRecording);
        }
      } catch (e) {}
    }
    fixHostIframes();
    const observer = new MutationObserver(fixHostIframes);
    observer.observe(window.parent.document.body, { childList: true, subtree: true });
    window.parent.addEventListener('scroll', fixHostIframes, true);
    window.parent.addEventListener('resize', fixHostIframes);
    setInterval(fixHostIframes, 250);
    </script>
    """,
    height=0,
)

st.markdown(
    "<div class='status-pill'>Click once to record · click again to stop</div>",
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
                    result = agent.run_turn(audio_bytes, st.session_state.history)
                    st.session_state.pending_audio = result["assistant_audio"]
                    st.session_state.turn_count += 1  # forces a fresh mic widget next turn
                    st.rerun()
                except Exception as e:
                    import traceback
                    print(traceback.format_exc())
                    st.session_state.pending_audio = None
                    st.session_state.last_audio_hash = None  # allow retrying this recording
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