import streamlit as st
from services.auth_client import sign_out


def render(on_home):
    profile = st.session_state.get('profile', {'name': 'Alex Morgan', 'email': 'alex@solutionforge.ai'})
    st.markdown(f'<div class="narrow"><div class="page-intro"><small>WORKSPACE SETTINGS</small><h1>Settings</h1><p>Manage your profile and report preferences.</p></div><div class="settings-card"><div class="profile-row"><span class="avatar">{profile["name"][0]}</span><div><h2>{profile["name"]}</h2><p>{profile["email"]}</p></div></div><hr class="settings-divider"><h3>Report preferences</h3>', unsafe_allow_html=True)
    st.checkbox('Generate PDF Report', value=True)
    st.checkbox('Generate Markdown Report', value=True)
    st.markdown('</div></div>', unsafe_allow_html=True)
    if st.button('Sign Out', key='settings_signout'):
        sign_out(); on_home()
