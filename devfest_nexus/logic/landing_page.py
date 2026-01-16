"""
Landing Page Component - Fullscreen Overlay Strategy
====================================================
Uses CSS injection to force iframe fullscreen, eliminating Streamlit's
layout constraints and scrollbar issues.

Strategy:
1. Render HTML component with height=0 to prevent ghost spacing
2. Inject global CSS to make iframe position:fixed and cover entire viewport
3. Hide Streamlit UI elements (header, footer, deploy button)
"""

import streamlit as st
import streamlit.components.v1 as components

def render_landing_page():
    """
    Renders the Nexus landing page using fullscreen overlay hack.
    This bypasses Streamlit's layout system entirely.
    """
    # 1. The Raw HTML
    html_code = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NEXUS</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@200;300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        :root {
            /* Matte Black / Charcoal Theme */
            --bg-dark: #121212; 
            --text-primary: #EDEDED;
            --text-secondary: #888888;
            --neon-blue: #3b82f6;
            --neon-purple: #8b5cf6;
            --neon-green: #10b981;
            --glass-border: rgba(255, 255, 255, 0.04);
            /* Darker, Matte Glass */
            --glass-bg: rgba(15, 15, 15, 0.8); 
            --header-bg: rgba(18, 18, 18, 0.8);
        }
        * { box-sizing: border-box; }
        body {
            background-color: var(--bg-dark);
            color: var(--text-primary);
            font-family: 'Inter', sans-serif;
            overflow: hidden; /* Prevent scroll within iframe */
            margin: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            height: 100vh;
        }
        /* --- Interactive Background --- */
        #bg-canvas {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            z-index: -1;
            opacity: 0.4; 
        }
        /* --- Intro Animation Sequence --- */
        #intro-overlay {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: var(--bg-dark);
            z-index: 100;
            display: flex;
            align-items: center;
            justify-content: center;
            animation: pan-out-reveal 1.2s ease-in-out 5.5s forwards;
        }
        .svg-intro-container {
            width: 600px;
            height: 150px;
            filter: drop-shadow(0 0 10px rgba(255,255,255,0.1));
        }
        /* SVG Animations */
        .intro-line { fill: none; stroke: var(--text-primary); stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; stroke-dasharray: 400; stroke-dashoffset: 400; }
        .intro-node { fill: var(--bg-dark); stroke: var(--text-primary); stroke-width: 2; opacity: 0; r: 5; transform-origin: center; transform-box: fill-box; }
        .path-n { animation: draw-line 1s cubic-bezier(0.2, 0, 0.2, 1) 0.5s forwards; }
        .node-n { animation: pop-in 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards; }
        .path-e { animation: draw-line 1s cubic-bezier(0.2, 0, 0.2, 1) 1.2s forwards; }
        .node-e { animation: pop-in 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) 1.2s forwards; }
        .path-x { animation: draw-line 1s cubic-bezier(0.2, 0, 0.2, 1) 1.9s forwards; }
        .node-x { animation: pop-in 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) 1.9s forwards; }
        .path-u { animation: draw-line 1s cubic-bezier(0.2, 0, 0.2, 1) 2.6s forwards; }
        .node-u { animation: pop-in 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) 2.6s forwards; }
        .path-s { animation: draw-line 1s cubic-bezier(0.2, 0, 0.2, 1) 3.3s forwards; }
        .node-s { animation: pop-in 0.3s cubic-bezier(0.175, 0.885, 0.32, 1.275) 3.3s forwards; }
        @keyframes draw-line { to { stroke-dashoffset: 0; } }
        @keyframes pop-in { 0% { opacity: 0; transform: scale(0); } 100% { opacity: 1; transform: scale(1); } }
        @keyframes pan-out-reveal { 
            0% { opacity: 1; transform: scale(1); pointer-events: auto; } 
            90% { opacity: 0; transform: scale(1.05); pointer-events: none; } 
            100% { opacity: 0; visibility: hidden; pointer-events: none; } 
        }
        /* --- Layout Sizing (CRITICAL) --- */
        #main-wrapper {
            display: flex;
            flex-direction: column;
            width: 100%;
            height: 100%;
            opacity: 0;
            animation: fade-in 1.5s ease-out 6.0s forwards;
            padding-top: 70px;
            justify-content: center;
        }
        @keyframes fade-in { from { opacity: 0; } to { opacity: 1; } }
        /* --- Header --- */
        .site-header {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 70px; 
            background: var(--header-bg);
            backdrop-filter: blur(12px);
            border-bottom: 1px solid rgba(255,255,255,0.03);
            display: flex;
            align-items: center;
            justify-content: space-between; 
            padding: 0 40px; 
            z-index: 50;
        }
        .header-brand {
            font-family: 'Inter', sans-serif;
            font-weight: 700;
            font-size: 1.1rem;
            letter-spacing: -0.2px;
            color: var(--text-primary);
            display: flex;
            align-items: center;
            gap: 12px;
        }
        .header-version {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.7rem;
            color: var(--text-secondary);
            letter-spacing: 1px;
            opacity: 0.6;
        }
        /* --- Hero --- */
        .hero-section {
            text-align: center;
            padding: 0 20px;
            max-width: 800px;
            margin: 0 auto 4vh auto;
            z-index: 10;
            flex-shrink: 0;
        }
        .hero-title {
            font-family: 'Inter', sans-serif;
            font-weight: 400;
            font-size: 0.75rem; 
            color: var(--text-secondary);
            letter-spacing: 3px;
            text-transform: uppercase;
            margin-bottom: 1.5vh;
            opacity: 0.8;
        }
        .hero-desc {
            font-family: 'Inter', sans-serif;
            font-weight: 300;
            font-size: 2.5rem;
            line-height: 1.2;
            color: var(--text-primary);
            margin-bottom: 2vh;
            letter-spacing: -1px;
        }
        .hero-sub {
            font-family: 'Inter', sans-serif;
            font-weight: 300;
            font-size: 1rem;
            color: #666;
            line-height: 1.6;
            max-width: 450px;
            margin: 0 auto;
        }
        /* --- Monolith Cards --- */
        .content-area {
            display: flex;
            align-items: flex-start;
            justify-content: center;
            padding: 0 40px;
            width: 100%;
            flex-grow: 0;
            padding-bottom: 5vh;
        }
        .cards-container {
            display: flex;
            gap: 16px;
            width: 100%;
            max-width: 900px;
            z-index: 10;
            height: 35vh;
            min-height: 280px;
            max-height: 400px;
        }
        .monolith-card {
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            border-radius: 4px;
            padding: 30px;
            flex: 1;
            cursor: pointer;
            transition: all 0.5s cubic-bezier(0.22, 1, 0.36, 1);
            position: relative;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        }
        .monolith-status {
            width: 100%;
            height: 2px;
            background: rgba(255,255,255,0.1);
            position: absolute;
            top: 0;
            left: 0;
            transition: all 0.3s ease;
        }
        .monolith-card:hover {
            transform: translateY(-8px);
            background: rgba(25, 25, 25, 0.9);
            border-color: rgba(255,255,255,0.1);
        }
        .card-a:hover .monolith-status { background: var(--neon-blue); box-shadow: 0 0 15px var(--neon-blue); }
        .card-b:hover .monolith-status { background: var(--neon-purple); box-shadow: 0 0 15px var(--neon-purple); }
        .card-c:hover .monolith-status { background: var(--neon-green); box-shadow: 0 0 15px var(--neon-green); }
        .card-index {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.7rem;
            color: var(--text-secondary);
            opacity: 0.5;
            letter-spacing: 1px;
            margin-bottom: auto;
        }
        .card-title {
            font-family: 'Inter', sans-serif;
            font-weight: 500;
            font-size: 1.1rem;
            color: var(--text-primary);
            letter-spacing: -0.5px;
            margin-bottom: 20px;
        }
        .target-list {
            display: flex;
            flex-direction: column;
            gap: 8px;
        }
        .target-item {
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.65rem;
            color: var(--text-secondary);
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .target-dot {
            width: 4px;
            height: 4px;
            background: #333;
            border-radius: 50%;
            transition: 0.3s;
        }
        .monolith-card:hover .target-dot { background: white; }
        .action-text {
            font-size: 0.7rem;
            font-weight: 600;
            letter-spacing: 1px;
            opacity: 0;
            transform: translateY(10px);
            transition: all 0.4s ease;
            margin-top: auto;
            text-transform: uppercase;
        }
        .card-a .action-text { color: var(--neon-blue); }
        .card-b .action-text { color: var(--neon-purple); }
        .card-c .action-text { color: var(--neon-green); }
        .monolith-card:hover .action-text { opacity: 1; transform: translateY(0); }
    </style>
</head>
<body>
    <canvas id="bg-canvas"></canvas>
    <div id="intro-overlay">
        <svg class="svg-intro-container" viewBox="0 0 500 120">
            <!-- N -->
            <path class="intro-line path-n" d="M20 100 L20 20 L80 100 L80 20" />
            <circle class="intro-node node-n" cx="20" cy="100" style="animation-delay: 0.5s"/>
            <circle class="intro-node node-n" cx="20" cy="20" style="animation-delay: 0.7s"/>
            <circle class="intro-node node-n" cx="80" cy="100" style="animation-delay: 0.9s"/>
            <circle class="intro-node node-n" cx="80" cy="20" style="animation-delay: 1.1s"/>
            <!-- E -->
            <path class="intro-line path-e" d="M160 20 L110 20 L110 100 L160 100 M110 60 L150 60" />
            <circle class="intro-node node-e" cx="160" cy="20" style="animation-delay: 1.2s"/>
            <circle class="intro-node node-e" cx="110" cy="20" style="animation-delay: 1.3s"/>
            <circle class="intro-node node-e" cx="110" cy="60" style="animation-delay: 1.4s"/>
            <circle class="intro-node node-e" cx="150" cy="60" style="animation-delay: 1.45s"/>
            <circle class="intro-node node-e" cx="110" cy="100" style="animation-delay: 1.5s"/>
            <circle class="intro-node node-e" cx="160" cy="100" style="animation-delay: 1.6s"/>
            <!-- X -->
            <path class="intro-line path-x" d="M190 20 L250 100 M250 20 L190 100" />
            <circle class="intro-node node-x" cx="190" cy="20" style="animation-delay: 1.9s"/>
            <circle class="intro-node node-x" cx="250" cy="100" style="animation-delay: 2.1s"/>
            <circle class="intro-node node-x" cx="250" cy="20" style="animation-delay: 2.0s"/>
            <circle class="intro-node node-x" cx="190" cy="100" style="animation-delay: 2.2s"/>
            <!-- U -->
            <path class="intro-line path-u" d="M280 20 L280 80 Q280 100 300 100 L320 100 Q340 100 340 80 L340 20" />
            <circle class="intro-node node-u" cx="280" cy="20" style="animation-delay: 2.6s"/>
            <circle class="intro-node node-u" cx="280" cy="80" style="animation-delay: 2.8s"/>
            <circle class="intro-node node-u" cx="340" cy="80" style="animation-delay: 3.0s"/>
            <circle class="intro-node node-u" cx="340" cy="20" style="animation-delay: 3.1s"/>
            <!-- S -->
            <path class="intro-line path-s" d="M430 20 L380 20 L380 60 L430 60 L430 100 L380 100" />
            <circle class="intro-node node-s" cx="430" cy="20" style="animation-delay: 3.3s"/>
            <circle class="intro-node node-s" cx="380" cy="20" style="animation-delay: 3.4s"/>
            <circle class="intro-node node-s" cx="380" cy="60" style="animation-delay: 3.6s"/>
            <circle class="intro-node node-s" cx="430" cy="60" style="animation-delay: 3.8s"/>
            <circle class="intro-node node-s" cx="430" cy="100" style="animation-delay: 3.9s"/>
            <circle class="intro-node node-s" cx="380" cy="100" style="animation-delay: 4.1s"/>
        </svg>
    </div>
    <div id="main-wrapper">
        <header class="site-header">
            <div class="header-brand">NEXUS</div>
            <div class="header-version">V5.0</div>
        </header>
        <div class="hero-section">
            <h2 class="hero-title">Intelligent Networking Engine</h2>
            <p class="hero-desc">Architecting Serendipity through<br>Temporal Intelligence.</p>
            <p class="hero-sub">Connecting intent with opportunity by analyzing professional signals in real-time.</p>
        </div>
        <div class="content-area">
            <div class="cards-container">
                <div class="monolith-card card-a group">
                    <div class="monolith-status"></div>
                    <div class="card-index">01 // CONTEXT</div>
                    <div>
                        <h3 class="card-title">Student / Intern</h3>
                        <div class="target-list">
                            <div class="target-item"><div class="target-dot"></div> Alumni Networks</div>
                            <div class="target-item"><div class="target-dot"></div> Campus Recruiters</div>
                            <div class="target-item"><div class="target-dot"></div> Mentorship Paths</div>
                        </div>
                    </div>
                    <div class="action-text">INITIALIZE SYSTEM</div>
                </div>
                <div class="monolith-card card-b group">
                    <div class="monolith-status"></div>
                    <div class="card-index">02 // CONTEXT</div>
                    <div>
                        <h3 class="card-title">Founder</h3>
                        <div class="target-list">
                            <div class="target-item"><div class="target-dot"></div> Venture Capital</div>
                            <div class="target-item"><div class="target-dot"></div> Co-founder Matching</div>
                            <div class="target-item"><div class="target-dot"></div> Talent Acquisition</div>
                        </div>
                    </div>
                    <div class="action-text">INITIALIZE SYSTEM</div>
                </div>
                <div class="monolith-card card-c group">
                    <div class="monolith-status"></div>
                    <div class="card-index">03 // CONTEXT</div>
                    <div>
                        <h3 class="card-title">Researcher</h3>
                        <div class="target-list">
                            <div class="target-item"><div class="target-dot"></div> Lab Opportunities</div>
                            <div class="target-item"><div class="target-dot"></div> Citation Networks</div>
                            <div class="target-item"><div class="target-dot"></div> Conference Circles</div>
                        </div>
                    </div>
                    <div class="action-text">INITIALIZE SYSTEM</div>
                </div>
            </div>
        </div>
    </div>
    <script>
        const canvas = document.getElementById('bg-canvas');
        const ctx = canvas.getContext('2d');
        let width, height;
        let particlesArray;
        let mouse = { x: undefined, y: undefined, radius: 250, lastX: undefined, lastY: undefined };
        window.addEventListener('mousemove', function(event) {
            mouse.lastX = mouse.x;
            mouse.lastY = mouse.y;
            mouse.x = event.x;
            mouse.y = event.y;
        });
        class Particle {
            constructor(x, y, size) {
                this.x = x; this.y = y; this.size = size;
                this.baseVx = (Math.random() * 0.2) - 0.1;
                this.baseVy = (Math.random() * 0.2) - 0.1;
                this.vx = this.baseVx; 
                this.vy = this.baseVy;
                this.friction = 0.96;
            }
            draw() {
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2, false);
                ctx.fillStyle = 'rgba(255, 255, 255, 0.4)'; 
                ctx.fill();
            }
            update() {
                if(mouse.x != undefined && mouse.lastX != undefined) {
                    let dx = mouse.x - this.x; 
                    let dy = mouse.y - this.y;
                    let distance = Math.sqrt(dx*dx + dy*dy);
                    if (distance < mouse.radius) {
                        let mouseVx = mouse.x - mouse.lastX;
                        let mouseVy = mouse.y - mouse.lastY;
                        let force = (mouse.radius - distance) / mouse.radius;
                        this.vx += mouseVx * force * 0.05; 
                        this.vy += mouseVy * force * 0.05;
                    }
                }
                this.vx *= this.friction;
                this.vy *= this.friction;
                if(Math.abs(this.vx) < Math.abs(this.baseVx)) this.vx = this.baseVx;
                if(Math.abs(this.vy) < Math.abs(this.baseVy)) this.vy = this.baseVy;
                this.x += this.vx;
                this.y += this.vy;
                if (this.x > width) this.x = 0;
                if (this.x < 0) this.x = width;
                if (this.y > height) this.y = 0;
                if (this.y < 0) this.y = height;
            }
        }
        function init() {
            width = window.innerWidth; height = window.innerHeight;
            canvas.width = width; canvas.height = height;
            particlesArray = [];
            let numberOfParticles = (width * height) / 10000;
            for (let i = 0; i < numberOfParticles; i++) {
                particlesArray.push(new Particle(Math.random() * width, Math.random() * height, (Math.random() * 1.5) + 0.5));
            }
        }
        function animate() {
            requestAnimationFrame(animate);
            ctx.clearRect(0, 0, width, height);
            for (let i = 0; i < particlesArray.length; i++) {
                particlesArray[i].update(); particlesArray[i].draw();
            }
        }
        window.addEventListener('resize', function(){ init(); });
        init(); animate();
        lucide.createIcons();
    </script>
</body>
</html>
    """
    
    # 2. Render the component (Height 0 prevents ghost spacing)
    components.html(html_code, height=0, scrolling=False)
    
    # 3. The "Nuclear" CSS Hack
    # This forces the IFrame to ignore Streamlit's layout and cover the screen.
    st.markdown("""
        <style>
            /* Remove Streamlit's default padding */
            .block-container {
                padding-top: 0rem;
                padding-bottom: 0rem;
                padding-left: 0rem;
                padding-right: 0rem;
            }
            
            /* Target the IFrame generated by components.html */
            iframe {
                position: fixed;
                top: 0;
                left: 0;
                width: 100vw;
                height: 100vh;
                border: none;
                margin: 0;
                padding: 0;
                overflow: hidden;
                z-index: 99999; /* Force it to top */
                display: block;
            }
            
            /* Hide Streamlit elements */
            header {visibility: hidden;}
            footer {visibility: hidden;}
            .stDeployButton {display:none;}
        </style>
    """, unsafe_allow_html=True)
