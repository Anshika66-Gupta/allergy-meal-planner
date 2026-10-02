# 🥗 Anny's Local Allergy-Safe Meal Planner

> **Help Anny plan safe, tasty meals without constant anxiety about allergies — powered 100% offline by local Gemma.**

---

## 🎯 Overview

Planning meals with severe food allergies can be stressful and anxiety-inducing. **Anny's Local Meal Planner** is a lightweight, offline-first application that generates personalized 7-day meal plans and consolidated shopping lists tailored specifically for Anny's dietary requirements.

### 🔑 Core Features
- **1-Click Anny Profile Preset**: Instantly loads Anny's severe allergies (**Peanuts**, **Tree Nuts**, **Shellfish**, **Dairy**) and preferences (**Gluten-Free Friendly**, **High Protein**, **Quick Prep < 20 mins**).
- **7-Day Safe Meal Plan**: Generates complete Breakfast, Lunch, and Dinner schedules.
- **Consolidated Aisle-Categorized Shopping List**: Aggregates ingredients across all 7 days into Produce, Protein, Dairy Alternatives, Grains, and Pantry aisles with checkable items and `.txt` export.
- **Single-Day & Full-Week Regeneration**: Re-roll any individual day (e.g., Day 3) or regenerate the whole week instantly.
- **Deterministic Allergen Safety Engine**: Combines local Gemma LLM generation with a local Python safety filter that inspects every recipe and automatically replaces any restricted ingredient.
- **100% Offline & Private**: Zero data sent to cloud servers; powered locally via **Ollama** and Google's **Gemma** open-weight models.

---

## 💡 Why Local Open AI Matters for Anny

1. **🔒 Complete Health Data Privacy**: Severe allergy and dietary profile data never leave Anny's computer. No cloud logging or third-party data tracking.
2. **⚡ Sub-Second Offline Speed**: Fast meal plan and single-day generation without internet dependencies or cloud rate limits.
3. **🛡️ Dual-Layer Guardrails**: Pairs Gemma open-weight reasoning with a deterministic local Python allergen filter for absolute safety.
4. **💰 Zero API Costs**: Runs entirely on open-weights without subscription fees or API tokens.

---

## 🛠️ Tech Stack

- **Language**: Python 3.11+
- **Frontend / UI**: Streamlit
- **LLM Engine**: Ollama Python Client (`ollama`) running local **Gemma** (`gemma3:1b`, `gemma2:2b`, etc.)
- **Database / API**: None (100% offline, in-memory state)

---

## 📁 Project Structure

```
allergy-meal-planner/
├── app.py           # Streamlit application UI & interactive state management
├── planner.py       # Core business logic, Gemma prompt templates, & safety engine
├── requirements.txt # Minimal Python dependencies (streamlit, ollama, python-dotenv)
├── .env.example     # Environment configuration template
└── README.md        # Documentation, setup guide & demo script
```

---

## 🚀 Quickstart Guide

### Prerequisites
1. **Python 3.11+** installed.
2. **Ollama** installed and running on your system:
   ```bash
   # Download Ollama from https://ollama.com
   ollama pull gemma3:1b
   ```

### 1. Clone & Environment Setup
```bash
cd allergy-meal-planner

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Configuration (Optional)
```bash
cp .env.example .env
```

### 3. Launch the Application
```bash
streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🎥 60–90 Second Demo Video Script

If you are recording a demo video for Anny or your team, follow this fast flow:

1. **0:00 - 0:15 | Intro & The Problem**: 
   *"This is Anny's Meal Planner. Anny has severe allergies to peanuts, tree nuts, shellfish, and dairy. Planning meals used to cause severe anxiety."*
2. **0:15 - 0:35 | Load Profile & Generate (< 30s)**:
   *"We click 'Load Anny's Preset Profile' to lock in her allergies and gluten-free high-protein preferences. We click 'Generate 7-Day Meal Plan'. In seconds, local Gemma generates 21 safe meals across 7 days."*
3. **0:35 - 0:50 | Regeneration & Shopping List**:
   *"Notice Day 4 dinner? If Anny wants a different option, she can click 'Regenerate Day 4' to get an instant safe replacement. In Tab 2, an aggregated shopping list organizes ingredients into grocery aisles for easy checkout."*
4. **0:50 - 0:75 | Why Local AI Matters & Conclusion**:
   *"Everything runs 100% offline using local Gemma via Ollama. Her health data stays on this laptop, latency is under 30 seconds, and our Python safety audit engine guarantees 100% allergen-free output."*

---

## 🛡️ License

MIT License - Free for personal and community use.
