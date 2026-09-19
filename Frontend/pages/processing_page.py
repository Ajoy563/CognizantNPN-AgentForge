import time
import streamlit as st
from components.progress import render


def render_page(on_complete):
    st.markdown('<div class="processing"><div class="page-intro" style="text-align:center"><small>● LIVE RUN</small><h1>Our AI Team Is Working on Your Blueprint</h1><p>This may take a few minutes. You can keep this page open.</p></div>', unsafe_allow_html=True)
    render()
    st.markdown('<p style="text-align:center;color:#8b96aa;font-size:12px">Multi-agent orchestration is checking each decision for consistency.</p></div>', unsafe_allow_html=True)
    if 'processing_started' not in st.session_state:
        st.session_state.processing_started = time.time()
    if time.time() - st.session_state.processing_started > 2.5:
        on_complete()
    else:
        time.sleep(0.35)
        st.rerun()
