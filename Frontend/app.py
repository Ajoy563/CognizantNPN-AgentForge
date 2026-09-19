import os
from dotenv import load_dotenv
import streamlit as st

load_dotenv()

st.set_page_config(page_title='SolutionForge AI', page_icon=None, layout='wide', initial_sidebar_state='collapsed')
st.markdown('<style>@import url("https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@500;600;700&display=swap");</style>', unsafe_allow_html=True)
with open('styles/style.css') as f:
    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)

# Hide default Streamlit chrome
st.markdown('<style>[data-testid="stSidebar"]{display:none} #MainMenu{visibility:hidden} footer{visibility:hidden} header{visibility:hidden}</style>', unsafe_allow_html=True)


def init_state():
    defaults = {'screen': 'home', 'app_view': 'new', 'profile': {'name': 'Alex Morgan', 'email': 'alex@solutionforge.ai'}, 'blueprint': None}
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def main():
    init_state()
    screen = st.session_state.screen

    if screen == 'home':
        from pages.home import render
        render(on_auth=lambda: st.session_state.update({'screen': 'signin'}))
    elif screen == 'signin':
        from pages.signin import render
        render(
            on_success=lambda user, email, name: st.session_state.update({'screen': 'app', 'app_view': 'new', 'profile': {'name': name, 'email': email}}),
            on_switch=lambda: st.session_state.update({'screen': 'signup'}),
            on_back=lambda: st.session_state.update({'screen': 'home'}),
        )
    elif screen == 'signup':
        from pages.signup import render
        render(
            on_success=lambda user, email, name: st.session_state.update({'screen': 'app', 'app_view': 'new', 'profile': {'name': name, 'email': email}}),
            on_switch=lambda: st.session_state.update({'screen': 'signin'}),
            on_back=lambda: st.session_state.update({'screen': 'home'}),
        )
    elif screen == 'app':
        from components.sidebar import render as sidebar
        from services.auth_client import sign_out

        view = st.session_state.app_view
        left, main_area = st.columns([1, 5.5], gap='small', vertical_alignment='top')

        with left:
            sidebar(
                view,
                on_navigate=lambda v: st.session_state.update({'app_view': v}),
                on_signout=lambda: (sign_out(), st.session_state.update({'screen': 'home'})),
            )

        with main_area:
            label = {'new': 'New Blueprint', 'processing': 'Processing', 'dashboard': 'Dashboard', 'settings': 'Settings'}[view]
            st.markdown(f'<div class="app-bar"><span>Workspace › <b>{label}</b></span><span class="online">● AI agents online</span></div><div class="app-content">', unsafe_allow_html=True)

            if view == 'new':
                from pages.input_page import render as page
                page(on_generated=lambda data: st.session_state.update({'blueprint': data, 'app_view': 'processing'}))
            elif view == 'processing':
                from pages.processing_page import render_page as page
                page(on_complete=lambda: st.session_state.update({'app_view': 'dashboard'}))
            elif view == 'dashboard':
                from pages.dashboard_page import render as page
                page(st.session_state.blueprint or {'summary': '', 'scope': [], 'brief': {}, 'stack': [], 'risks': []})
            elif view == 'settings':
                from pages.settings import render as page
                page(on_home=lambda: st.session_state.update({'screen': 'home'}))

            st.markdown('</div>', unsafe_allow_html=True)


if __name__ == '__main__':
    main()
