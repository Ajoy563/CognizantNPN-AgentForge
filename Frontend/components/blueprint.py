import streamlit as st


def download_markdown(data: dict) -> None:
    brief = data['brief']
    content = f"# SolutionForge AI Blueprint\n\n## Executive Summary\n{data['summary']}\n\n## Original Brief\n{brief['idea']}\n\n## MVP Scope\n" + '\n'.join(f'- {item}' for item in data['scope'])
    st.download_button('Download Markdown', content, 'solutionforge-blueprint.md', 'text/markdown', key='download_markdown')
