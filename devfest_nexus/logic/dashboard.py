"""
Nexus Dashboard Component - Fullscreen Overlay Strategy
=======================================================
The Strategy Console view featuring:
- Chat interface with AI strategist
- Target profile sidebar
- Activity timeline and context panel
- Mock data structure for backend integration
"""

import streamlit as st
import streamlit.components.v1 as components

def render_dashboard():
    """
    Renders the Nexus Strategy Console dashboard.
    Uses fullscreen overlay hack to bypass Streamlit layout.
    """
    
    # --- 1. THE DATA INTERFACE (Backend Contract) ---
    # This dictionary defines exactly what the Backend Team needs to provide.
    # Currently populated with static mock data for the UI demo.
    data = {
        "target_name": "Aditya Kushwaha",
        "target_role": "Software Engineer",
        "target_avatar": "https://api.dicebear.com/7.x/avataaars/svg?seed=Aditya",
        "status_label": "FLOW STATE",
        "status_color": "neon-green",  # CSS variable mapping
        "readiness_score": 94,
        "current_intent": "Mentorship",
        "focus_area": "Optimization",
        "last_active": "2m ago",
        "signal_source": "GitHub",
        "ai_insight": "Target is in 'Builder Mode' (12 commits in 3h). Technical engagement recommended.",
        "draft_message": "Hey Aditya, saw your GPU allocation fix on aeon-toolkit. I'm facing a similar bottleneck—did you find the memory overhead reduced significantly after the patch?"
    }

    # --- 2. THE FRONTEND (HTML/CSS/JS) ---
    # Note: Double curly braces {{ }} are used for CSS/JS to avoid f-string conflicts.
    # Single curly braces { } are used for Python data injection.
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
                --bg-dark: #121212; 
                --bg-panel: #121212;
                --text-primary: #EDEDED;
                --text-secondary: #888888; 
                --glass-bg: rgba(255, 255, 255, 0.03);
                --glass-border: rgba(255, 255, 255, 0.06);
                --glass-highlight: rgba(255, 255, 255, 0.08);
                --neon-blue: #3b82f6;
                --neon-purple: #8b5cf6;
                --neon-green: #10b981;
                --neon-red: #ef4444;
                --msg-user: #1f1f22; 
                --msg-ai: transparent;
            }}
            * {{ box-sizing: border-box; margin: 0; padding: 0; }}
            body {{
                background-color: var(--bg-dark);
                color: var(--text-primary);
                font-family: 'Inter', sans-serif;
                height: 100vh;
                width: 100vw;
                overflow: hidden;
                display: flex;
                margin: 0;
                font-weight: 300; 
            }}
            
            /* App Container */
            .app-container {{
                display: flex;
                width: 100%;
                height: 100vh;
            }}
            
            /* Sidebar */
            .sidebar {{
                width: 280px;
                background: var(--bg-panel);
                border-right: 1px solid rgba(255,255,255,0.04);
                display: flex;
                flex-direction: column;
                padding: 20px;
                overflow-y: auto;
            }}
            
            .intent-header {{
                margin-bottom: 20px;
            }}
            
            .intent-label {{
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.65rem;
                color: var(--text-secondary);
                letter-spacing: 1px;
                margin-bottom: 8px;
            }}
            
            .intent-select {{
                background: var(--glass-bg);
                border: 1px solid var(--glass-border);
                border-radius: 6px;
                padding: 10px 12px;
                display: flex;
                align-items: center;
                justify-content: space-between;
                cursor: pointer;
                transition: all 0.2s;
            }}
            
            .intent-select:hover {{
                background: var(--glass-highlight);
            }}
            
            .intent-val {{
                font-size: 0.75rem;
                font-weight: 500;
                letter-spacing: 0.5px;
            }}
            
            .cmd-wrapper {{
                position: relative;
                margin-bottom: 24px;
            }}
            
            .cmd-icon {{
                position: absolute;
                left: 12px;
                top: 50%;
                transform: translateY(-50%);
                color: #666;
            }}
            
            .cmd-input {{
                width: 100%;
                background: var(--glass-bg);
                border: 1px solid var(--glass-border);
                border-radius: 6px;
                padding: 10px 12px 10px 36px;
                color: var(--text-primary);
                font-size: 0.8rem;
                outline: none;
                transition: all 0.2s;
            }}
            
            .cmd-input:focus {{
                border-color: var(--neon-blue);
                background: rgba(59, 130, 246, 0.05);
            }}
            
            .section-label {{
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.65rem;
                color: var(--text-secondary);
                letter-spacing: 1px;
                margin-bottom: 12px;
                margin-top: 8px;
            }}
            
            .signal-item {{
                background: var(--glass-bg);
                border: 1px solid var(--glass-border);
                border-radius: 8px;
                padding: 12px;
                display: flex;
                gap: 12px;
                margin-bottom: 8px;
                cursor: pointer;
                transition: all 0.2s;
            }}
            
            .signal-item:hover {{
                background: var(--glass-highlight);
                border-color: rgba(255,255,255,0.1);
            }}
            
            .signal-item.active {{
                border-color: var(--neon-green);
                background: rgba(16, 185, 129, 0.05);
            }}
            
            .monogram {{
                width: 40px;
                height: 40px;
                border-radius: 8px;
                background: linear-gradient(135deg, #444 0%, #222 100%);
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: 600;
                font-size: 0.75rem;
                position: relative;
                flex-shrink: 0;
            }}
            
            .status-pixel {{
                position: absolute;
                top: -2px;
                right: -2px;
                width: 8px;
                height: 8px;
                border-radius: 50%;
                border: 2px solid var(--bg-panel);
            }}
            
            .status-pixel.urgent {{
                background: var(--neon-green);
                box-shadow: 0 0 8px var(--neon-green);
            }}
            
            .sig-info {{
                flex: 1;
                overflow: hidden;
            }}
            
            .sig-name {{
                font-size: 0.85rem;
                font-weight: 500;
                margin-bottom: 4px;
                white-space: nowrap;
                overflow: hidden;
                text-overflow: ellipsis;
            }}
            
            .sig-meta {{
                font-size: 0.7rem;
                color: var(--text-secondary);
                font-family: 'JetBrains Mono', monospace;
            }}
            
            /* Main Console */
            .main-console {{
                flex: 1;
                display: flex;
                overflow: hidden;
            }}
            
            /* Chat Section */
            .chat-section {{
                flex: 1;
                display: flex;
                flex-direction: column;
                background: var(--bg-dark);
            }}
            
            .chat-history {{
                flex: 1;
                overflow-y: auto;
                padding: 30px;
                display: flex;
                flex-direction: column;
                gap: 20px;
            }}
            
            .message {{
                display: flex;
                gap: 12px;
                align-items: flex-start;
            }}
            
            .icon-box {{
                width: 28px;
                height: 28px;
                border-radius: 6px;
                display: flex;
                align-items: center;
                justify-content: center;
                flex-shrink: 0;
            }}
            
            .icon-ai {{
                background: rgba(59, 130, 246, 0.1);
                border: 1px solid rgba(59, 130, 246, 0.2);
                color: var(--neon-blue);
            }}
            
            .msg-bubble {{
                background: var(--glass-bg);
                border: 1px solid var(--glass-border);
                border-radius: 12px;
                padding: 16px;
                max-width: 85%;
                font-size: 0.9rem;
                line-height: 1.6;
            }}
            
            .ai-bubble {{
                border-color: rgba(59, 130, 246, 0.15);
            }}
            
            .draft-container {{
                background: rgba(0,0,0,0.3);
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 8px;
                margin-top: 12px;
                overflow: hidden;
            }}
            
            .draft-header {{
                padding: 10px 14px;
                border-bottom: 1px solid rgba(255,255,255,0.06);
                display: flex;
                align-items: center;
                justify-content: space-between;
                background: rgba(255,255,255,0.02);
            }}
            
            .draft-title {{
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.65rem;
                letter-spacing: 1px;
                color: var(--text-secondary);
                font-weight: 500;
            }}
            
            .draft-content {{
                padding: 14px;
                font-size: 0.85rem;
                line-height: 1.6;
                color: var(--text-primary);
            }}
            
            .suggestions {{
                display: flex;
                gap: 8px;
                margin-top: 12px;
            }}
            
            .chip {{
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.1);
                padding: 6px 12px;
                border-radius: 20px;
                font-size: 0.75rem;
                cursor: pointer;
                transition: all 0.2s;
            }}
            
            .chip:hover {{
                background: rgba(255,255,255,0.1);
                border-color: var(--neon-blue);
            }}
            
            .input-area {{
                border-top: 1px solid rgba(255,255,255,0.04);
                padding: 20px 30px;
                background: var(--bg-panel);
            }}
            
            .input-wrapper {{
                background: var(--glass-bg);
                border: 1px solid var(--glass-border);
                border-radius: 10px;
                padding: 12px 16px;
                display: flex;
                align-items: center;
                gap: 12px;
                transition: all 0.2s;
            }}
            
            .input-wrapper:focus-within {{
                border-color: var(--neon-blue);
                background: rgba(59, 130, 246, 0.05);
            }}
            
            .chat-input {{
                flex: 1;
                background: transparent;
                border: none;
                outline: none;
                color: var(--text-primary);
                font-size: 0.9rem;
            }}
            
            .chat-input::placeholder {{
                color: #555;
            }}
            
            /* Context Panel */
            .context-panel {{
                width: 320px;
                background: var(--bg-panel);
                border-left: 1px solid rgba(255,255,255,0.04);
                padding: 30px 20px;
                overflow-y: auto;
            }}
            
            .panel-title {{
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.7rem;
                color: var(--text-secondary);
                letter-spacing: 1px;
                margin-bottom: 16px;
                font-weight: 500;
            }}
            
            .kv-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                padding: 10px 0;
                border-bottom: 1px solid rgba(255,255,255,0.04);
            }}
            
            .kv-label {{
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.7rem;
                color: var(--text-secondary);
                letter-spacing: 0.5px;
            }}
            
            .kv-val {{
                font-size: 0.8rem;
                font-weight: 500;
            }}
            
            .timeline-wrapper {{
                margin-top: 16px;
            }}
            
            .tl-item {{
                display: flex;
                gap: 12px;
                padding: 10px 0;
                position: relative;
            }}
            
            .tl-item:not(:last-child)::after {{
                content: '';
                position: absolute;
                left: 5px;
                top: 28px;
                bottom: -10px;
                width: 1px;
                background: rgba(255,255,255,0.08);
            }}
            
            .tl-dot {{
                width: 10px;
                height: 10px;
                border-radius: 50%;
                background: #333;
                border: 2px solid var(--bg-panel);
                flex-shrink: 0;
                margin-top: 4px;
            }}
            
            .tl-dot.active {{
                background: var(--neon-green);
                box-shadow: 0 0 10px var(--neon-green);
            }}
            
            .tl-dot.future {{
                background: transparent;
                border-color: #333;
            }}
            
            .tl-time {{
                font-family: 'JetBrains Mono', monospace;
                font-size: 0.65rem;
                color: var(--text-secondary);
                width: 60px;
                flex-shrink: 0;
            }}
            
            .tl-time.future {{
                color: #444;
            }}
            
            .tl-content {{
                font-size: 0.8rem;
                flex: 1;
            }}
            
            .tl-content.future {{
                color: #666;
            }}
            
            .tl-highlight {{
                color: var(--neon-blue);
                font-weight: 500;
            }}
            
            /* Scrollbar Styling */
            ::-webkit-scrollbar {{
                width: 6px;
                height: 6px;
            }}
            
            ::-webkit-scrollbar-track {{
                background: transparent;
            }}
            
            ::-webkit-scrollbar-thumb {{
                background: rgba(255,255,255,0.1);
                border-radius: 3px;
            }}
            
            ::-webkit-scrollbar-thumb:hover {{
                background: rgba(255,255,255,0.15);
            }}
        </style>
    </head>
    <body>
        <div class="app-container">
            <!-- SIDEBAR -->
            <aside class="sidebar">
                <div class="intent-header">
                    <div class="intent-label">CURRENT INTENT</div>
                    <div class="intent-select">
                        <span class="intent-val">{data['current_intent'].upper()}</span>
                        <i data-lucide="chevron-down" width="12" color="#666"></i>
                    </div>
                </div>
                <div class="cmd-wrapper">
                    <i data-lucide="search" class="cmd-icon" width="14"></i>
                    <input type="text" class="cmd-input" placeholder="Jump to...">
                </div>
                <div class="section-label">PRIORITY</div>
                <div class="signal-item active">
                    <div class="monogram">
                        AK
                        <div class="status-pixel urgent"></div>
                    </div>
                    <div class="sig-info">
                        <h4 class="sig-name">{data['target_name']}</h4>
                        <div class="sig-meta">{data['status_label']} • {data['last_active']}</div>
                    </div>
                </div>
                <div class="signal-item">
                    <div class="monogram">PK</div>
                    <div class="sig-info">
                        <h4 class="sig-name">Priya Kumar</h4>
                        <div class="sig-meta">ACTIVE • 1h ago</div>
                    </div>
                </div>
                <div class="signal-item">
                    <div class="monogram">RV</div>
                    <div class="sig-info">
                        <h4 class="sig-name">Rohit Verma</h4>
                        <div class="sig-meta">DORMANT • 3d ago</div>
                    </div>
                </div>
            </aside>

            <!-- MAIN CONSOLE -->
            <div class="main-console">
                <section class="chat-section">
                    <div class="chat-history">
                        <!-- AI Insight -->
                        <div class="message">
                            <div class="icon-box icon-ai">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M6 3v18" />
                                    <path d="M18 3v18" />
                                    <path d="M6 3l12 18" />
                                </svg>
                            </div>
                            <div class="msg-bubble ai-bubble">
                                <p style="color:#666; font-size:0.7rem; margin-bottom:8px; font-family:'JetBrains Mono', monospace; letter-spacing:1px; font-weight:500;">SYSTEM INSIGHT • {data['target_name'].upper()}</p>
                                <p>{data['ai_insight']}</p>
                            </div>
                        </div>
                        
                        <!-- Draft -->
                        <div class="message">
                            <div class="icon-box icon-ai">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round">
                                    <path d="M6 3v18" />
                                    <path d="M18 3v18" />
                                    <path d="M6 3l12 18" />
                                </svg>
                            </div>
                            <div class="msg-bubble ai-bubble" style="width:100%; max-width:none;">
                                <p>Here is a concise draft referencing the specific commit:</p>
                                <div class="draft-container">
                                    <div class="draft-header">
                                        <span class="draft-title">LINKEDIN / DM</span>
                                        <i data-lucide="copy" width="12" color="#666" style="cursor:pointer"></i>
                                    </div>
                                    <div class="draft-content">
                                        {data['draft_message']}
                                    </div>
                                </div>
                                <div class="suggestions">
                                    <div class="chip">Make it Formal</div>
                                    <div class="chip">Ask for Call</div>
                                    <div class="chip">Add Context</div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="input-area">
                        <div class="input-wrapper">
                            <input type="text" class="chat-input" placeholder="Message Nexus Strategist...">
                            <i data-lucide="arrow-right" width="16" color="#444" style="cursor:pointer"></i>
                        </div>
                    </div>
                </section>

                <aside class="context-panel">
                    <div class="panel-title">TARGET DATA</div>
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
                        <div class="tl-item">
                            <div class="tl-dot"></div>
                            <div class="tl-time">14:00</div>
                            <div class="tl-content">
                                Signal Detected: <span class="tl-highlight">{data['signal_source']}</span>
                            </div>
                        </div>
                        <div class="tl-item">
                            <div class="tl-dot active"></div>
                            <div class="tl-time" style="color:var(--neon-green)">NOW</div>
                            <div class="tl-content">Drafting Outreach</div>
                        </div>
                    </div>
                    
                    <div class="panel-title" style="margin-top: 30px;">TENTATIVE STRATEGY</div>
                    <div class="timeline-wrapper future">
                        <div class="tl-item">
                            <div class="tl-dot future"></div>
                            <div class="tl-time future">JAN 19</div>
                            <div class="tl-content future">Schedule Follow-up Call</div>
                        </div>
                        <div class="tl-item">
                            <div class="tl-dot future"></div>
                            <div class="tl-time future">JAN 21</div>
                            <div class="tl-content future">Share Research Notes</div>
                        </div>
                    </div>
                </aside>
            </div>
        </div>
        <script>
            lucide.createIcons();
        </script>
    </body>
    </html>
    """

    # --- 3. RENDER FULLSCREEN ---
    components.html(html_code, height=0, scrolling=False)
    
    st.markdown("""
        <style>
            .block-container { padding: 0 !important; }
            iframe { 
                position: fixed; 
                top: 0; 
                left: 0; 
                width: 100vw; 
                height: 100vh; 
                border: none; 
                z-index: 99999; 
            }
            header, footer, .stDeployButton { visibility: hidden; }
        </style>
    """, unsafe_allow_html=True)
