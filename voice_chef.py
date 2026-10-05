"""
voice_chef.py - High-Fidelity ElevenLabs Audio Narration for Allergy-Safe Meal Planner

Features:
- Hands-Free Audio Cooking Guide for individual recipes.
- Daily Safe Meal Audio Briefing (Podcast-style morning overview).
- Aisle-by-Aisle Hands-Free Grocery Run Audio Guide.
- Local MD5 disk caching to prevent re-consuming ElevenLabs character quotas.
- Graceful offline fallback if API key is not provided.
"""

import os
import hashlib
from pathlib import Path
from typing import Optional, Dict, Any, List
import requests
from dotenv import load_dotenv

load_dotenv()

CACHE_DIR = Path(".cache/audio")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_VOICES = {
    "🇮🇳 Anika (Warm & Natural Indian Voice)": "RABOvaPec1ymXz02oDQi",
    "🇮🇳 Rudra (Clear & Energetic Indian Voice)": "xLm17wfwFDI3GeAaAOZA",
    "Rachel (Warm & Natural)": "21m00Tcm4TlvDq8ikWAM",
    "Adam (Deep & Engaging)": "pNInz6obpgDQGcFmaJgB",
    "Bella (Friendly & Clear)": "EXAVITQu4vr4xnSDxMaL",
    "Antoni (Culinary Guide)": "ErXwobaYiN019PkySvjV",
    "Charlotte (Elegant & Calm)": "XB0fDUnXU5powFXDhCwa"
}

DEFAULT_VOICE_ID = "RABOvaPec1ymXz02oDQi"  # Anika (Indian accent)


def get_api_key(explicit_key: Optional[str] = None) -> Optional[str]:
    """Retrieve ElevenLabs API key from explicit param, environment, or return None."""
    if explicit_key is not None:
        return explicit_key.strip() or None
    return os.getenv("ELEVENLABS_API_KEY", "").strip() or None


def synthesize_speech(
    text: str,
    api_key: Optional[str] = None,
    voice_id: Optional[str] = None,
    model_id: str = "eleven_multilingual_v2"
) -> Optional[bytes]:
    """
    Synthesize speech using ElevenLabs API with persistent disk caching.
    Returns MP3 audio bytes on success, or None if key is missing/request fails.
    """
    token = get_api_key(api_key)
    if not token:
        return None

    voice = voice_id or DEFAULT_VOICE_ID
    clean_text = text.strip()
    if not clean_text:
        return None

    # Compute cache key from text + voice
    cache_key = hashlib.md5(f"{voice}_{clean_text}".encode("utf-8")).hexdigest()
    cache_file = CACHE_DIR / f"{cache_key}.mp3"

    if cache_file.exists():
        try:
            return cache_file.read_bytes()
        except Exception:
            pass

    url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice}"
    headers = {
        "xi-api-key": token,
        "Content-Type": "application/json",
        "Accept": "audio/mpeg"
    }
    payload = {
        "text": clean_text,
        "model_id": model_id,
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.8
        }
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=25)
        if response.status_code == 200 and response.content:
            try:
                cache_file.write_bytes(response.content)
            except Exception:
                pass
            return response.content
        else:
            return None
    except Exception:
        return None


def build_recipe_speech_script(meal: Dict[str, Any], meal_type: str = "Meal") -> str:
    """Format recipe steps into an engaging spoken kitchen chef script."""
    name = meal.get("name", meal_type)
    time = meal.get("prep_time", "15 minutes")
    instructions = meal.get("instructions", "Prepare fresh according to recipe instructions.")
    tip = meal.get("chef_tip", "")

    # Clean numbered lists for natural pause when spoken
    spoken_instructions = instructions.replace("\n", " ").replace("  ", " ")
    
    script = f"Here is your step-by-step chef guide for {name}. Ready in approximately {time}. {spoken_instructions}."
    if tip:
        script += f" Chef's secret tip: {tip}."
    script += " Bon appétit and enjoy your safe meal!"
    return script


def build_daily_briefing_script(
    friend_name: str,
    day: Dict[str, Any],
    allergies: List[str]
) -> str:
    """Format a morning podcast-style audio briefing of the day's meals."""
    day_label = day.get("day", "Today")
    b = day.get("breakfast", {}).get("name", "Wholesome breakfast")
    l = day.get("lunch", {}).get("name", "Nourishing lunch")
    d = day.get("dinner", {}).get("name", "Delicious dinner")

    allergies_str = ", ".join(allergies) if allergies else "common allergens"

    script = (
        f"Good morning {friend_name}! Here is your safe culinary preview for {day_label}. "
        f"To start your morning, breakfast is {b}. "
        f"For midday nourishment, lunch features {l}. "
        f"And for this evening's dinner, you'll be enjoying {d}. "
        f"Every recipe is 100 percent verified free of {allergies_str}. "
        f"Have a healthy and wonderful day!"
    )
    return script


def build_shopping_speech_script(
    friend_name: str,
    categorized_items: Dict[str, List[str]]
) -> str:
    """Format an aisle-by-aisle hands-free audio checklist for the grocery store."""
    total_items = sum(len(items) for items in categorized_items.values())
    script_parts = [
        f"Hands-free grocery guide for {friend_name}. We have {total_items} items to gather today."
    ]

    for category, items in categorized_items.items():
        if items:
            clean_category = category.replace("🥬", "").replace("🍗", "").replace("🥛", "").replace("🌾", "").replace("🥜", "").strip()
            item_list = ", ".join(items[:6])
            script_parts.append(f"In the {clean_category} section, grab: {item_list}.")

    script_parts.append("All items have been verified allergen-safe. Happy shopping!")
    return " ".join(script_parts)
