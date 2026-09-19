import os
import requests
from typing import Optional, Tuple
import streamlit as st

def get_api_key():
    return os.getenv('VITE_FIREBASE_API_KEY') or os.getenv('FIREBASE_API_KEY')

def sign_in(email: str, password: str) -> Tuple[Optional[dict], Optional[str]]:
    api_key = get_api_key()
    if not api_key:
        return None, "Firebase API Key is missing in environment."
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={api_key}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        data = response.json()
        st.session_state['id_token'] = data.get('idToken')
        return {"email": data.get("email"), "uid": data.get("localId")}, None
    else:
        err = response.json().get('error', {}).get('message', 'Authentication failed')
        return None, err

def sign_up(email: str, password: str, name: str) -> Tuple[Optional[dict], Optional[str]]:
    api_key = get_api_key()
    if not api_key:
        return None, "Firebase API Key is missing in environment."
    url = f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={api_key}"
    payload = {"email": email, "password": password, "returnSecureToken": True}
    response = requests.post(url, json=payload)
    if response.status_code == 200:
        data = response.json()
        st.session_state['id_token'] = data.get('idToken')
        return {"email": data.get("email"), "uid": data.get("localId")}, None
    else:
        err = response.json().get('error', {}).get('message', 'Registration failed')
        return None, err

def sign_out() -> None:
    if 'id_token' in st.session_state:
        del st.session_state['id_token']
