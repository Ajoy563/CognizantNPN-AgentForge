import streamlit as st
from services.auth_client import sign_in
from components.header import brand


def render(on_success, on_switch, on_back):
    st.markdown('<div class="auth-shell"><div class="auth-card">', unsafe_allow_html=True)
    brand(); st.markdown('<div class="auth-title"><h1>Welcome Back</h1><p>Sign in to continue to SolutionForge AI</p></div>', unsafe_allow_html=True)
    with st.form('signin_form'):
        email = st.text_input('Email address', placeholder='you@company.com')
        password = st.text_input('Password', type='password', placeholder='Enter your password')
        st.checkbox('Remember me')
        submitted = st.form_submit_button('Sign In  →', use_container_width=True)
    if submitted:
        user, error = sign_in(email, password)
        if error: st.error(error)
        else: on_success(user, email, 'Alex Morgan')
    st.markdown('<div class="auth-divider"><span>or continue with</span></div><div class="social"><button>G　Continue with Google</button><button>■　Continue with Microsoft</button></div><p class="auth-switch">Don’t have an account? ', unsafe_allow_html=True)
    if st.button('Create an Account', key='signin_switch'): on_switch()
    if st.button('← Back to Home', key='signin_back'): on_back()
    st.markdown('</div></div>', unsafe_allow_html=True)
