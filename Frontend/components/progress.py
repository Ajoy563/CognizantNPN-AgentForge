import streamlit as st


def render() -> None:
    steps = ['Business Analyst', 'Solution Architect', 'Technology Advisor', 'Delivery Planner', 'Consistency Validator', 'Generating Final Report']
    details = ['Analyzing business requirements...', 'Designing architecture...', 'Selecting technology stack...', 'Creating workstreams, timeline and team plan...', 'Reviewing and validating the complete blueprint...', 'Preparing the final report...']
    st.markdown('<div class="processing-card">', unsafe_allow_html=True)
    for index, step in enumerate(steps):
        state = 'done' if index < 3 else 'current' if index == 3 else ''
        marker = '✓' if index < 3 else '•'
        st.markdown(f'<div class="process-row {state}"><span class="marker">{marker}</span><div><strong>{step}</strong><small>{details[index]}</small></div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
