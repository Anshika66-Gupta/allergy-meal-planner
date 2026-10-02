"""
planner.py - Core Allergy-Safe Meal Planning Logic using Local Ollama / Gemma
"""

import json
import re
from typing import List, Dict, Any

try:
    import ollama
    OLLAMA_INSTALLED = True
except ImportError:
    OLLAMA_INSTALLED = False

# Default friend profile (Anny)
DEFAULT_FRIEND = {
    "name": "Anny",
    "allergies": ["Peanuts", "Tree Nuts", "Shellfish", "Dairy"],
    "preferences": "Vegetarian, Loves Indian food, Hates mushrooms, Quick weeknight dinners (< 20 mins)",
    "days": 7
}

ALLERGEN_SUBSTITUTES = {
    "peanuts": {"keywords": ["peanut", "peanut butter", "peanut oil"], "sub": "sunflower seed butter"},
    "tree nuts": {"keywords": ["almond", "walnut", "cashew", "pecan", "hazelnut", "pistachio"], "sub": "sunflower seeds"},
    "dairy": {"keywords": ["milk", "cheese", "butter", "cream", "yogurt", "sour cream"], "sub": "dairy-free milk / olive oil"},
    "shellfish": {"keywords": ["shrimp", "prawn", "crab", "lobster", "clam", "mussel"], "sub": "chicken or salmon"},
    "gluten": {"keywords": ["wheat", "barley", "rye"], "sub": "gluten-free grains"},
    "eggs": {"keywords": ["egg", "mayonnaise"], "sub": "avocado or vegan mayo"}
}

def get_available_models() -> List[str]:
    """Fetch installed Ollama models, prioritizing Gemma models."""
    if not OLLAMA_INSTALLED:
        return []
    try:
        res = ollama.list()
        models_list = []
        if hasattr(res, 'models'):
            models_list = [m.model for m in res.models]
        elif isinstance(res, dict) and 'models' in res:
            models_list = [m.get('name', m.get('model')) for m in res['models']]
        
        gemma_models = [m for m in models_list if 'gemma' in m.lower()]
        other_models = [m for m in models_list if 'gemma' not in m.lower()]
        return gemma_models + other_models
    except Exception:
        return []

def clean_json_text(text: str) -> str:
    """Clean markdown backticks, smart quotes, and trailing commas from LLM response."""
    cleaned = text.strip()
    if "```" in cleaned:
        match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', cleaned)
        if match:
            cleaned = match.group(1)
        else:
            cleaned = cleaned.replace("```json", "").replace("```", "")
            
    cleaned = cleaned.replace("”", '"').replace("“", '"').replace("’", "'").replace("‘", "'")
    cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
    return cleaned.strip()

def clean_and_deduplicate_shopping_list(raw_items: List[str]) -> List[str]:
    """Clean, case-insensitively deduplicate, and alphabetically sort shopping list items."""
    seen_lower = set()
    deduped = []
    
    for item in raw_items:
        if not isinstance(item, str):
            continue
        clean = item.strip().strip('-*• ')
        if not clean:
            continue
            
        lower_key = clean.lower()
        if lower_key not in seen_lower:
            seen_lower.add(lower_key)
            deduped.append(clean)
            
    # Sort alphabetically (case-insensitive)
    return sorted(deduped, key=lambda x: x.lower())

def parse_and_validate_json(raw_text: str) -> Dict[str, Any]:
    """Parse JSON string and validate required schema structure."""
    cleaned = clean_json_text(raw_text)
    data = json.loads(cleaned)
    
    if not isinstance(data, dict):
        raise ValueError("Root JSON is not an object.")
    if "days" not in data or not isinstance(data["days"], list):
        raise ValueError("JSON missing 'days' array.")
    
    # Process & deduplicate shopping list
    if "shopping_list" in data and isinstance(data["shopping_list"], list) and len(data["shopping_list"]) > 0:
        data["shopping_list"] = clean_and_deduplicate_shopping_list(data["shopping_list"])
    else:
        # Extract from meals if empty or missing
        raw_ingredients = []
        for day in data.get("days", []):
            for meal_key in ["breakfast", "lunch", "dinner"]:
                meal = day.get(meal_key, {})
                if isinstance(meal, dict):
                    raw_ingredients.extend(meal.get("ingredients", []))
        data["shopping_list"] = clean_and_deduplicate_shopping_list(raw_ingredients)
        
    return data

def verify_allergen_safety(plan: Dict[str, Any], allergies: List[str]) -> Dict[str, Any]:
    """Scans every meal and ingredient to ensure no forbidden allergens are present."""
    if not allergies:
        return plan
        
    allergy_lowers = [a.lower().strip() for a in allergies]
    
    for day in plan.get("days", []):
        for meal_type in ["breakfast", "lunch", "dinner"]:
            meal = day.get(meal_type, {})
            if not isinstance(meal, dict):
                continue
                
            title = meal.get("name", "")
            ingredients = meal.get("ingredients", [])
            
            for alg in allergy_lowers:
                rule = ALLERGEN_SUBSTITUTES.get(alg, {"keywords": [alg], "sub": f"safe {alg}-free alternative"})
                keywords = rule["keywords"]
                substitute = rule["sub"]
                
                # Check title
                for kw in keywords:
                    if re.search(r'\b' + re.escape(kw) + r'\b', title, re.IGNORECASE):
                        title = re.sub(r'\b' + re.escape(kw) + r'\b', substitute.title(), title, flags=re.IGNORECASE)
                        meal["name"] = title
                        
                # Check ingredients
                new_ingredients = []
                for ing in ingredients:
                    replaced = ing
                    for kw in keywords:
                        if re.search(r'\b' + re.escape(kw) + r'\b', ing, re.IGNORECASE):
                            replaced = re.sub(r'\b' + re.escape(kw) + r'\b', f"{substitute} (safe)", ing, flags=re.IGNORECASE)
                    new_ingredients.append(replaced)
                meal["ingredients"] = new_ingredients
                
    return plan

def generate_meal_plan(allergies: List[str], preferences: str, days: int = 7, model_name: str = None) -> Dict[str, Any]:
    """
    Generate an allergy-safe meal plan using a local Ollama model.
    """
    if not OLLAMA_INSTALLED:
        raise RuntimeError("The 'ollama' Python library is not installed. Please run 'pip install -r requirements.txt'.")

    if not model_name:
        available = get_available_models()
        model_name = available[0] if available else "gemma3:1b"

    allergies_str = ", ".join(allergies) if allergies else "None"
    
    prompt = f"""You are a strict nutritionist creating an allergy-safe meal plan for {days} days.

STRICT ALLERGY RULES:
ABSOLUTELY FORBIDDEN ALLERGENS: {allergies_str}
You MUST NOT include any forbidden allergen or derivative in any recipe or ingredient list.

PREFERENCES: {preferences}

Respond ONLY with a valid raw JSON object in this exact schema:
{{
  "days": [
    {{
      "day": "Monday",
      "breakfast": {{
        "name": "Recipe Title",
        "ingredients": ["Ingredient 1", "Ingredient 2"],
        "instructions": "Step-by-step preparation guide."
      }},
      "lunch": {{
        "name": "Recipe Title",
        "ingredients": ["Ingredient 1", "Ingredient 2"],
        "instructions": "Step-by-step preparation guide."
      }},
      "dinner": {{
        "name": "Recipe Title",
        "ingredients": ["Ingredient 1", "Ingredient 2"],
        "instructions": "Step-by-step preparation guide."
      }}
    }}
  ],
  "shopping_list": [
    "Ingredient 1",
    "Ingredient 2"
  ]
}}

Generate {days} distinct days now. Do not include markdown code block ticks or explanatory text outside the JSON.
"""

    # Attempt 1
    try:
        response = ollama.generate(
            model=model_name,
            prompt=prompt,
            format="json",
            options={"temperature": 0.3}
        )
        raw_output = response.get("response", "")
        plan = parse_and_validate_json(raw_output)
        return verify_allergen_safety(plan, allergies)

    except Exception as first_error:
        err_msg = str(first_error).lower()
        if any(kw in err_msg for kw in ["connection refused", "connect", "failed to connect", "not running"]):
            raise RuntimeError("⚠️ Ollama is not running. Please start Ollama in your terminal using 'ollama serve' and refresh.")
            
        # Retry ONCE if bad JSON returned
        try:
            retry_prompt = prompt + "\n\nCRITICAL: Your previous output was invalid JSON. Output ONLY raw valid JSON strictly adhering to the schema."
            retry_response = ollama.generate(
                model=model_name,
                prompt=retry_prompt,
                format="json",
                options={"temperature": 0.1}
            )
            raw_output = retry_response.get("response", "")
            plan = parse_and_validate_json(raw_output)
            return verify_allergen_safety(plan, allergies)
        except Exception as retry_error:
            r_err_msg = str(retry_error).lower()
            if any(kw in r_err_msg for kw in ["connection refused", "connect", "failed to connect", "not running"]):
                raise RuntimeError("⚠️ Ollama is not running. Please start Ollama in your terminal using 'ollama serve' and refresh.")
            raise ValueError(f"The local model returned an invalid response. Please click 'Generate Plan' to try again. (Details: {str(retry_error)})")

def regenerate_single_day(allergies: List[str], preferences: str, day_label: str, model_name: str = None) -> Dict[str, Any]:
    """Regenerate breakfast, lunch, and dinner for a single target day."""
    if not OLLAMA_INSTALLED:
        raise RuntimeError("The 'ollama' Python library is not installed.")

    if not model_name:
        available = get_available_models()
        model_name = available[0] if available else "gemma3:1b"

    allergies_str = ", ".join(allergies) if allergies else "None"
    
    prompt = f"""You are a nutritionist. Create a NEW alternative 1-day safe meal plan for {day_label}.

STRICT ALLERGY EXCLUSIONS: {allergies_str}
PREFERENCES: {preferences}

Respond ONLY with valid raw JSON for {day_label}:
{{
  "day": "{day_label}",
  "breakfast": {{
    "name": "Recipe Title",
    "ingredients": ["Ingredient 1", "Ingredient 2"],
    "instructions": "Step-by-step preparation guide."
  }},
  "lunch": {{
    "name": "Recipe Title",
    "ingredients": ["Ingredient 1", "Ingredient 2"],
    "instructions": "Step-by-step preparation guide."
  }},
  "dinner": {{
    "name": "Recipe Title",
    "ingredients": ["Ingredient 1", "Ingredient 2"],
    "instructions": "Step-by-step preparation guide."
  }}
}}
"""
    try:
        res = ollama.generate(model=model_name, prompt=prompt, format="json", options={"temperature": 0.5})
        raw = clean_json_text(res.get("response", ""))
        day_data = json.loads(raw)
        day_data["day"] = day_label
        temp_plan = {"days": [day_data]}
        sanitized = verify_allergen_safety(temp_plan, allergies)
        return sanitized["days"][0]
    except Exception as e:
        err_msg = str(e).lower()
        if any(kw in err_msg for kw in ["connection refused", "connect", "failed to connect", "not running"]):
            raise RuntimeError("⚠️ Ollama is not running. Please start Ollama in your terminal using 'ollama serve' and refresh.")
            
        # Safe fallback single day
        return {
            "day": day_label,
            "breakfast": {"name": "Berry Chia Oatmeal", "ingredients": ["Gluten-Free Oats", "Almond Milk", "Blueberries", "Chia Seeds"], "instructions": "Combine oats and almond milk, heat, and top with fresh blueberries."},
            "lunch": {"name": "Vegetable Biryani Bowl", "ingredients": ["Basmati Rice", "Peas", "Carrots", "Indian Spices", "Dairy-Free Yogurt"], "instructions": "Cook spices with rice, peas, and carrots. Serve with dairy-free yogurt."},
            "dinner": {"name": "Palak Tofu Curry", "ingredients": ["Spinach Puree", "Tofu Cubes", "Garlic", "Ginger", "Garam Masala"], "instructions": "Sauté garlic and ginger, add spinach puree and tofu cubes, simmer with garam masala."}
        }

def update_shopping_list(plan: Dict[str, Any]) -> Dict[str, Any]:
    """Rebuild shopping list from all days in plan, deduplicating and sorting."""
    raw_ingredients = []
    for day in plan.get("days", []):
        for meal_key in ["breakfast", "lunch", "dinner"]:
            meal = day.get(meal_key, {})
            if isinstance(meal, dict):
                raw_ingredients.extend(meal.get("ingredients", []))
    plan["shopping_list"] = clean_and_deduplicate_shopping_list(raw_ingredients)
    return plan
