import streamlit as st
from components.header import brand


def render(on_auth):
    st.markdown('<div class="site-shell">', unsafe_allow_html=True)
    st.markdown('<div class="topbar">', unsafe_allow_html=True)
    brand()
    st.markdown('<nav><a href="#home">Home</a><a href="#how">How It Works</a><a href="#about">About</a></nav>', unsafe_allow_html=True)
    if st.button('Sign In  →', key='home_signin'):
        on_auth()
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<main id="home" class="hero"><div class="hero-copy"><div class="eyebrow">AI-Powered Solution Consulting</div><h1>Turn Your Business Idea into a <span>Real-World Solution</span></h1><p>Get a complete technology blueprint — from business analysis to architecture, technology and delivery plan — in minutes using the power of multi-agent AI.</p>', unsafe_allow_html=True)
    if st.button('Generate My Solution  →', key='hero_generate'):
        on_auth()
    st.markdown('</div><div class="agent-flow"><div class="flow-label"><span>MEET YOUR AI TEAM</span><span>4 AGENTS · 1 BLUEPRINT</span></div>', unsafe_allow_html=True)
    for index, (name, detail) in enumerate([('Business Analyst', 'Clarifies goals & requirements'), ('Solution Architect', 'Designs the right blueprint'), ('Technology Advisor', 'Recommends the best-fit stack'), ('Delivery Planner', 'Maps the path to launch')]):
        st.markdown(f'<div class="agent"><div class="agent-icon">{index + 1:02d}</div><div><strong>{name}</strong><small>{detail}</small></div><em>0{index + 1}</em></div>', unsafe_allow_html=True)
    st.markdown('</div></main><section id="how" class="capabilities">', unsafe_allow_html=True)
    for title, detail in [('Business Analysis', 'Understand the problem before writing a line of code.'), ('Solution Architecture', 'Turn ambition into a clear, scalable system design.'), ('Technology Recommendations', 'Choose tools that fit your context, scale, and budget.'), ('Delivery Planning', 'Move from idea to execution with confidence.')]:
        st.markdown(f'<div class="capability"><div class="cap-icon">+</div><div><h3>{title}</h3><p>{detail}</p></div></div>', unsafe_allow_html=True)
    st.markdown('</section><section id="about" class="footer-band"><div><small>FROM FIRST THOUGHT TO FIRST RELEASE</small><h2>Ideas are everywhere.<br><span>Execution is rare.</span></h2></div><p>SolutionForge AI gives teams the clarity to build what matters next.</p></section></div>', unsafe_allow_html=True)
