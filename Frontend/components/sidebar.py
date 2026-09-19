import streamlit as st
from components.header import brand


def render(current: str, on_navigate, on_signout) -> None:
    st.markdown('<aside class="sidebar">', unsafe_allow_html=True)
    brand()
    st.markdown('<div class="label">WORKSPACE</div>', unsafe_allow_html=True)
    for key, label in [('new', 'New Blueprint'), ('processing', 'Processing'), ('dashboard', 'Dashboard'), ('settings', 'Settings')]:
        if st.button(label, key=f'nav_{key}', type='primary' if current == key else 'secondary'):
            on_navigate(key)
    st.markdown('<div style="height:42vh"></div>', unsafe_allow_html=True)
    profile = st.session_state.get('profile', {'name': 'Alex Morgan', 'email': 'alex@solutionforge.ai'})
    st.markdown(f'<div class="profile-row"><span class="avatar">{profile["name"][0]}</span><span><b>{profile["name"]}</b><br><small>{profile["email"]}</small></span></div>', unsafe_allow_html=True)
    if st.button('Sign Out', key='side_signout'):
        on_signout()
    st.markdown('</aside>', unsafe_allow_html=True)
