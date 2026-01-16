"""
Landing Page Component - With Navigation
=========================================
Fullscreen landing page with card selection and Streamlit button for navigation.
"""

import streamlit as st
import streamlit.components.v1 as components

def render_landing_page():
    # --- 1. THE LANDING PAGE HTML (Visuals & Selection Logic) ---
    html_code = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <script src="https://cdn.tailwindcss.com"></script>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
        <script src="https://unpkg.com/lucide@latest"></script>
        <style>
            :root {
                --bg-dark: #121212;
                --text-primary: #EDEDED;
                --neon-blue: #3b82f6;
                --neon-purple: #8b5cf6;
                --neon-green: #10b981;
                --glass-bg: rgba(255, 255, 255, 0.03);
                --glass-border: rgba(255, 255, 255, 0.08);
            }
            body {
                background-color: var(--bg-dark);
                color: var(--text-primary);
                font-family: 'Inter', sans-serif;
                overflow: hidden;
                height: 100vh;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                margin: 0;
            }
            #bg-canvas { position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1; opacity: 0.5; }
            
            /* CARDS */
            .cards-container { display: flex; gap: 20px; width: 100%; max-width: 1000px; z-index: 10; margin-top: 40px; }
            .persona-card {
                background: var(--glass-bg);
                border: 1px solid var(--glass-border);
                backdrop-filter: blur(20px);
                border-radius: 12px;
                padding: 28px;
                flex: 1;
                cursor: pointer;
                transition: all 0.3s ease;
                position: relative;
            }
            .persona-card:hover { transform: translateY(-5px); background: rgba(255, 255, 255, 0.05); }
            
            /* SELECTION STATE */
            .persona-card.active {
                background: rgba(255, 255, 255, 0.08);
                transform: scale(1.02);
                box-shadow: 0 0 30px rgba(0,0,0,0.5);
            }
            .persona-card.active.card-blue { border-color: var(--neon-blue); box-shadow: 0 0 20px rgba(59, 130, 246, 0.3); }
            .persona-card.active.card-purple { border-color: var(--neon-purple); box-shadow: 0 0 20px rgba(139, 92, 246, 0.3); }
            .persona-card.active.card-green { border-color: var(--neon-green); box-shadow: 0 0 20px rgba(16, 185, 129, 0.3); }

            .card-title { font-weight: 700; font-size: 1.2rem; margin-bottom: 0.5rem; color: #fff; }
            .card-desc { font-weight: 300; font-size: 0.85rem; color: #888; line-height: 1.5; }
            .mode-badge { font-family: 'JetBrains Mono', monospace; font-size: 0.65rem; padding: 4px 8px; border-radius: 4px; background: rgba(255,255,255,0.05); color: #666; margin-bottom: 12px; display: inline-block; }
            
            .logo-text { font-family: 'Inter', sans-serif; font-weight: 800; font-size: 3rem; letter-spacing: -2px; margin-bottom: 10px; }
            .logo-sub { font-family: 'JetBrains Mono', monospace; color: #666; letter-spacing: 2px; font-size: 0.8rem; }
        </style>
    </head>
    <body>
        <canvas id="bg-canvas"></canvas>
        
        <div style="text-align:center; z-index:10; margin-bottom:20px;">
            <div class="logo-text">NEXUS</div>
            <div class="logo-sub">INTELLIGENT NETWORKING ENGINE v5.0</div>
        </div>

        <div class="cards-container">
            <!-- Card 1 -->
            <div class="persona-card card-blue" onclick="selectCard(this)">
                <span class="mode-badge">MODE A</span>
                <h3 class="card-title">Student</h3>
                <p class="card-desc">Optimize for Alumni & Recruiters.</p>
            </div>
            <!-- Card 2 -->
            <div class="persona-card card-purple" onclick="selectCard(this)">
                <span class="mode-badge">MODE B</span>
                <h3 class="card-title">Founder</h3>
                <p class="card-desc">Optimize for VCs & Talent.</p>
            </div>
            <!-- Card 3 -->
            <div class="persona-card card-green" onclick="selectCard(this)">
                <span class="mode-badge">MODE C</span>
                <h3 class="card-title">Researcher</h3>
                <p class="card-desc">Optimize for Labs & Citations.</p>
            </div>
        </div>

        <script>
            function selectCard(element) {
                document.querySelectorAll('.persona-card').forEach(c => c.classList.remove('active'));
                element.classList.add('active');
            }
            
            const canvas = document.getElementById('bg-canvas');
            const ctx = canvas.getContext('2d');
            canvas.width = window.innerWidth; canvas.height = window.innerHeight;
            let particles = [];
            for(let i=0; i<50; i++) particles.push({x:Math.random()*canvas.width, y:Math.random()*canvas.height, vx:(Math.random()-0.5), vy:(Math.random()-0.5)});
            function animate(){
                ctx.clearRect(0,0,canvas.width,canvas.height);
                ctx.fillStyle='rgba(255,255,255,0.2)';
                particles.forEach(p=>{
                    p.x+=p.vx; p.y+=p.vy;
                    if(p.x<0||p.x>canvas.width) p.vx*=-1;
                    if(p.y<0||p.y>canvas.height) p.vy*=-1;
                    ctx.beginPath(); ctx.arc(p.x,p.y,2,0,Math.PI*2); ctx.fill();
                });
                requestAnimationFrame(animate);
            }
            animate();
        </script>
    </body>
    </html>
    """
    
    # 2. Render Fullscreen HTML
    components.html(html_code, height=0, scrolling=False)
    
    # 3. CSS to Force Fullscreen & Position Button
    st.markdown("""
        <style>
            .block-container { padding: 0 !important; }
            iframe { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; border: none; z-index: 0; }
            
            /* Style the Streamlit Button to float at the bottom */
            div.stButton > button {
                position: fixed;
                bottom: 80px;
                left: 50%;
                transform: translateX(-50%);
                z-index: 99999;
                background-color: #3b82f6;
                color: white;
                border: none;
                padding: 12px 30px;
                font-family: 'JetBrains Mono', monospace;
                font-weight: 700;
                letter-spacing: 1px;
                border-radius: 8px;
                box-shadow: 0 0 20px rgba(59, 130, 246, 0.5);
                transition: all 0.3s;
            }
            div.stButton > button:hover {
                background-color: #2563eb;
                transform: translateX(-50%) scale(1.05);
                box-shadow: 0 0 30px rgba(59, 130, 246, 0.8);
            }
            header, footer, .stDeployButton { visibility: hidden; }
        </style>
    """, unsafe_allow_html=True)

    # 4. THE NAVIGATION TRIGGER
    if st.button("INITIALIZE SYSTEM"):
        st.session_state.page = 'dashboard'
        st.rerun()
