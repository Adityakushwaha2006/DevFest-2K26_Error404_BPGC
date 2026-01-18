import os
import json
import streamlit as st
import streamlit.components.v1 as components
import sys

# Ensure correct import path based on your project structure
from devfest_nexus.logic.chat_engine import create_chat_engine

def load_frontend_state() -> dict:
    """
    Load frontend state from the Logistic Mind's state file.
    Falls back to default mock data if file doesn't exist.
    """
    state_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "backend", "data", "frontend_state.json"
    )

    default_state = {
        "active_person": {
            "name": "Aditya Kushwaha",
            "avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Aditya",
            "role": "Software Engineer",
            "github": ""
        },
        "cit_score": {
            "context": 85,
            "intent": 72,
            "timing": 91,
            "total": 83,
            "execution_state": "PROCEED"
        },
        "focus_keywords": ["Optimization", "Machine Learning"],
        "intent_classification": "Mentorship",
        "activity_stream": [
            {"time": "14:00", "type": "signal", "content": "Signal Detected: GitHub"},
            {"time": "NOW", "type": "action", "content": "Drafting Outreach"}
        ],
        "tentative_strategy": [
            {"date": "JAN 19", "action": "Schedule Follow-up Call"},
            {"date": "JAN 21", "action": "Share Research Notes"}
        ],
        "conversations": []
    }

    try:
        if os.path.exists(state_file):
            with open(state_file, "r", encoding="utf-8") as f:
                loaded = json.load(f)
                # Merge with defaults for missing keys
                for key, value in default_state.items():
                    if key not in loaded or not loaded[key]:
                        loaded[key] = value
                return loaded
    except Exception as e:
        print(f"⚠️ Could not load frontend state: {e}")

    return default_state

def _mode_to_intent(mode: str) -> str:
    """Map user mode to their primary networking intent"""
    mode_intents = {
        "Student / Intern": "mentorship",
        "Founder": "hiring",
        "Researcher": "collaboration"
    }
    return mode_intents.get(mode, "networking")

def _mode_to_goals(mode: str) -> str:
    """Map user mode to their primary goals description"""
    mode_goals = {
        "Student / Intern": "Finding mentors, securing internships, getting career advice, building a professional network",
        "Founder": "Recruiting talent, finding co-founders, connecting with investors, building strategic partnerships",
        "Researcher": "Finding collaborators, discovering research opportunities, connecting with labs and academics"
    }
    return mode_goals.get(mode, "Building professional connections and exploring opportunities")

def render():
    """
    Renders the Nexus Strategy Console dashboard.
    Consolidated Version: Rich UI + Robust Logout Logic.
    """

    # --- 1. AUTO-REFRESH MECHANISM ---
    import time
    state_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "backend", "data", "frontend_state.json"
    )

    if 'last_state_mtime' not in st.session_state:
        st.session_state.last_state_mtime = 0
        st.session_state.state_initialized = False

    try:
        if os.path.exists(state_file):
            current_mtime = os.path.getmtime(state_file)
            previous_mtime = st.session_state.last_state_mtime

            if current_mtime > previous_mtime and st.session_state.state_initialized:
                st.session_state.last_state_mtime = current_mtime
                time.sleep(0.1)
                st.rerun()
            else:
                st.session_state.last_state_mtime = current_mtime
                st.session_state.state_initialized = True
    except Exception:
        pass

    # --- 2. CONTEXT INJECTION INTO CHAT ---
    active_context_file = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "backend", "data", "active_context.json"
    )

    if 'last_context_mtime' not in st.session_state:
        st.session_state.last_context_mtime = 0

    try:
        if os.path.exists(active_context_file) and 'chat_engine' in st.session_state and st.session_state.chat_engine:
            context_mtime = os.path.getmtime(active_context_file)

            if context_mtime > st.session_state.last_context_mtime:
                st.session_state.last_context_mtime = context_mtime

                with open(active_context_file, "r", encoding="utf-8") as f:
                    context_data = json.load(f)

                if context_data.get("discovery_mode") and context_data.get("needs_clarification"):
                    discovery_context = {
                        "discovery_mode": True,
                        "user_intent": context_data.get("user_intent", "general"),
                        "extracted_signals": context_data.get("extracted_signals", {}),
                        "suggested_questions": context_data.get("suggested_questions", []),
                        "signal_confirmations": context_data.get("signal_confirmations", []),
                        "guidance": context_data.get("guidance", "")
                    }
                    clarification_context = f"""[DISCOVERY MODE ACTIVE]
The user wants to discover people to connect with but hasn't provided enough context.
User's vague intent: {discovery_context['user_intent']}
Detected context: {discovery_context.get('extracted_signals', {})}
Your task: Ask 1-2 clarifying questions NATURALLY (don't list them robotically).
Suggested questions: {discovery_context['suggested_questions']}
{f"Also mention: {discovery_context['signal_confirmations'][0]}" if discovery_context.get('signal_confirmations') else ""}
DO NOT run a search yet. The backend will search once the user provides more specifics."""

                    if hasattr(st.session_state.chat_engine, 'context_data'):
                        st.session_state.chat_engine.context_data = clarification_context
                else:
                    target_profile = context_data.get("target_profile", {})
                    cit_score = context_data.get("cit_score", {})
                    intent = context_data.get("intent", "networking")
                    st.session_state.chat_engine.inject_context(
                        cit_score=cit_score,
                        target_profile=target_profile,
                        intent=intent
                    )
    except Exception as e:
        print(f"⚠️ Context injection error: {e}")

    # --- 3. DATA PREPARATION ---
    frontend_state = load_frontend_state()
    active_person = frontend_state.get("active_person", {})
    cit_score = frontend_state.get("cit_score", {})

    exec_state = cit_score.get("execution_state", "PROCEED")
    status_map = {
        "STRONG_GO": ("STRONG GO", "neon-green"),
        "PROCEED": ("PROCEED", "neon-blue"),
        "CAUTION": ("CAUTION", "neon-purple"),
        "ABORT": ("WATCHLIST", "neon-red")
    }
    status_label, status_color = status_map.get(exec_state, ("UNKNOWN", "neon-blue"))

    data = {
        "selected_mode": st.session_state.get('selected_mode', 'Student / Intern'),
        "target_name": active_person.get("name", "Unknown Target"),
        "target_role": active_person.get("role", ""),
        "target_avatar": active_person.get("avatar", "https://api.dicebear.com/7.x/avataaars/svg?seed=User"),
        "status_label": status_label,
        "status_color": status_color,
        "readiness_score": cit_score.get("total", 0),
        "current_intent": frontend_state.get("intent_classification", "Exploration"),
        "focus_area": (frontend_state.get("focus_keywords", ["General"]) or ["General"])[0],
        "last_active": "Recent",
        "signal_source": "GitHub" if active_person.get("github") else "Social",
        "ai_insight": f"CIT Score: C={cit_score.get('context', 0)} I={cit_score.get('intent', 0)} T={cit_score.get('timing', 0)}",
        "activity_stream": frontend_state.get("activity_stream", []),
        "tentative_strategy": frontend_state.get("tentative_strategy", []),
        "conversations": frontend_state.get("conversations", [])
    }

    # --- 4. HTML COMPONENT GENERATION ---

    # Chat History HTML
    chat_messages_html = ""
    chat_history = st.session_state.get('chat_history', [])
    for msg in chat_history:
        if msg.get('role') == 'assistant':
            content = msg.get('content', '').replace('\n', '<br>')
            chat_messages_html += f"""
        <div class="message">
            <div class="icon-box icon-ai">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M6 3v18" />
                    <path d="M18 3v18" />
                    <path d="M6 3l12 18" />
                </svg>
            </div>
            <div class="msg-bubble ai-bubble">
                <div style="line-height: 1.5;">{content}</div>
            </div>
        </div>"""
        elif msg.get('role') == 'user':
            content = msg.get('content', '')
            chat_messages_html += f"""
        <div class="message" style="justify-content: flex-end;">
            <div class="msg-bubble" style="background: rgba(59, 130, 246, 0.1); border-color: rgba(59, 130, 246, 0.2);">
                <p>{content}</p>
            </div>
        </div>"""

    # Activity Stream HTML
    activity_stream_html = ""
    for i, item in enumerate(data.get("activity_stream", [])[:5]):
        is_active = item.get("time", "").upper() == "NOW"
        dot_class = "active" if is_active else ""
        time_style = 'style="color:var(--neon-green)"' if is_active else ""
        activity_stream_html += f"""
                        <div class="tl-item">
                            <div class="tl-dot {dot_class}"></div>
                            <div class="tl-time" {time_style}>{item.get('time', '')}</div>
                            <div class="tl-content">{item.get('content', '')}</div>
                        </div>"""

    # Strategy HTML
    strategy_html = ""
    for item in data.get("tentative_strategy", [])[:4]:
        strategy_html += f"""
                        <div class="tl-item">
                            <div class="tl-dot future"></div>
                            <div class="tl-time future">{item.get('date', '')}</div>
                            <div class="tl-content future">{item.get('action', '')}</div>
                        </div>"""

    # Sidebar Conversations HTML
    sidebar_conversations_html = ""
    for conv in data.get("conversations", [])[:5]:
        name = conv.get("person", "UN")
        initials = "".join([word[0].upper() for word in name.split()[:2]]) if name else "?"
        preview = conv.get("preview", "")[:30]
        sidebar_conversations_html += f"""
                <div class="signal-item">
                    <div class="monogram">{initials}</div>
                    <div class="sig-info">
                        <h4 class="sig-name">{name}</h4>
                        <div class="sig-meta">{preview}</div>
                    </div>
                </div>"""

    # --- 5. MAIN HTML STRUCTURE ---
    html_code = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>NEXUS | Console</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400;500;600;800&family=JetBrains+Mono:wght@300;400;500;700&display=swap" rel="stylesheet">
        <script src="https://unpkg.com/lucide@latest"></script>
        <style>
            :root {{
                --bg-dark: #121212; --bg-panel: #121212; --text-primary: #EDEDED; --text-secondary: #888888;
                --glass-bg: rgba(255, 255, 255, 0.03); --glass-border: rgba(255, 255, 255, 0.06); --glass-highlight: rgba(255, 255, 255, 0.08);
                --neon-blue: #3b82f6; --neon-purple: #8b5cf6; --neon-green: #10b981; --neon-red: #ef4444;
            }}
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{ background-color: var(--bg-dark); color: var(--text-primary); font-family: 'Inter', sans-serif; height: 100vh; width: 100vw; overflow: hidden; display: flex; margin: 0; font-weight: 300; }}

            /* Background Canvas */
            #bg-canvas {{ position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; opacity: 1; }}
            .app-container {{ display: flex; width: 100%; height: 100vh; position: relative; z-index: 1; }}

            /* Sidebar */
            .sidebar {{ width: 280px; background: rgba(18, 18, 18, 0.3); backdrop-filter: blur(12px); -webkit-backdrop-filter: blur(12px); border-right: 1px solid rgba(255,255,255,0.04); display: flex; flex-direction: column; padding: 20px; overflow-y: auto; }}

            /* Logout Button - Robust Anchor Tag Style */
            .logout-btn {{ 
                margin-top: auto; padding: 12px; border-top: 1px solid rgba(255,255,255,0.06); 
                cursor: pointer; display: flex; align-items: center; gap: 10px; color: #666; transition: 0.2s; 
                text-decoration: none;
            }}
            .logout-btn:hover {{ color: #ef4444; background: rgba(239, 68, 68, 0.05); }}

            /* Common UI Elements */
            .section-label {{ font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; color: var(--text-secondary); letter-spacing: 1px; margin-bottom: 12px; margin-top: 8px; }}
            .signal-item {{ background: var(--glass-bg); border: 1px solid var(--glass-border); border-radius: 8px; padding: 12px; display: flex; gap: 12px; margin-bottom: 8px; cursor: pointer; transition: all 0.2s; }}
            .signal-item:hover {{ background: var(--glass-highlight); border-color: rgba(255,255,255,0.1); }}
            .signal-item.active {{ border-color: var(--neon-green); background: rgba(16, 185, 129, 0.05); }}
            .monogram {{ width: 40px; height: 40px; border-radius: 8px; background: linear-gradient(135deg, #444 0%, #222 100%); display: flex; align-items: center; justify-content: center; font-weight: 600; font-size: 0.75rem; position: relative; flex-shrink: 0; }}
            .status-pixel {{ position: absolute; top: -2px; right: -2px; width: 8px; height: 8px; border-radius: 50%; border: 2px solid var(--bg-panel); }}
            .status-pixel.urgent {{ background: var(--neon-green); box-shadow: 0 0 8px var(--neon-green); }}
            .sig-info {{ flex: 1; overflow: hidden; }}
            .sig-name {{ font-size: 0.85rem; font-weight: 500; margin-bottom: 4px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
            .sig-meta {{ font-size: 0.7rem; color: var(--text-secondary); font-family: 'JetBrains Mono', monospace; }}

            /* Main Console */
            .main-console {{ flex: 1; display: flex; overflow: hidden; }}
            .chat-section {{ flex: 1; display: flex; flex-direction: column; background: transparent; position: relative; }}
            .chat-section::before {{ content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(18, 18, 18, 0.85); z-index: -1; }}
            .messages {{ flex: 1; overflow-y: auto; padding: 20px; padding-bottom: 80px; display: flex; flex-direction: column; gap: 16px; }}
            .message {{ display: flex; gap: 12px; align-items: flex-start; }}
            .icon-box {{ width: 28px; height: 28px; border-radius: 6px; display: flex; align-items: center; justify-content: center; flex-shrink: 0; }}
            .icon-ai {{ background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.2); color: var(--neon-blue); }}
            .msg-bubble {{ background: rgba(18, 18, 18, 0.92); border: 1px solid var(--glass-border); border-radius: 12px; padding: 16px; max-width: 85%; font-size: 0.9rem; line-height: 1.6; }}
            .ai-bubble {{ border-color: rgba(59, 130, 246, 0.15); }}

            /* Context Panel */
            .context-panel {{ width: 320px; background: var(--bg-panel); border-left: 1px solid rgba(255,255,255,0.04); padding: 30px 20px; overflow-y: auto; }}
            .panel-title {{ font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: var(--text-secondary); letter-spacing: 1px; margin-bottom: 16px; font-weight: 500; }}
            .kv-row {{ display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid rgba(255,255,255,0.04); }}
            .kv-label {{ font-family: 'JetBrains Mono', monospace; font-size: 0.7rem; color: var(--text-secondary); letter-spacing: 0.5px; }}
            .kv-val {{ font-size: 0.8rem; font-weight: 500; }}
            .timeline-wrapper {{ margin-top: 16px; }}
            .tl-item {{ display: flex; gap: 12px; padding: 10px 0; position: relative; }}
            .tl-item:not(:last-child)::after {{ content: ''; position: absolute; left: 5px; top: 28px; bottom: -10px; width: 1px; background: rgba(255,255,255,0.08); }}
            .tl-dot {{ width: 10px; height: 10px; border-radius: 50%; background: #333; border: 2px solid var(--bg-panel); flex-shrink: 0; margin-top: 4px; }}
            .tl-dot.active {{ background: var(--neon-green); box-shadow: 0 0 10px var(--neon-green); }}
            .tl-dot.future {{ background: transparent; border-color: #333; }}
            .tl-time {{ font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; color: var(--text-secondary); width: 60px; flex-shrink: 0; }}
            .tl-time.future {{ color: #444; }}
            .tl-content {{ font-size: 0.8rem; flex: 1; }}
            .tl-content.future {{ color: #666; }}

            /* Scrollbar */
            ::-webkit-scrollbar {{ width: 6px; height: 6px; }}
            ::-webkit-scrollbar-track {{ background: transparent; }}
            ::-webkit-scrollbar-thumb {{ background: rgba(255,255,255,0.1); border-radius: 3px; }}
            ::-webkit-scrollbar-thumb:hover {{ background: rgba(255,255,255,0.15); }}
        </style>
    </head>
    <body>
        <canvas id="bg-canvas"></canvas>
        <div class="app-container">
            <aside class="sidebar">
                <div style="margin-bottom:24px; position:relative;">
                    <i data-lucide="search" style="position:absolute; left:12px; top:50%; transform:translateY(-50%); color:#666; width:14px;"></i>
                    <input type="text" placeholder="Jump to..." style="width:100%; background:rgba(255,255,255,0.03); border:1px solid rgba(255,255,255,0.06); border-radius:6px; padding:10px 12px 10px 36px; color:white; outline:none;">
                </div>

                <div class="section-label">CURRENT TARGET</div>
                <div class="signal-item active">
                    <div class="monogram">
                        {data['target_name'][:2].upper() if data['target_name'] else '??'}
                        <div class="status-pixel urgent"></div>
                    </div>
                    <div class="sig-info">
                        <h4 class="sig-name">{data['target_name']}</h4>
                        <div class="sig-meta">{data['status_label']} • {data['last_active']}</div>
                    </div>
                </div>

                <div class="section-label" style="margin-top: 20px;">CONVERSATIONS</div>
                {sidebar_conversations_html}

                <div class="logout-btn" onclick="window.location.href='?logout=true'" style="cursor:pointer;">
                    <i data-lucide="log-out" width="16"></i>
                    <span style="font-size:0.8rem; font-weight:500;">Logout</span>
                </div>
            </aside>

            <div class="main-console">
                <section class="chat-section">
                    <div class="messages" id="chat-history">
                        {chat_messages_html}
                    </div>
                </section>

                <aside class="context-panel">
                    <div class="panel-title">TARGET DATA</div>
                    <div class="kv-row">
                        <span class="kv-label">MODE</span>
                        <span class="kv-val">{data['selected_mode']}</span>
                    </div>
                    <div class="kv-row">
                        <span class="kv-label">INTENT</span>
                        <span class="kv-val">{data['current_intent']}</span>
                    </div>
                    <div class="kv-row">
                        <span class="kv-label">READINESS</span>
                        <span class="kv-val" style="color:var(--neon-green)">{data['readiness_score']}%</span>
                    </div>
                    <div class="kv-row">
                        <span class="kv-label">FOCUS</span>
                        <span class="kv-val">{data['focus_area']}</span>
                    </div>

                    <div class="panel-title" style="margin-top: 30px;">ACTIVITY STREAM</div>
                    <div class="timeline-wrapper">
                        {activity_stream_html}
                    </div>

                    <div class="panel-title" style="margin-top: 30px;">TENTATIVE STRATEGY</div>
                    <div class="timeline-wrapper future">
                        {strategy_html}
                    </div>
                </aside>
            </div>
        </div>
        <script>
            lucide.createIcons();
            const chatHistory = document.getElementById('chat-history');
            if (chatHistory) {{ chatHistory.scrollTop = chatHistory.scrollHeight; }}



            // Background Animation
            const canvas = document.getElementById('bg-canvas');
            const ctx = canvas.getContext('2d');
            let width, height;
            let particlesArray;

            class Particle {{
                constructor(x, y, size) {{
                    this.x = x; this.y = y; this.size = size;
                    this.baseVx = (Math.random() * 0.2) - 0.1;
                    this.baseVy = (Math.random() * 0.2) - 0.1;
                    this.vx = this.baseVx; this.vy = this.baseVy;
                }}
                draw() {{
                    ctx.beginPath();
                    ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2, false);
                    ctx.fillStyle = 'rgba(255, 255, 255, 0.8)';
                    ctx.fill();
                }}
                update() {{
                    this.x += this.vx; this.y += this.vy;
                    if (this.x > width) this.x = 0; if (this.x < 0) this.x = width;
                    if (this.y > height) this.y = 0; if (this.y < 0) this.y = height;
                }}
            }}

            function connect() {{
                let opacityValue = 1;
                for (let a = 0; a < particlesArray.length; a++) {{
                    for (let b = a; b < particlesArray.length; b++) {{
                        let distance = ((particlesArray[a].x - particlesArray[b].x) * (particlesArray[a].x - particlesArray[b].x))
                                     + ((particlesArray[a].y - particlesArray[b].y) * (particlesArray[a].y - particlesArray[b].y));
                        if (distance < (canvas.width/9) * (canvas.height/9)) {{
                            opacityValue = 1 - (distance / 25000);
                            if(opacityValue > 0) {{
                                 ctx.strokeStyle = 'rgba(255, 255, 255,' + opacityValue * 0.15 + ')';
                                 ctx.lineWidth = 1;
                                 ctx.beginPath();
                                 ctx.moveTo(particlesArray[a].x, particlesArray[a].y);
                                 ctx.lineTo(particlesArray[b].x, particlesArray[b].y);
                                 ctx.stroke();
                            }}
                        }}
                    }}
                }}
            }}

            function init() {{
                width = window.innerWidth; height = window.innerHeight;
                canvas.width = width; canvas.height = height;
                particlesArray = [];
                let numberOfParticles = (width * height) / 9000;
                for (let i = 0; i < numberOfParticles; i++) {{
                    particlesArray.push(new Particle(Math.random() * width, Math.random() * height, (Math.random() * 1.8) + 0.6));
                }}
            }}

            function animate() {{
                requestAnimationFrame(animate);
                ctx.clearRect(0, 0, width, height);
                for (let i = 0; i < particlesArray.length; i++) {{
                    particlesArray[i].update(); particlesArray[i].draw();
                }}
                connect();
            }}

            window.addEventListener('resize', function(){{ init(); }});
            init(); animate();
        </script>
    </body>
    </html>
    """


    # --- 6. RENDER DASHBOARD ---
    components.html(html_code, height=0, scrolling=False)

    # --- 6. CHAT FUNCTIONALITY ---
    if 'chat_engine' not in st.session_state:
        try:
            # Sticky Session Logic
            query_params = st.query_params
            session_id = query_params.get("session", None)

            st.session_state.chat_engine = create_chat_engine(session_id=session_id)

            if st.session_state.chat_engine:
                new_session_id = st.session_state.chat_engine.session_id
                if session_id != new_session_id:
                    st.query_params["session"] = new_session_id

                # Context Setup
                user_mode = st.session_state.get('selected_mode', 'Student / Intern')
                st.session_state.chat_engine.set_context({
                    "user_mode": user_mode,
                    "user_intent": _mode_to_intent(user_mode)
                })

                # System Prompt Injection
                if not st.session_state.chat_engine.get_history():
                    mode_context = f"""
--- USER CONTEXT ---
User Role: {user_mode}
Primary Goals: {_mode_to_goals(user_mode)}
Tailor all advice to this user's perspective.
--- END USER CONTEXT ---
"""
                    st.session_state.chat_engine.system_prompt = mode_context + st.session_state.chat_engine.system_prompt

                st.session_state.chat_history = st.session_state.chat_engine.get_history()

        except Exception as e:
            st.error(f"Failed to initialize chat: {e}")
            st.session_state.chat_engine = None
            st.session_state.chat_history = []

    # CSS for Input Area
    st.markdown("""
        <style>
            .block-container { padding: 0 !important; }
            iframe { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; border: none; z-index: 99999; }
            header, footer, .stDeployButton { visibility: hidden; }

            div[data-testid="stTextArea"] {
                position: fixed !important;
                bottom: 22px !important;
                left: 310px !important;
                width: calc(100vw - 660px) !important;
                z-index: 999999 !important;
                margin: 0 !important;
                padding: 0 !important;
                box-sizing: border-box !important;
            }

            div[data-testid="stTextArea"] textarea {
                background: #1e1e1e !important;
                caret-color: #EDEDED !important;
                border: 1px solid rgba(255, 255, 255, 0.06) !important;
                border-radius: 10px !important;
                padding: 12px 16px !important;
                color: #FFFFFF !important;
                font-size: 0.9rem !important;
                font-family: 'Inter', sans-serif !important;
                resize: none !important;
                overflow-wrap: break-word !important;
                min-height: 44px !important;
                max-height: 200px !important;
                overflow-y: auto !important;
                box-sizing: border-box !important;
            }

            div[data-testid="stTextArea"] textarea:focus {
                border-color: rgba(59, 130, 246, 0.4) !important;
                outline: none !important;
                box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1) !important;
            }

            div[data-testid="stTextArea"] label { display: none !important; }
        </style>
    """, unsafe_allow_html=True)

    def handle_input():
        user_msg = st.session_state.get('chat_input_text', '').strip()
        if user_msg and user_msg != st.session_state.get('last_processed_msg', ''):
            try:
                st.session_state.chat_engine.send_message(user_msg)
                st.session_state.chat_history = st.session_state.chat_engine.get_history()
                st.session_state.last_processed_msg = user_msg
                st.session_state.chat_input_text = ''
            except Exception as e:
                st.error(f"Error: {str(e)}")

    if 'chat_input_text' not in st.session_state:
        st.session_state.chat_input_text = ''

    st.text_area(
        "Message",
        key='chat_input_text',
        placeholder="Message Nexus Strategist...",
        height=60,
        label_visibility="collapsed",
        on_change=handle_input
    )