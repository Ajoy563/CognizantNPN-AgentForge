import streamlit as st
from services.auth_client import sign_up
from components.header import brand


def render(on_success, on_switch, on_back):
    st.markdown('<div class="auth-shell"><div class="auth-card">', unsafe_allow_html=True)
    brand(); st.markdown('<div class="auth-title"><h1>Create Your Account</h1><p>Start building your solution with SolutionForge AI</p></div>', unsafe_allow_html=True)
    with st.form('signup_form'):
        name = st.text_input('Full Name', placeholder='John Doe')
        email = st.text_input('Email address', placeholder='you@company.com')
        password = st.text_input('Password', type='password', placeholder='Create a password')
        confirm = st.text_input('Confirm Password', type='password', placeholder='Confirm your password')
        st.checkbox('I agree to the Terms of Service and Privacy Policy', value=False)
        submitted = st.form_submit_button('Create Account  →', use_container_width=True)
    if submitted:
        if password != confirm: st.error('Passwords do not match.')
        else:
            user, error = sign_up(email, password, name)
            if error: st.error(error)
            else: on_success(user, email, name)
    st.markdown('<div class="auth-divider"><span>or continue with</span></div><div class="social"><button>G　Continue with Google</button><button>■　Continue with Microsoft</button></div><p class="auth-switch">Already have an account? ', unsafe_allow_html=True)
    if st.button('Sign In', key='signup_switch'): on_switch()
    if st.button('← Back to Home', key='signup_back'): on_back()
    st.markdown('</div></div>', unsafe_allow_html=True)
