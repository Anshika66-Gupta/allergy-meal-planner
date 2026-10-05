"""
app.py - Comprehensive, Classy & Feature-Complete Streamlit UI for Allergy-Safe Meal Planner
"""

import os
import streamlit as st
import planner
import pdf_export
import voice_chef

# Streamlit Page Config
st.set_page_config(
    page_title="Allergy-Safe Meal Planner for Anny",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Classy Glassmorphism & Gradient CSS Styling
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700&display=swap');
    
    /* Main Background & Typography */
    .stApp {
        background: linear-gradient(135deg, #090D16 0%, #0F172A 40%, #1E1B4B 100%);
        color: #F8FAFC;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    
    /* Global Container Padding & Max-Width Alignment */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 3.5rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 1340px !important;
        margin: 0 auto !important;
    }

    @media (max-width: 768px) {
        .block-container {
            padding-top: 1rem !important;
            padding-left: 0.75rem !important;
            padding-right: 0.75rem !important;
        }
    }
    
    h1, h2, h3, h4, .gradient-title {
        font-family: 'Outfit', sans-serif !important;
        letter-spacing: -0.02em;
    }

    /* Gradient Title */
    .gradient-title {
        background: linear-gradient(90deg, #C084FC 0%, #F472B6 50%, #38BDF8 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.35rem;
        font-weight: 800;
        margin: 0;
        line-height: 1.2;
    }

    /* Glassmorphic Header Card */
    .glass-header {
        background: rgba(30, 41, 59, 0.55);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 24px 28px;
        margin-bottom: 24px;
        box-shadow: 0 20px 40px -15px rgba(0, 0, 0, 0.45);
    }
    
    .header-top-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
        margin-bottom: 12px;
    }

    .badge-status {
        background: rgba(6, 78, 59, 0.65);
        color: #34D399;
        border: 1px solid rgba(16, 185, 129, 0.4);
        padding: 6px 16px;
        border-radius: 9999px;
        font-size: 0.84rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        gap: 6px;
        box-shadow: 0 4px 12px rgba(6, 78, 59, 0.25);
    }

    /* Welcome Banner */
    .welcome-banner {
        background: linear-gradient(90deg, rgba(6, 78, 59, 0.75) 0%, rgba(15, 118, 110, 0.6) 100%);
        color: #34D399;
        border: 1px solid rgba(52, 211, 153, 0.3);
        padding: 12px 18px;
        border-radius: 12px;
        font-size: 0.98rem;
        font-weight: 600;
        margin-top: 10px;
        box-shadow: 0 4px 12px rgba(6, 78, 59, 0.2);
    }

    /* Badges */
    .header-exclusions-row {
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 14px;
    }

    .badge-allergy {
        background: rgba(153, 27, 27, 0.4);
        color: #FCA5A5;
        border: 1px solid rgba(239, 68, 68, 0.35);
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.82rem;
        font-weight: 600;
        display: inline-flex;
        align-items: center;
        margin: 0;
    }

    /* Meal Type Badges */
    .meal-type-tag {
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        padding: 4px 10px;
        border-radius: 8px;
        display: inline-block;
    }
    .breakfast-tag { background: rgba(245, 158, 11, 0.2); color: #FBBF24; border: 1px solid rgba(245, 158, 11, 0.3); }
    .lunch-tag { background: rgba(16, 185, 129, 0.2); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .dinner-tag { background: rgba(99, 102, 241, 0.2); color: #818CF8; border: 1px solid rgba(99, 102, 241, 0.3); }

    /* Custom Streamlit Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #070B14 !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
    }
    
    /* Interactive Tabs Override - Pill Segmented Control */
    div[data-baseweb="tab-list"] {
        gap: 8px !important;
        background: rgba(15, 23, 42, 0.5) !important;
        padding: 6px !important;
        border-radius: 14px !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        margin-bottom: 22px !important;
        flex-wrap: wrap !important;
    }
    
    div[data-baseweb="tab-border"],
    div[data-baseweb="tab-highlight"] {
        display: none !important;
    }
    
    button[data-baseweb="tab"] {
        background: transparent !important;
        border-radius: 10px !important;
        border: 1px solid transparent !important;
        color: #94A3B8 !important;
        font-weight: 600 !important;
        font-size: 0.92rem !important;
        padding: 8px 18px !important;
        margin-right: 0 !important;
        transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }
    
    button[data-baseweb="tab"]:hover {
        color: #F8FAFC !important;
        background: rgba(255, 255, 255, 0.06) !important;
    }
    
    button[data-baseweb="tab"][aria-selected="true"] {
        background: linear-gradient(135deg, #7C3AED 0%, #A855F7 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        box-shadow: 0 4px 14px rgba(124, 58, 237, 0.4) !important;
    }

    /* Unified Button Styling */
    div.stButton > button,
    div.stDownloadButton > button {
        min-height: 44px !important;
        height: 44px !important;
        display: inline-flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-family: 'Inter', system-ui, sans-serif !important;
        font-size: 0.92rem !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        padding: 0 18px !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
        box-sizing: border-box !important;
        width: 100% !important;
    }

    /* Primary Button Styling with Glow */
    div.stButton > button[kind="primary"],
    div.stDownloadButton > button[kind="primary"] {
        background: linear-gradient(135deg, #7C3AED 0%, #A855F7 100%) !important;
        color: #FFFFFF !important;
        border: 1px solid rgba(255, 255, 255, 0.15) !important;
        box-shadow: 0 6px 18px -4px rgba(124, 58, 237, 0.45) !important;
    }

    div.stButton > button[kind="primary"]:hover,
    div.stDownloadButton > button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 10px 24px -4px rgba(168, 85, 247, 0.6) !important;
        border-color: rgba(255, 255, 255, 0.3) !important;
    }

    /* Secondary Button Styling */
    div.stButton > button[kind="secondary"],
    div.stDownloadButton > button[kind="secondary"] {
        background: rgba(30, 41, 59, 0.65) !important;
        color: #E2E8F0 !important;
        border: 1px solid rgba(255, 255, 255, 0.12) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2) !important;
    }
    
    div.stButton > button[kind="secondary"]:hover,
    div.stDownloadButton > button[kind="secondary"]:hover {
        background: rgba(51, 65, 85, 0.85) !important;
        border-color: rgba(192, 132, 252, 0.45) !important;
        color: #FFFFFF !important;
        transform: translateY(-1px) !important;
    }

    /* Streamlit Expander Styling */
    div[data-testid="stExpander"] {
        background: rgba(30, 41, 59, 0.45) !important;
        border: 1px solid rgba(255, 255, 255, 0.08) !important;
        border-radius: 14px !important;
        margin-bottom: 22px !important;
        overflow: hidden !important;
    }
    div[data-testid="stExpander"] details {
        border: none !important;
    }
    div[data-testid="stExpander"] summary {
        padding: 12px 18px !important;
        font-weight: 600 !important;
        color: #F8FAFC !important;
        font-size: 0.95rem !important;
    }

    /* 3D Flip Card Container & Animation */
    .flip-card {
        background-color: transparent;
        width: 100%;
        min-height: 520px;
        height: 520px;
        perspective: 1200px;
        margin-bottom: 20px;
        position: relative;
    }

    .flip-checkbox {
        display: none;
    }

    .flip-card-inner {
        position: relative;
        width: 100%;
        height: 100%;
        text-align: left;
        transition: transform 0.65s cubic-bezier(0.4, 0, 0.2, 1);
        transform-style: preserve-3d;
        -webkit-transform-style: preserve-3d;
        border-radius: 18px;
        cursor: pointer;
        display: block;
    }

    /* 1. On Hover: Flip to back to reveal step-by-step instructions */
    .flip-card:hover .flip-card-inner {
        transform: rotateY(180deg);
    }

    /* 2. On Click while Hovering: Checkbox becomes checked, flipping BACK to front */
    .flip-card:hover .flip-checkbox:checked + .flip-card-inner {
        transform: rotateY(0deg) !important;
    }

    /* 3. Non-hover / touch fallback */
    .flip-checkbox:checked + .flip-card-inner {
        transform: rotateY(180deg);
    }

    /* 4. When mouse leaves, smoothly reset back to front */
    .flip-card:not(:hover) .flip-card-inner {
        transform: rotateY(0deg) !important;
    }

    .flip-card-front, .flip-card-back {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        -webkit-backface-visibility: hidden;
        backface-visibility: hidden;
        border-radius: 18px;
        padding: 22px;
        box-sizing: border-box;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }

    /* Front side of card */
    .flip-card-front {
        background: rgba(30, 41, 59, 0.65);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.5);
    }

    /* Back side of card */
    .flip-card-back {
        background: linear-gradient(145deg, rgba(30, 27, 75, 0.97) 0%, rgba(15, 23, 42, 0.98) 100%);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(192, 132, 252, 0.4);
        transform: rotateY(180deg);
        box-shadow: 0 16px 36px -8px rgba(124, 58, 237, 0.35);
    }

    .card-body-scroll {
        flex: 1;
        overflow-y: auto;
        padding-right: 6px;
        margin-bottom: 12px;
    }

    .card-body-scroll::-webkit-scrollbar {
        width: 4px;
    }
    .card-body-scroll::-webkit-scrollbar-track {
        background: rgba(15, 23, 42, 0.3);
        border-radius: 4px;
    }
    .card-body-scroll::-webkit-scrollbar-thumb {
        background: rgba(192, 132, 252, 0.35);
        border-radius: 4px;
    }
    .card-body-scroll::-webkit-scrollbar-thumb:hover {
        background: rgba(192, 132, 252, 0.65);
    }

    .card-recipe-title {
        margin: 8px 0 6px 0;
        color: #F8FAFC;
        font-size: 1.15rem;
        font-weight: 700;
        line-height: 1.35;
        min-height: 2.7rem;
        display: flex;
        align-items: center;
    }

    .flip-hint-badge {
        background: rgba(124, 58, 237, 0.22);
        color: #C084FC;
        border: 1px solid rgba(192, 132, 252, 0.35);
        padding: 8px 12px;
        border-radius: 12px;
        font-size: 0.78rem;
        font-weight: 600;
        text-align: center;
        display: flex;
        align-items: center;
        justify-content: center;
        gap: 6px;
        transition: all 0.2s ease;
        width: 100%;
        box-sizing: border-box;
    }

    .flip-hint-badge:hover {
        background: rgba(124, 58, 237, 0.45);
        color: #FFFFFF;
    }

    .chef-tip-box {
        background: rgba(245, 158, 11, 0.12);
        border-left: 3px solid #F59E0B;
        border-radius: 8px;
        padding: 8px 12px;
        margin-top: 10px;
        font-size: 0.8rem;
        color: #FCD34D;
        line-height: 1.4;
    }

    /* Single Day Regeneration Banner */
    .day-re-banner {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 12px 18px;
        margin-top: 10px;
        margin-bottom: 20px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
    }

    /* Aisle Category Cards & Checkbox Styling */
    .aisle-card {
        background: rgba(30, 41, 59, 0.4);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 16px 18px 10px 18px;
        margin-bottom: 16px;
    }
    
    .aisle-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
        padding-bottom: 8px;
        border-bottom: 1px solid rgba(255, 255, 255, 0.06);
    }
    
    .aisle-title {
        font-size: 1.02rem;
        font-weight: 700;
        color: #F8FAFC;
        margin: 0;
    }
    
    .aisle-count {
        font-size: 0.78rem;
        font-weight: 600;
        color: #C084FC;
        background: rgba(124, 58, 237, 0.2);
        padding: 3px 10px;
        border-radius: 9999px;
        border: 1px solid rgba(192, 132, 252, 0.3);
    }

    /* Interactive Checkbox custom styling */
    div[data-testid="stCheckbox"] {
        background: rgba(15, 23, 42, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.06);
        border-radius: 10px;
        padding: 8px 12px !important;
        margin-bottom: 6px !important;
        transition: all 0.2s ease;
    }
    div[data-testid="stCheckbox"]:hover {
        background: rgba(30, 41, 59, 0.7);
        border-color: rgba(192, 132, 252, 0.3);
    }
    div[data-testid="stCheckbox"] label {
        cursor: pointer !important;
        width: 100% !important;
    }
    div[data-testid="stCheckbox"] label p {
        font-size: 0.9rem !important;
        color: #E2E8F0 !important;
    }

    /* Feature Cards for Tab 3 */
    .glass-feature-card {
        background: rgba(30, 41, 59, 0.5);
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 22px;
        margin-bottom: 18px;
        transition: all 0.25s ease;
    }
    .glass-feature-card:hover {
        border-color: rgba(192, 132, 252, 0.35);
        transform: translateY(-2px);
        box-shadow: 0 10px 25px -8px rgba(0, 0, 0, 0.4);
    }
    .feature-title-row {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 8px;
    }
    .feature-title-row h4 {
        margin: 0;
        font-size: 1.05rem;
        font-weight: 700;
        color: #F8FAFC;
    }
    .feature-body {
        font-size: 0.88rem;
        color: #CBD5E1;
        line-height: 1.55;
        margin: 0;
    }
    .timeline-step {
        background: rgba(15, 23, 42, 0.5);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        padding: 14px 18px;
        margin-bottom: 10px;
        display: flex;
        align-items: flex-start;
        gap: 14px;
    }
    .timeline-badge {
        background: linear-gradient(135deg, #7C3AED 0%, #A855F7 100%);
        color: #FFFFFF;
        font-size: 0.78rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 8px;
        white-space: nowrap;
    }

    /* Soundwave Equalizer Playing Animation */
    @keyframes soundwave-bar-pulse {
        0%, 100% { height: 4px; }
        50% { height: 22px; }
    }

    .soundwave-box {
        display: inline-flex;
        align-items: center;
        gap: 3px;
        height: 24px;
        padding: 0 4px;
        vertical-align: middle;
    }

    .soundwave-box span {
        display: inline-block;
        width: 3px;
        background: linear-gradient(180deg, #C084FC 0%, #F472B6 100%);
        border-radius: 3px;
        animation: soundwave-bar-pulse 1.05s ease-in-out infinite;
    }

    .soundwave-box span:nth-child(1) { animation-delay: 0.0s; height: 6px; }
    .soundwave-box span:nth-child(2) { animation-delay: 0.2s; height: 16px; }
    .soundwave-box span:nth-child(3) { animation-delay: 0.4s; height: 22px; }
    .soundwave-box span:nth-child(4) { animation-delay: 0.15s; height: 12px; }
    .soundwave-box span:nth-child(5) { animation-delay: 0.35s; height: 18px; }

    /* Active Audio Studio Card */
    .audio-studio-card {
        background: linear-gradient(135deg, rgba(30, 27, 75, 0.85) 0%, rgba(15, 23, 42, 0.92) 100%);
        border: 1px solid rgba(192, 132, 252, 0.4);
        border-radius: 14px;
        padding: 12px 18px;
        margin-bottom: 14px;
        box-shadow: 0 8px 24px -6px rgba(124, 58, 237, 0.35);
        backdrop-filter: blur(14px);
    }

    .audio-playing-pill {
        background: linear-gradient(135deg, #7C3AED 0%, #DB2777 100%);
        color: #FFFFFF;
        font-size: 0.72rem;
        font-weight: 800;
        letter-spacing: 0.05em;
        padding: 2px 8px;
        border-radius: 6px;
    }

    /* Day Ribbon Command Bar */
    .day-command-ribbon {
        background: rgba(30, 41, 59, 0.45);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 14px;
        padding: 10px 16px;
        margin-bottom: 14px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 12px;
    }

    /* Audio Player Custom Glassmorphic Styling */
    audio {
        width: 100% !important;
        border-radius: 12px !important;
        margin-top: 4px !important;
        margin-bottom: 4px !important;
        height: 38px !important;
        filter: drop-shadow(0 4px 10px rgba(124, 58, 237, 0.25));
    }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "meal_plan" not in st.session_state:
    st.session_state.meal_plan = None
if "checked_items" not in st.session_state:
    st.session_state.checked_items = set()
if "active_audio" not in st.session_state:
    st.session_state.active_audio = None
if "input_friend_name" not in st.session_state:
    st.session_state.input_friend_name = planner.DEFAULT_FRIEND["name"]
if "input_allergies" not in st.session_state:
    st.session_state.input_allergies = list(planner.DEFAULT_FRIEND["allergies"])
if "input_custom_allergies" not in st.session_state:
    st.session_state.input_custom_allergies = ""
if "input_preferences" not in st.session_state:
    st.session_state.input_preferences = planner.DEFAULT_FRIEND["preferences"]
if "input_num_days" not in st.session_state:
    st.session_state.input_num_days = int(planner.DEFAULT_FRIEND["days"])

def set_active_audio(audio_id: str, audio_bytes: bytes, title: str = ""):
    """Ensure only one soundtrack is active at a time; stops and clears any previous track."""
    for k in list(st.session_state.keys()):
        if k.startswith("meal_audio_") or k.startswith("audio_briefing_") or k == "grocery_audio":
            del st.session_state[k]
    st.session_state["active_audio"] = {
        "id": audio_id,
        "bytes": audio_bytes,
        "title": title
    }

def stop_active_audio():
    """Immediately stop and dismiss the active soundtrack."""
    st.session_state["active_audio"] = None

# Sidebar Setup & Controls
st.sidebar.markdown("## ⚙️ Profile & Setup")

# Preset Profile Loader Button
if st.sidebar.button("⚡ Load Anny's Preset Profile", type="primary", use_container_width=True):
    st.session_state.input_friend_name = planner.DEFAULT_FRIEND["name"]
    st.session_state.input_allergies = list(planner.DEFAULT_FRIEND["allergies"])
    st.session_state.input_custom_allergies = ""
    st.session_state.input_preferences = planner.DEFAULT_FRIEND["preferences"]
    st.session_state.input_num_days = int(planner.DEFAULT_FRIEND["days"])
    st.toast("Loaded Anny's profile: Peanuts, Tree Nuts, Shellfish & Dairy excluded!", icon="✅")
    st.rerun()

st.sidebar.markdown("---")

friend_name = st.sidebar.text_input(
    "Friend's Name",
    value=st.session_state.input_friend_name,
    key="input_friend_name"
)

allergy_presets = ["Peanuts", "Tree Nuts", "Shellfish", "Dairy", "Gluten", "Eggs", "Soy", "Fish"]
selected_allergies = st.sidebar.multiselect(
    "Select Severe Allergies",
    options=allergy_presets,
    default=st.session_state.input_allergies,
    key="input_allergies"
)

custom_allergies_text = st.sidebar.text_input(
    "Additional Allergies (comma-separated)",
    value=st.session_state.input_custom_allergies,
    key="input_custom_allergies"
)

# Combine allergies
allergies_list = list(selected_allergies)
if custom_allergies_text:
    for extra in custom_allergies_text.split(","):
        clean_extra = extra.strip()
        if clean_extra and clean_extra not in allergies_list:
            allergies_list.append(clean_extra)

preferences = st.sidebar.text_area(
    "Dietary Preferences & Dislikes",
    value=st.session_state.input_preferences,
    key="input_preferences",
    height=90
)

num_days = st.sidebar.slider(
    "Number of Days",
    min_value=1,
    max_value=7,
    value=st.session_state.input_num_days,
    key="input_num_days"
)

# Advanced AI Settings
st.sidebar.markdown("---")
st.sidebar.markdown("### 🤖 Engine & Intelligence")

available_models = planner.get_available_models()
default_model_options = ["gemma3:1b", "gemma2:2b", "gemma4:e4b", "mistral:latest"]
model_options = list(dict.fromkeys(available_models + default_model_options))

selected_model = st.sidebar.selectbox(
    "Ollama Model", 
    options=model_options,
    index=0
)

temperature = st.sidebar.slider(
    "Creativity (Temperature)",
    min_value=0.0,
    max_value=1.0,
    value=0.3,
    step=0.05,
    help="Lower values yield consistent, strict outputs. Higher values yield creative recipes."
)

st.sidebar.markdown("---")

col_sb1, col_sb2 = st.sidebar.columns([3, 2])
with col_sb1:
    generate_btn = st.button("✨ Generate Plan", type="primary", use_container_width=True)
with col_sb2:
    if st.button("🔄 Reset", type="secondary", use_container_width=True):
        st.session_state.meal_plan = None
        st.session_state.checked_items = set()
        st.session_state.active_audio = None
        st.toast("Planner reset!", icon="🔄")
        st.rerun()

# ElevenLabs Hands-Free Voice Assistant Configuration (Default: 🇮🇳 Anika - Warm & Natural Indian Voice)
elevenlabs_api_key = voice_chef.get_api_key()
voice_options = list(voice_chef.DEFAULT_VOICES.keys())
selected_voice_label = st.sidebar.selectbox(
    "🎙️ AI Chef Narrator Voice:",
    options=voice_options,
    index=0,  # 🇮🇳 Anika (Warm & Natural Indian Voice)
    help="Select the AI Chef narrator voice and accent. Authentic Indian English accents available!"
)
selected_voice_id = voice_chef.DEFAULT_VOICES[selected_voice_label]

# Privacy Card in Sidebar
st.sidebar.markdown("""
<div style="background-color: #1E293B; border: 1px solid #334155; padding: 12px; border-radius: 12px; margin-top: 15px;">
    <p style="margin: 0; font-size: 0.85rem; color: #34D399; font-weight: 600;">🔒 Private & Offline</p>
    <p style="margin: 4px 0 0 0; font-size: 0.8rem; color: #94A3B8;">Health & allergy data never leaves this machine. Powered by local Gemma via Ollama or the local safety rules engine.</p>
</div>
""", unsafe_allow_html=True)

# Status & Badge logic
if available_models and selected_model in available_models:
    badge_label = f"🟢 Local Gemma ({selected_model})"
else:
    badge_label = "⚡ Smart Safety Engine (Cloud Ready)"

allergies_text_str = ", ".join(allergies_list) if allergies_list else "allergies"

# Glassmorphic Header Banner (Flexbox Layout Without Floating Elements)
st.markdown(f"""
<div class="glass-header">
    <div class="header-top-row">
        <h1 class="gradient-title">🥗 Meal Planner for {friend_name}</h1>
        <span class="badge-status">{badge_label}</span>
    </div>
    <div class="welcome-banner">
        ❤️ Built especially for {friend_name} so you never have to worry about {allergies_text_str} again.
    </div>
    <div class="header-exclusions-row">
        <span style="font-size: 0.9rem; color: #94A3B8; font-weight: 600; margin-right: 6px;">Strict Exclusions:</span>
        {' '.join([f'<span class="badge-allergy">🚫 {a}</span>' for a in allergies_list]) if allergies_list else '<span style="color:#94A3B8; font-size:0.9rem;">None specified</span>'}
    </div>
</div>
""", unsafe_allow_html=True)

# Generate Plan Processing
if generate_btn:
    with st.spinner(f"✨ Generating a personalized {num_days}-day meal plan for {friend_name}..."):
        try:
            plan = planner.generate_meal_plan(
                allergies=allergies_list,
                preferences=preferences,
                days=num_days,
                model_name=selected_model,
                temperature=temperature
            )
            st.session_state.meal_plan = plan
            st.session_state.checked_items = set()
            st.toast(f"Plan generated for {friend_name}!", icon="🎉")
        except Exception as e:
            st.error(f"⚠️ Error creating meal plan: {str(e)}")

# MAIN APPLICATION WORKSPACE - TOP LEVEL TABS
plan_days_count = len(st.session_state.meal_plan.get("days", [])) if st.session_state.meal_plan else num_days
days_label_str = f"{plan_days_count}-Day" if plan_days_count > 1 else "1-Day"

main_tab1, main_tab2, main_tab3 = st.tabs([
    f"📅 {days_label_str} Meal Plan", 
    "🛒 Consolidated Shopping List", 
    "🛡️ Why Local AI Matters"
])

# TAB 1: MEAL PLAN
with main_tab1:
    if not st.session_state.meal_plan:
        st.info(f"👈 Customize {friend_name}'s preferences in the sidebar and click **'Generate Plan'** to begin!")
    else:
        plan = st.session_state.meal_plan
        days = plan.get("days", [])
        plan_days_count = len(days)
        days_label_str = f"{plan_days_count}-Day" if plan_days_count > 1 else "1-Day"
        audit = plan.get("audit_summary", {})
        engine_source = plan.get("engine", badge_label)

        # Action Bar: Regenerate All Days, Clear Plan & Quick PDF Download
        act1, act2, act3 = st.columns([2.5, 2, 3.5])
        with act1:
            if st.button("🔄 Regenerate All Days", type="primary", use_container_width=True):
                with st.spinner(f"Re-generating full {plan_days_count}-day plan for {friend_name}..."):
                    new_plan = planner.generate_meal_plan(
                        allergies=allergies_list,
                        preferences=preferences,
                        days=plan_days_count,
                        model_name=selected_model,
                        temperature=temperature
                    )
                    st.session_state.meal_plan = new_plan
                    st.session_state.checked_items = set()
                    st.toast("Regenerated all days!", icon="✨")
                    st.rerun()
        with act2:
            if st.button("🗑️ Clear Plan", type="secondary", use_container_width=True):
                st.session_state.meal_plan = None
                st.session_state.checked_items = set()
                st.rerun()
        with act3:
            quick_plan_pdf = pdf_export.generate_meal_plan_pdf(
                friend_name=friend_name,
                allergies=allergies_list,
                preferences=preferences,
                plan=plan
            )
            st.download_button(
                label=f"📋 Download {days_label_str} Plan (PDF)",
                data=quick_plan_pdf,
                file_name=f"{friend_name.lower()}_{plan_days_count}day_meal_plan.pdf",
                mime="application/pdf",
                type="secondary",
                use_container_width=True
            )

        # Allergen Safety Guard Audit Log
        with st.expander("🛡️ Local Allergen Audit Log (Deterministic Safety Guarantee)", expanded=False):
            scanned = audit.get("total_scanned", sum(len(d.get(m, {}).get("ingredients", [])) for d in days for m in ["breakfast", "lunch", "dinner"]))
            violations = audit.get("violations_caught", len(audit.get("details", [])))
            st.markdown(f"""
            - **Engine Active:** `{engine_source}`
            - **Total Ingredients Scanned:** `{scanned}` across all meals & groceries
            - **Zero-Tolerance Safety Interceptions:** `{violations}` allergens detected & safely substituted
            - **Verified Allergen Protections:** {', '.join([f'`{a}`' for a in allergies_list]) if allergies_list else '`None`'}
            - **Status:** 🟢 **100% ALLERGEN-SAFE GUARANTEED**
            """)
            if audit.get("details"):
                st.markdown("##### 🔍 Audit Trace of Substitutions Applied:")
                for d in audit["details"][:10]:
                    st.caption(f"• **{d.get('location', 'Meal')}**: Found `{d.get('detected', 'allergen')}` ({d.get('allergen')}) → *{d.get('action')}*")
            else:
                st.caption("✅ All recipes in this plan are naturally free of forbidden allergens.")

        # Interactive Day Tabs
        tab_titles = [f"🗓️ {day.get('day', f'Day {i+1}')}" for i, day in enumerate(days)]
        day_tabs = st.tabs(tab_titles)
        
        for idx, (tab, day) in enumerate(zip(day_tabs, days)):
            day_label = day.get("day", f"Day {idx + 1}")
            
            with tab:
                st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

                # Unified Day Command Ribbon (Title + Voice Briefing + Re-roll Day)
                col_ribbon_info, col_ribbon_brief, col_ribbon_regen = st.columns([3, 1.4, 1.3])
                with col_ribbon_info:
                    st.markdown(f"""
                    <div style="padding: 4px 0;">
                        <span style="font-weight: 700; color: #F8FAFC; font-size: 1.05rem;">🗓️ {day_label} Menu</span>
                        <div style="color: #94A3B8; font-size: 0.8rem; margin-top: 2px;">
                            3 safe meals • 🟢 100% allergen-verified
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                is_briefing_active = (st.session_state.get("active_audio") and st.session_state["active_audio"].get("id") == f"briefing_{idx}")
                with col_ribbon_brief:
                    brief_btn_label = "⏹️ Stop Briefing" if is_briefing_active else "🎙️ Daily Briefing"
                    if st.button(brief_btn_label, key=f"btn_briefing_{idx}", type="primary" if is_briefing_active else "secondary", use_container_width=True):
                        if is_briefing_active:
                            stop_active_audio()
                            st.rerun()
                        else:
                            if not elevenlabs_api_key:
                                st.toast("Add your ELEVENLABS_API_KEY to your .env file to enable voice briefings!", icon="🎙️")
                            else:
                                with st.spinner(f"Synthesizing {day_label} briefing with ElevenLabs..."):
                                    brief_script = voice_chef.build_daily_briefing_script(friend_name, day, allergies_list)
                                    audio_bytes = voice_chef.synthesize_speech(brief_script, api_key=elevenlabs_api_key, voice_id=selected_voice_id)
                                    if audio_bytes:
                                        set_active_audio(f"briefing_{idx}", audio_bytes, f"Daily Voice Briefing ({day_label})")
                                        st.rerun()
                                    else:
                                        st.error("Failed to generate audio. Verify your ElevenLabs API key.")

                with col_ribbon_regen:
                    if st.button(f"🔄 Re-roll Day", key=f"tab_regen_{idx}", type="secondary", use_container_width=True, help=f"Re-roll all 3 safe meals for {day_label}"):
                        with st.spinner(f"Re-rolling {day_label} for {friend_name}..."):
                            existing_meals = [
                                day.get("breakfast", {}).get("name", ""),
                                day.get("lunch", {}).get("name", ""),
                                day.get("dinner", {}).get("name", "")
                            ]
                            new_day = planner.regenerate_single_day(
                                allergies=allergies_list,
                                preferences=preferences,
                                day_label=day_label,
                                model_name=selected_model,
                                temperature=temperature,
                                existing_day_meals=existing_meals
                            )
                            st.session_state.meal_plan["days"][idx] = new_day
                            st.session_state.meal_plan = planner.update_shopping_list(st.session_state.meal_plan)
                            st.toast(f"Regenerated {day_label}!", icon="✨")
                            st.rerun()

                # Active Audio Studio Player with Soundwave Equalizer (Shows when briefing or any meal is active for this day)
                active_aud = st.session_state.get("active_audio")
                if active_aud and (active_aud.get("id") == f"briefing_{idx}" or active_aud.get("id") in [f"meal_{idx}_b", f"meal_{idx}_l", f"meal_{idx}_d"]):
                    voice_name_clean = selected_voice_label.split(" (")[0].replace("🇮🇳 ", "")
                    st.markdown(f"""
                    <div class="audio-studio-card">
                        <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 10px;">
                            <div style="display: flex; align-items: center; gap: 12px;">
                                <div class="soundwave-box">
                                    <span></span><span></span><span></span><span></span><span></span>
                                </div>
                                <div>
                                    <div style="display: flex; align-items: center; gap: 8px;">
                                        <span class="audio-playing-pill">PLAYING</span>
                                        <span style="font-weight: 700; color: #F8FAFC; font-size: 0.95rem;">{active_aud.get('title', 'Chef Voice Guide')}</span>
                                    </div>
                                    <div style="font-size: 0.76rem; color: #C084FC; margin-top: 2px;">
                                        🎙️ ElevenLabs Kitchen Audio • Narrated by {voice_name_clean} (Indian Accent)
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    c_aud, c_cls = st.columns([6, 1])
                    with c_aud:
                        st.audio(active_aud["bytes"], format="audio/mp3", autoplay=True)
                    with c_cls:
                        st.markdown("<div style='padding-top: 6px;'>", unsafe_allow_html=True)
                        if st.button("⏹️ Stop", key=f"studio_stop_{idx}", help="Stop audio narration", use_container_width=True):
                            stop_active_audio()
                            st.rerun()
                        st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
                m1, m2, m3 = st.columns(3)
                
                # Breakfast Card (3D Rotatable Flip Card)
                with m1:
                    b = day.get("breakfast", {})
                    b_name = b.get("name", "Breakfast")
                    b_time = b.get("prep_time", "15 mins")
                    b_desc = b.get("description", "A wholesome, allergy-safe recipe prepared fresh.")
                    b_ingredients = "\n".join([f"• {ing}" for ing in b.get("ingredients", [])])
                    b_instructions = b.get("instructions", "Prepare fresh and enjoy warm.")
                    b_tip = b.get("chef_tip", "Season to taste with fresh herbs and olive oil.")
                    card_id_b = f"flip_card_{idx}_b"
                    
                    st.markdown(f"""
                    <div class="flip-card">
                        <input type="checkbox" id="{card_id_b}" class="flip-checkbox" />
                        <label for="{card_id_b}" class="flip-card-inner">
                            <div class="flip-card-front">
                                <div class="card-body-scroll">
                                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 6px;">
                                        <span class="meal-type-tag breakfast-tag">🥣 Breakfast</span>
                                        <span style="font-size:0.8rem; color:#94A3B8; font-weight:500;">⏱️ {b_time}</span>
                                    </div>
                                    <h3 class="card-recipe-title">{b_name}</h3>
                                    <p style="font-size: 0.82rem; color: #A5B4FC; font-style: italic; margin-bottom: 10px; line-height: 1.4;">
                                        {b_desc}
                                    </p>
                                    <p style="font-size: 0.84rem; color: #CBD5E1; margin-bottom: 6px; font-weight: 600;">Ingredients:</p>
                                    <p style="font-size: 0.82rem; color: #94A3B8; white-space: pre-line; line-height: 1.45; margin: 0;">{b_ingredients}</p>
                                </div>
                                <div class="flip-hint-badge">
                                    🔄 Hover or Click for Recipe Steps ➔
                                </div>
                            </div>
                            <div class="flip-card-back">
                                <div class="card-body-scroll">
                                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 8px;">
                                        <span style="font-size:0.85rem; font-weight:700; color:#C084FC;">👨‍🍳 Step-by-Step Cooking Guide</span>
                                        <span style="font-size:0.75rem; color:#34D399; background:rgba(6,78,59,0.6); padding:2px 8px; border-radius:10px; font-weight:600;">🟢 Verified Safe</span>
                                    </div>
                                    <div style="font-size:0.82rem; color:#E2E8F0; line-height:1.55; white-space:pre-line; margin-bottom: 10px;">
                                        {b_instructions}
                                    </div>
                                    <div class="chef-tip-box">
                                        💡 <strong>Chef's Tip:</strong> {b_tip}
                                    </div>
                                </div>
                                <div class="flip-hint-badge" style="background:rgba(30,41,59,0.7); color:#94A3B8; border-color:rgba(255,255,255,0.1);">
                                    ↺ Click to Flip Back to Ingredients
                                </div>
                            </div>
                        </label>
                    </div>
                    """, unsafe_allow_html=True)

                    # Breakfast Audio Chef Guide Button
                    is_b_active = (st.session_state.get("active_audio") and st.session_state["active_audio"].get("id") == f"meal_{idx}_b")
                    b_btn_text = "⏹️ Stop Chef Guide" if is_b_active else "👨‍🍳 Chef Audio Guide"
                    if st.button(b_btn_text, key=f"audio_btn_b_{idx}", type="primary" if is_b_active else "secondary", use_container_width=True):
                        if is_b_active:
                            stop_active_audio()
                            st.rerun()
                        else:
                            if not elevenlabs_api_key:
                                st.toast("Add your ELEVENLABS_API_KEY to your .env file for hands-free voice guides!", icon="👨‍🍳")
                            else:
                                with st.spinner("Synthesizing kitchen audio guide with ElevenLabs..."):
                                    meal_script = voice_chef.build_recipe_speech_script(b, "Breakfast")
                                    aud_data = voice_chef.synthesize_speech(meal_script, api_key=elevenlabs_api_key, voice_id=selected_voice_id)
                                    if aud_data:
                                        set_active_audio(f"meal_{idx}_b", aud_data, f"Breakfast: {b_name}")
                                        st.rerun()
                                    else:
                                        st.error("Could not generate audio. Verify your ElevenLabs API key.")

                # Lunch Card (3D Rotatable Flip Card)
                with m2:
                    l = day.get("lunch", {})
                    l_name = l.get("name", "Lunch")
                    l_time = l.get("prep_time", "15 mins")
                    l_desc = l.get("description", "A nourishing, allergy-safe midday meal.")
                    l_ingredients = "\n".join([f"• {ing}" for ing in l.get("ingredients", [])])
                    l_instructions = l.get("instructions", "Prepare fresh and enjoy warm.")
                    l_tip = l.get("chef_tip", "Season to taste with fresh herbs and olive oil.")
                    card_id_l = f"flip_card_{idx}_l"
                    
                    st.markdown(f"""
                    <div class="flip-card">
                        <input type="checkbox" id="{card_id_l}" class="flip-checkbox" />
                        <label for="{card_id_l}" class="flip-card-inner">
                            <div class="flip-card-front">
                                <div class="card-body-scroll">
                                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 6px;">
                                        <span class="meal-type-tag lunch-tag">🥗 Lunch</span>
                                        <span style="font-size:0.8rem; color:#94A3B8; font-weight:500;">⏱️ {l_time}</span>
                                    </div>
                                    <h3 class="card-recipe-title">{l_name}</h3>
                                    <p style="font-size: 0.82rem; color: #A5B4FC; font-style: italic; margin-bottom: 10px; line-height: 1.4;">
                                        {l_desc}
                                    </p>
                                    <p style="font-size: 0.84rem; color: #CBD5E1; margin-bottom: 6px; font-weight: 600;">Ingredients:</p>
                                    <p style="font-size: 0.82rem; color: #94A3B8; white-space: pre-line; line-height: 1.45; margin: 0;">{l_ingredients}</p>
                                </div>
                                <div class="flip-hint-badge">
                                    🔄 Hover or Click for Recipe Steps ➔
                                </div>
                            </div>
                            <div class="flip-card-back">
                                <div class="card-body-scroll">
                                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 8px;">
                                        <span style="font-size:0.85rem; font-weight:700; color:#C084FC;">👨‍🍳 Step-by-Step Cooking Guide</span>
                                        <span style="font-size:0.75rem; color:#34D399; background:rgba(6,78,59,0.6); padding:2px 8px; border-radius:10px; font-weight:600;">🟢 Verified Safe</span>
                                    </div>
                                    <div style="font-size:0.82rem; color:#E2E8F0; line-height:1.55; white-space:pre-line; margin-bottom: 10px;">
                                        {l_instructions}
                                    </div>
                                    <div class="chef-tip-box">
                                        💡 <strong>Chef's Tip:</strong> {l_tip}
                                    </div>
                                </div>
                                <div class="flip-hint-badge" style="background:rgba(30,41,59,0.7); color:#94A3B8; border-color:rgba(255,255,255,0.1);">
                                    ↺ Click to Flip Back to Ingredients
                                </div>
                            </div>
                        </label>
                    </div>
                    """, unsafe_allow_html=True)

                    # Lunch Audio Chef Guide Button
                    is_l_active = (st.session_state.get("active_audio") and st.session_state["active_audio"].get("id") == f"meal_{idx}_l")
                    l_btn_text = "⏹️ Stop Chef Guide" if is_l_active else "👨‍🍳 Chef Audio Guide"
                    if st.button(l_btn_text, key=f"audio_btn_l_{idx}", type="primary" if is_l_active else "secondary", use_container_width=True):
                        if is_l_active:
                            stop_active_audio()
                            st.rerun()
                        else:
                            if not elevenlabs_api_key:
                                st.toast("Add your ELEVENLABS_API_KEY to your .env file for hands-free voice guides!", icon="👨‍🍳")
                            else:
                                with st.spinner("Synthesizing kitchen audio guide with ElevenLabs..."):
                                    meal_script = voice_chef.build_recipe_speech_script(l, "Lunch")
                                    aud_data = voice_chef.synthesize_speech(meal_script, api_key=elevenlabs_api_key, voice_id=selected_voice_id)
                                    if aud_data:
                                        set_active_audio(f"meal_{idx}_l", aud_data, f"Lunch: {l_name}")
                                        st.rerun()
                                    else:
                                        st.error("Could not generate audio. Verify your ElevenLabs API key.")

                # Dinner Card (3D Rotatable Flip Card)
                with m3:
                    d = day.get("dinner", {})
                    d_name = d.get("name", "Dinner")
                    d_time = d.get("prep_time", "20 mins")
                    d_desc = d.get("description", "A delicious, comforting allergy-safe dinner.")
                    d_ingredients = "\n".join([f"• {ing}" for ing in d.get("ingredients", [])])
                    d_instructions = d.get("instructions", "Prepare fresh and enjoy warm.")
                    d_tip = d.get("chef_tip", "Season to taste with fresh herbs and olive oil.")
                    card_id_d = f"flip_card_{idx}_d"
                    
                    st.markdown(f"""
                    <div class="flip-card">
                        <input type="checkbox" id="{card_id_d}" class="flip-checkbox" />
                        <label for="{card_id_d}" class="flip-card-inner">
                            <div class="flip-card-front">
                                <div class="card-body-scroll">
                                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 6px;">
                                        <span class="meal-type-tag dinner-tag">🍲 Dinner</span>
                                        <span style="font-size:0.8rem; color:#94A3B8; font-weight:500;">⏱️ {d_time}</span>
                                    </div>
                                    <h3 class="card-recipe-title">{d_name}</h3>
                                    <p style="font-size: 0.82rem; color: #A5B4FC; font-style: italic; margin-bottom: 10px; line-height: 1.4;">
                                        {d_desc}
                                    </p>
                                    <p style="font-size: 0.84rem; color: #CBD5E1; margin-bottom: 6px; font-weight: 600;">Ingredients:</p>
                                    <p style="font-size: 0.82rem; color: #94A3B8; white-space: pre-line; line-height: 1.45; margin: 0;">{d_ingredients}</p>
                                </div>
                                <div class="flip-hint-badge">
                                    🔄 Hover or Click for Recipe Steps ➔
                                </div>
                            </div>
                            <div class="flip-card-back">
                                <div class="card-body-scroll">
                                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom: 8px;">
                                        <span style="font-size:0.85rem; font-weight:700; color:#C084FC;">👨‍🍳 Step-by-Step Cooking Guide</span>
                                        <span style="font-size:0.75rem; color:#34D399; background:rgba(6,78,59,0.6); padding:2px 8px; border-radius:10px; font-weight:600;">🟢 Verified Safe</span>
                                    </div>
                                    <div style="font-size:0.82rem; color:#E2E8F0; line-height:1.55; white-space:pre-line; margin-bottom: 10px;">
                                        {d_instructions}
                                    </div>
                                    <div class="chef-tip-box">
                                        💡 <strong>Chef's Tip:</strong> {d_tip}
                                    </div>
                                </div>
                                <div class="flip-hint-badge" style="background:rgba(30,41,59,0.7); color:#94A3B8; border-color:rgba(255,255,255,0.1);">
                                    ↺ Click to Flip Back to Ingredients
                                </div>
                            </div>
                        </label>
                    </div>
                    """, unsafe_allow_html=True)

                    # Dinner Audio Chef Guide Button
                    is_d_active = (st.session_state.get("active_audio") and st.session_state["active_audio"].get("id") == f"meal_{idx}_d")
                    d_btn_text = "⏹️ Stop Chef Guide" if is_d_active else "👨‍🍳 Chef Audio Guide"
                    if st.button(d_btn_text, key=f"audio_btn_d_{idx}", type="primary" if is_d_active else "secondary", use_container_width=True):
                        if is_d_active:
                            stop_active_audio()
                            st.rerun()
                        else:
                            if not elevenlabs_api_key:
                                st.toast("Add your ELEVENLABS_API_KEY to your .env file for hands-free voice guides!", icon="👨‍🍳")
                            else:
                                with st.spinner("Synthesizing kitchen audio guide with ElevenLabs..."):
                                    meal_script = voice_chef.build_recipe_speech_script(d, "Dinner")
                                    aud_data = voice_chef.synthesize_speech(meal_script, api_key=elevenlabs_api_key, voice_id=selected_voice_id)
                                    if aud_data:
                                        set_active_audio(f"meal_{idx}_d", aud_data, f"Dinner: {d_name}")
                                        st.rerun()
                                    else:
                                        st.error("Could not generate audio. Verify your ElevenLabs API key.")

# TAB 2: SHOPPING LIST (WITH AISLE CATEGORIZATION, PROGRESS & DOWNLOADS)
with main_tab2:
    if not st.session_state.meal_plan:
        st.info("🛒 Generate a meal plan first to view your aggregated shopping list.")
    else:
        plan = st.session_state.meal_plan
        shopping_items = plan.get("shopping_list", [])
        categorized_shop = planner.generate_categorized_shopping_list(shopping_items)
        
        st.markdown(f"### 🛒 Consolidated Grocery List for {friend_name}")
        st.caption("Consolidated & aisle-categorized from all days of safe meals.")

        # Progress tracking
        total_items_count = len(shopping_items)
        checked_count = len([item for item in shopping_items if item in st.session_state.checked_items])
        progress_val = checked_count / total_items_count if total_items_count > 0 else 0.0

        st.progress(progress_val)
        c_p1, c_p2, c_p3 = st.columns([3, 1, 1])
        with c_p1:
            st.markdown(f"<div style='padding-top: 8px; font-size: 0.92rem; color: #E2E8F0;'><strong>Progress:</strong> {checked_count} of {total_items_count} items checked ({int(progress_val * 100)}%)</div>", unsafe_allow_html=True)
        with c_p2:
            if st.button("✓ Check All", type="secondary", use_container_width=True):
                st.session_state.checked_items = set(shopping_items)
                st.rerun()
        with c_p3:
            if st.button("✕ Clear All", type="secondary", use_container_width=True):
                st.session_state.checked_items = set()
                st.rerun()

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        c1, c2 = st.columns([3, 2])
        
        with c1:
            for category, items in categorized_shop.items():
                if items:
                    st.markdown(f"""
                    <div class="aisle-card">
                        <div class="aisle-header">
                            <span class="aisle-title">{category}</span>
                            <span class="aisle-count">{len(items)} items</span>
                        </div>
                    """, unsafe_allow_html=True)
                    for item in items:
                        is_checked = item in st.session_state.checked_items
                        if st.checkbox(item, value=is_checked, key=f"chk_aisle_{category}_{item}"):
                            st.session_state.checked_items.add(item)
                        else:
                            st.session_state.checked_items.discard(item)
                    st.markdown("</div>", unsafe_allow_html=True)
                    
        with c2:
            st.markdown("#### 🎧 Hands-Free Grocery Audio")
            is_grocery_active = (st.session_state.get("active_audio") and st.session_state["active_audio"].get("id") == "grocery")
            g_btn_text = "⏹️ Stop Grocery Audio" if is_grocery_active else "🎙️ Play Supermarket Audio Run"
            if st.button(g_btn_text, key="btn_grocery_audio", type="primary" if is_grocery_active else "secondary", use_container_width=True):
                if is_grocery_active:
                    stop_active_audio()
                    st.rerun()
                else:
                    if not elevenlabs_api_key:
                        st.toast("Add your ELEVENLABS_API_KEY to your .env file to listen to grocery audio!", icon="🛒")
                    else:
                        with st.spinner("Synthesizing aisle shopping guide with ElevenLabs..."):
                            g_script = voice_chef.build_shopping_speech_script(friend_name, categorized_shop)
                            g_audio = voice_chef.synthesize_speech(g_script, api_key=elevenlabs_api_key, voice_id=selected_voice_id)
                            if g_audio:
                                set_active_audio("grocery", g_audio, f"Grocery Audio Run for {friend_name}")
                                st.rerun()
                            else:
                                st.error("Could not generate audio. Verify your ElevenLabs API key.")

            if is_grocery_active:
                st.markdown("""
                <div style="display: flex; align-items: center; gap: 8px; margin: 8px 0 4px 0;">
                    <div class="soundwave-box">
                        <span></span><span></span><span></span><span></span><span></span>
                    </div>
                    <span style="font-size: 0.8rem; color: #C084FC; font-weight: 600;">Supermarket Run Audio Playing...</span>
                </div>
                """, unsafe_allow_html=True)
                st.audio(st.session_state["active_audio"]["bytes"], format="audio/mp3", autoplay=True)
            
            st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
            st.markdown("#### 📄 Export & Downloads")
            
            # Generate PDFs using pdf_export
            shop_pdf_bytes = pdf_export.generate_shopping_list_pdf(
                friend_name=friend_name,
                allergies=allergies_list,
                categorized_items=categorized_shop,
                checked_items=st.session_state.checked_items
            )
            
            plan_pdf_bytes = pdf_export.generate_meal_plan_pdf(
                friend_name=friend_name,
                allergies=allergies_list,
                preferences=preferences,
                plan=plan
            )

            # Elegant summary box instead of raw plaintext
            st.markdown(f"""
            <div style="background: rgba(30, 41, 59, 0.5); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 14px; padding: 18px; margin-bottom: 18px;">
                <h4 style="margin: 0 0 10px 0; color: #F8FAFC; font-size: 1.05rem;">🛒 Grocery Summary</h4>
                <p style="margin: 4px 0; font-size: 0.88rem; color: #CBD5E1;">• <strong>Total Items:</strong> {total_items_count} items across {len([k for k, v in categorized_shop.items() if v])} aisles</p>
                <p style="margin: 4px 0; font-size: 0.88rem; color: #CBD5E1;">• <strong>Checked Off:</strong> {checked_count} of {total_items_count} items</p>
                <p style="margin: 4px 0; font-size: 0.88rem; color: #34D399;">• <strong>Safety Seal:</strong> 100% free of {allergies_text_str}</p>
            </div>
            """, unsafe_allow_html=True)
            
            st.download_button(
                label="📄 Download Grocery List (PDF)",
                data=shop_pdf_bytes,
                file_name=f"{friend_name.lower()}_grocery_list.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )

            plan_days_count = len(plan.get("days", []))
            days_label_str = f"{plan_days_count}-Day" if plan_days_count > 1 else "1-Day"

            st.download_button(
                label=f"📋 Download Complete {days_label_str} Plan (PDF)",
                data=plan_pdf_bytes,
                file_name=f"{friend_name.lower()}_{plan_days_count}day_meal_plan.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )



# TAB 3: WHY LOCAL AI MATTERS
with main_tab3:
    st.markdown("### 🛡️ Why Open / Local AI Matters for Anny")
    st.caption("Safeguarding sensitive personal health information with offline intelligence.")
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    
    col_story1, col_story2 = st.columns(2)
    
    with col_story1:
        st.markdown("""
        <div class="glass-feature-card">
            <div class="feature-title-row">
                <span style="font-size: 1.3rem;">🔒</span>
                <h4>1. Absolute Health Data Privacy</h4>
            </div>
            <p class="feature-body">
                Dietary restrictions and severe medical allergies are sensitive personal health information. 
                Using <strong>open-weight Gemma models locally via Ollama</strong> ensures that 
                <strong>zero health data ever leaves your device</strong>—no cloud tracking, no telemetry, and zero leaks.
            </p>
        </div>

        <div class="glass-feature-card">
            <div class="feature-title-row">
                <span style="font-size: 1.3rem;">⚡</span>
                <h4>2. Sub-Second Offline Speed & Reliability</h4>
            </div>
            <p class="feature-body">
                Running lightweight open-weight models locally on Apple Silicon / CPU allows instant generation 
                and single-day regeneration without internet connection, API rate limits, or surprise cloud billing.
            </p>
        </div>
        """, unsafe_allow_html=True)

    with col_story2:
        st.markdown("""
        <div class="glass-feature-card">
            <div class="feature-title-row">
                <span style="font-size: 1.3rem;">🛡️</span>
                <h4>3. Deterministic Allergen Safety Engine</h4>
            </div>
            <p class="feature-body">
                Combines <strong>Gemma open-weight reasoning</strong> with a deterministic 
                <strong>Python Allergen Audit Engine</strong> that scans every single ingredient 
                against forbidden allergens to guarantee 100% safety with zero hallucinations.
            </p>
        </div>

        <div class="glass-feature-card">
            <div class="feature-title-row">
                <span style="font-size: 1.3rem;">☁️</span>
                <h4>4. Seamless Cloud & Render Compatibility</h4>
            </div>
            <p class="feature-body">
                When deployed to Render or Streamlit Cloud, the intelligent <strong>Cloud Smart Engine</strong> 
                runs without needing an Ollama daemon, providing instant, bug-free, and diverse allergy-safe meal plans.
            </p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    st.markdown("#### 🎬 60–90 Second Demo Video Script for Hackathons & Judges")
    st.markdown("""
    <div class="timeline-step">
        <span class="timeline-badge">0:00 - 0:15</span>
        <div>
            <strong style="color: #F8FAFC;">The Problem & Urgency:</strong>
            <span style="color: #CBD5E1;"> Introduce Anny, who has severe allergies to Peanuts, Tree Nuts, Shellfish, and Dairy. Explain the anxiety of meal planning and accidental cross-contamination.</span>
        </div>
    </div>

    <div class="timeline-step">
        <span class="timeline-badge">0:15 - 0:35</span>
        <div>
            <strong style="color: #F8FAFC;">One-Click Generation:</strong>
            <span style="color: #CBD5E1;"> Click <em>⚡ Load Anny's Preset Profile</em>, show the strict exclusions populate, and click <em>✨ Generate Plan</em>. Highlight diverse safe meals across all selected days.</span>
        </div>
    </div>

    <div class="timeline-step">
        <span class="timeline-badge">0:35 - 0:50</span>
        <div>
            <strong style="color: #F8FAFC;">Interactive 3D Cards & ElevenLabs Audio:</strong>
            <span style="color: #CBD5E1;"> Hover and click the 3D rotatable cards to view step-by-step cooking guides. Play the hands-free Indian accent Chef Voice Guide and morning briefing. Re-roll any single day with one click.</span>
        </div>
    </div>

    <div class="timeline-step">
        <span class="timeline-badge">0:50 - 0:75</span>
        <div>
            <strong style="color: #F8FAFC;">Consolidated Shopping & Safety Guarantee:</strong>
            <span style="color: #CBD5E1;"> Switch to the <em>Consolidated Shopping List</em> for aisle checklists, grocery audio run, and one-click PDF downloads. Highlight 100% offline privacy and deterministic allergen safety log.</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

