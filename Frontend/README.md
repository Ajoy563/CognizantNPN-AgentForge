# SolutionForge AI — Streamlit frontend

This folder contains the Streamlit version of the SolutionForge AI frontend. It keeps the same dark landing page, clean authentication pages, workspace sidebar, blueprint form, processing flow, results dashboard, reports, and settings experience.

## Structure

- `app.py` — Streamlit entry point and route state
- `pages/` — page-level views
- `components/` — shared UI pieces
- `services/` — authentication and blueprint API boundaries
- `styles/style.css` — visual system
- `assets/` — optional brand assets

The authentication service uses Supabase email/password auth when the existing project environment values are available. Blueprint generation is kept behind `services/api_client.py` so the backend can be connected without changing the UI.
