import streamlit as st


def metric(label: str, value: str) -> None:
    st.markdown(f'<div class="metric"><span class="cap-icon">+</span><span>{label}<b>{value}</b></span></div>', unsafe_allow_html=True)


def info_card(title: str, items: list[str]) -> None:
    st.markdown(f'<div class="result-card"><h2>{title}</h2><ul>{"".join(f"<li>{item}</li>" for item in items)}</ul></div>', unsafe_allow_html=True)
