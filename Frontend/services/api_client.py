import os
import requests
import streamlit as st
from typing import Any, Dict

BASE_URL = "http://localhost:8000/api"

def get_headers():
    token = st.session_state.get('id_token')
    if not token:
        raise ValueError("Not authenticated")
    return {"Authorization": f"Bearer {token}"}

def generate_blueprint(brief: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{BASE_URL}/generate"
    cloud_val = str(brief.get("cloud", "aws")).lower()
    if cloud_val not in ["aws", "azure", "gcp", "none"]:
        cloud_val = "aws"
    try:
        traffic_val = int(brief.get("traffic", 1000))
    except (ValueError, TypeError):
        traffic_val = 1000
    try:
        timeline_val = int(brief.get("timeline", 3))
    except (ValueError, TypeError):
        timeline_val = 3

    payload = {
        "business_idea": brief.get("idea", "").strip(),
        "tech_preference": "enterprise" if brief.get("technology", "").lower() == "enterprise" else "opensource",
        "cloud_preference": cloud_val,
        "expected_daily_traffic": traffic_val,
        "delivery_timeline_months": timeline_val,
        "country": str(brief.get("country", "US")).strip() or "US"
    }
    resp = requests.post(url, json=payload, headers=get_headers())
    resp.raise_for_status()
    data = resp.json()
    blueprint_data = data.get("blueprint", {})
    # Mangle response back to frontend expected structure
    return {
        'summary': blueprint_data.get("requirements", {}).get("summary", ""),
        'scope': blueprint_data.get("requirements", {}).get("scope", []),
        'brief': brief,
        'stack': [
            ["Frontend", blueprint_data.get("technology", {}).get("frontend", "")],
            ["Backend", blueprint_data.get("technology", {}).get("backend", "")],
            ["Database", blueprint_data.get("technology", {}).get("database", "")],
            ["Cloud", blueprint_data.get("technology", {}).get("cloud", "")]
        ],
        'risks': [
            [risk.get("risk", ""), risk.get("impact", ""), risk.get("mitigation", "")]
            for risk in blueprint_data.get("validation", {}).get("risks", []) if isinstance(risk, dict)
        ],
        'project_id': blueprint_data.get("project_id"),
        'generation_id': blueprint_data.get("generation_id")
    }

def list_projects() -> list:
    url = f"{BASE_URL}/projects"
    resp = requests.get(url, headers=get_headers())
    resp.raise_for_status()
    return resp.json()

def get_project(project_id: str) -> dict:
    url = f"{BASE_URL}/projects/{project_id}"
    resp = requests.get(url, headers=get_headers())
    resp.raise_for_status()
    return resp.json()
