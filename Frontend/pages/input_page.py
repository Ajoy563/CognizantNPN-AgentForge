import streamlit as st
from services.api_client import generate_blueprint


def render(on_generated):
    st.markdown('<div class="narrow"><div class="page-intro"><small>NEW BLUEPRINT</small><h1>Let’s Build Your Solution</h1><p>Provide a few details about your business idea and constraints. Our AI agents will do the rest.</p></div><div class="app-card">', unsafe_allow_html=True)
    st.markdown('<div class="card-head"><div><h2>Tell us about your idea</h2><p>The more context you share, the more precise your blueprint.</p></div><span class="private">Private workspace</span></div>', unsafe_allow_html=True)
    with st.form('blueprint_form'):
        idea = st.text_area('Business idea / problem statement', placeholder='Describe your business idea, problem statement or the solution you are looking for...', height=135)
        left, right = st.columns(2)
        with left:
            technology = st.selectbox('Technology preference', ['Open Source', 'Enterprise'])
            traffic = st.text_input('Expected daily traffic', value='20,000', placeholder='e.g. 20,000')
            country = st.text_input('Country / data residency', value='United States')
        with right:
            cloud = st.selectbox('Cloud preference', ['No Preference', 'AWS', 'Azure', 'GCP'])
            timeline = st.selectbox('Delivery timeline', ['2', '4', '6', '9+'])
        submitted = st.form_submit_button('Generate Blueprint  →', use_container_width=True)
    if submitted:
        if not all([idea.strip(), traffic.strip(), country.strip()]): st.error('Please complete all required fields.')
        else: on_generated(generate_blueprint({'idea': idea, 'technology': technology, 'cloud': cloud, 'traffic': traffic, 'timeline': timeline, 'country': country}))
    st.markdown('</div><div class="agent-note">Built by a team of AI specialists<br><small>Five agents will review your brief, challenge assumptions, and assemble a practical plan.</small></div></div>', unsafe_allow_html=True)
