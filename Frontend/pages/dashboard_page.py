import streamlit as st
from components.blueprint import download_markdown
from services.api_client import list_projects, get_project

def render(data=None):
    if not data or not getattr(st.session_state, 'viewing_blueprint', False):
        st.markdown('<h1>Your Projects & History</h1>', unsafe_allow_html=True)
        try:
            projects = list_projects()
            if not projects:
                st.info("No projects found.")
            else:
                for proj in projects:
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.subheader(proj.get('name', 'Untitled'))
                        st.write(f"Created at: {proj.get('created_at')}")
                    with col2:
                        if st.button("View", key=f"view_{proj['project_id']}"):
                            # Fetch full project and assume it acts like 'data'
                            st.session_state.viewing_blueprint = True
                            st.session_state.selected_project_id = proj['project_id']
                            st.rerun()
        except Exception as e:
            st.error(f"Failed to load projects: {e}")
        return

    # If we are viewing a specific blueprint
    if getattr(st.session_state, 'viewing_blueprint', False) and getattr(st.session_state, 'selected_project_id', None):
        if st.button("← Back to History"):
            st.session_state.viewing_blueprint = False
            st.rerun()
        
        # Here we should fetch the project detail but for simplicity, let's just use `data` if it was passed,
        # or we fetch from API. Let's fetch from API.
        try:
            proj_detail = get_project(st.session_state.selected_project_id)
            st.write(f"### Project: {proj_detail.get('name')}")
            gens = proj_detail.get('generations', [])
            if not gens:
                st.info("No generations found for this project.")
            else:
                for gen in gens:
                    st.write(f"Generation ID: {gen['generation_id']} (Status: {gen['validation_status']})")
        except Exception as e:
            st.error(f"Failed to load project details: {e}")
        return

    # Fallback to the original dashboard layout if 'data' is passed from 'processing_page.py'
    st.markdown(f'<div class="dashboard"><div class="dash-head"><div><small>SOLUTION BLUEPRINT</small><h1>Your Solution Blueprint</h1></div></div>', unsafe_allow_html=True)
    tabs = st.tabs(['Overview', 'Architecture', 'Technology', 'Delivery Plan', 'Risks'])
    with tabs[0]:
        st.write(data.get('summary', ''))
    with tabs[1]:
        st.write("Architecture Overview")
    with tabs[2]:
        for category, value in data.get('stack', []): st.write(f"**{category}**: {value}")
    with tabs[3]:
        st.write("Delivery timeline...")
    with tabs[4]:
        for risk, impact, mitigation in data.get('risks', []): st.write(f"**{risk}** ({impact}): {mitigation}")
    
    if st.button("← Back to Dashboard"):
        st.session_state.viewing_blueprint = False
        st.session_state.blueprint = None
        st.rerun()

