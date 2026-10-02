"""
planner.py - Core Allergy-Safe Meal Planning Logic using Local Ollama / Gemma with Cloud Smart Engine
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
    "shellfish": {"keywords": ["shrimp", "prawn", "crab", "lobster", "clam", "mussel"], "sub": "tofu or paneer alternative"},
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
            
    return sorted(deduped, key=lambda x: x.lower())

def parse_and_validate_json(raw_text: str) -> Dict[str, Any]:
    """Parse JSON string and validate required schema structure."""
    cleaned = clean_json_text(raw_text)
    data = json.loads(cleaned)
    
    if not isinstance(data, dict):
        raise ValueError("Root JSON is not an object.")
    if "days" not in data or not isinstance(data["days"], list):
        raise ValueError("JSON missing 'days' array.")
    
    if "shopping_list" in data and isinstance(data["shopping_list"], list) and len(data["shopping_list"]) > 0:
        data["shopping_list"] = clean_and_deduplicate_shopping_list(data["shopping_list"])
    else:
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

def generate_smart_fallback_meal_plan(allergies: List[str], preferences: str, days: int = 7) -> Dict[str, Any]:
    """
    Generates a guaranteed safe, delicious meal plan tailored to allergies & preferences
    when running in cloud environments (Render, Streamlit Cloud) without local Ollama daemon.
    """
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    breakfast_pool = [
        {"name": "Masala Poha with Peas & Curry Leaves", "ingredients": ["Flattened Rice (Poha)", "Green Peas", "Mustard Seeds", "Curry Leaves", "Turmeric", "Lemon"], "instructions": "Rinse poha. Sauté mustard seeds, curry leaves, and peas. Toss poha with turmeric and fresh lemon juice."},
        {"name": "Avocado & Tomato Toast on Gluten-Free Bread", "ingredients": ["Gluten-Free Bread", "Ripe Avocado", "Cherry Tomatoes", "Olive Oil", "Black Pepper"], "instructions": "Toast bread. Mash avocado with olive oil and salt, spread over toast, and top with sliced cherry tomatoes."},
        {"name": "Besan Chilla (Savory Chickpea Pancakes)", "ingredients": ["Chickpea Flour (Besan)", "Onion", "Tomato", "Cilantro", "Carom Seeds (Ajwain)", "Water"], "instructions": "Mix besan with water, diced veggies, and spices to form a batter. Pour onto a pan and cook until golden on both sides."},
        {"name": "South Indian Oats Upma", "ingredients": ["Gluten-Free Oats", "Mustard Seeds", "Ginger", "Green Chili", "Veggies (Carrots, Peas)", "Olive Oil"], "instructions": "Roast oats. Sauté spices and diced vegetables. Add hot water, fold in oats, and cook until fluffy."},
        {"name": "Smoothie Bowl with Chia & Berries", "ingredients": ["Oat Milk", "Frozen Bananas", "Blueberries", "Chia Seeds", "Sunflower Seed Butter"], "instructions": "Blend banana, oat milk, and blueberries into a thick smoothie. Top with chia seeds and sunflower seed butter."},
        {"name": "Tofu Scramble with Spinach & Turmeric", "ingredients": ["Firm Tofu", "Spinach", "Turmeric", "Garlic Powder", "Olive Oil", "Salt"], "instructions": "Crumble tofu into a skillet with olive oil. Add turmeric, garlic powder, and fresh spinach. Sauté until wilted."}
    ]
    
    lunch_pool = [
        {"name": "Yellow Dal Tadka with Jeera Rice", "ingredients": ["Yellow Toor Dal", "Basmati Rice", "Cumin Seeds", "Garlic", "Tomato", "Olive Oil"], "instructions": "Cook dal until soft. Prepare tadka by heating olive oil with cumin, garlic, and tomato. Combine with dal and serve over jeera rice."},
        {"name": "Chickpea & Avocado Power Bowl", "ingredients": ["Cooked Chickpeas", "Ripe Avocado", "Cucumber", "Cherry Tomatoes", "Lemon Tahini Dressing"], "instructions": "Combine chickpeas, diced cucumber, avocado, and tomatoes in a bowl. Drizzle with lemon tahini dressing."},
        {"name": "Rajma Masala (Kidney Bean Curry) with Brown Rice", "ingredients": ["Red Kidney Beans (Rajma)", "Onion-Tomato Puree", "Ginger-Garlic Paste", "Garam Masala", "Brown Rice"], "instructions": "Simmer kidney beans in a spiced onion-tomato gravy with garam masala. Serve hot over steamed brown rice."},
        {"name": "Quinoa Veggie Pulao", "ingredients": ["Quinoa", "Carrots", "Green Beans", "Peas", "Whole Spices (Cardamom, Cloves)", "Olive Oil"], "instructions": "Sauté whole spices and vegetables in olive oil. Add quinoa and vegetable broth, cover, and cook until fluffy."},
        {"name": "Aloo Gobi (Potato & Cauliflower Curry)", "ingredients": ["Cauliflower Florets", "Potatoes", "Turmeric", "Coriander Powder", "Cumin", "Ginger"], "instructions": "Sauté ginger and cumin. Add potato and cauliflower cubes with turmeric and coriander powder. Cover and cook until tender."}
    ]
    
    dinner_pool = [
        {"name": "Palak Tofu Curry with Corn Tortillas", "ingredients": ["Spinach Puree", "Firm Tofu Cubes", "Garlic", "Ginger", "Garam Masala", "Gluten-Free Corn Tortillas"], "instructions": "Sauté garlic and ginger, add fresh spinach puree and tofu cubes. Simmer with garam masala and serve with warm tortillas."},
        {"name": "Baingan Bharta (Smoked Eggplant Curry) with Rice", "ingredients": ["Roasted Eggplant", "Onions", "Tomatoes", "Green Chilies", "Coriander", "Jeera Rice"], "instructions": "Mash roasted eggplant flesh. Sauté onions, tomatoes, and chilies, fold in eggplant, and simmer for 10 minutes."},
        {"name": "Bhindi Masala (Spiced Okra) with Lentil Soup", "ingredients": ["Okra (Bhindi)", "Amchur (Mango Powder)", "Cumin", "Yellow Lentils", "Turmeric"], "instructions": "Sauté sliced okra with cumin and amchur powder until crisp. Pair with a bowl of warm turmeric yellow lentil soup."},
        {"name": "Vegetable Korma (Dairy-Free Coconut Milk)", "ingredients": ["Coconut Milk", "Carrots", "Peas", "Potatoes", "Korma Spice Mix", "Basmati Rice"], "instructions": "Simmer mixed vegetables in rich coconut milk with korma spice mix until vegetables are tender. Serve over basmati rice."},
        {"name": "South Indian Sambar with Steamed Idli", "ingredients": ["Toor Dal", "Mixed Veggies", "Sambar Powder", "Tamarind Pulp", "Rice Idli"], "instructions": "Cook dal and veggies in tamarind broth with sambar powder. Serve piping hot alongside soft steamed idlis."}
    ]

    generated_days = []
    for i in range(days):
        day_label = day_names[i % len(day_names)] if days <= 7 else f"Day {i+1}"
        b = breakfast_pool[i % len(breakfast_pool)]
        l = lunch_pool[i % len(lunch_pool)]
        d = dinner_pool[i % len(dinner_pool)]
        
        generated_days.append({
            "day": day_label,
            "breakfast": b,
            "lunch": l,
            "dinner": d
        })
        
    temp_plan = {"days": generated_days}
    sanitized = verify_allergen_safety(temp_plan, allergies)
    
    raw_ing = []
    for day in sanitized["days"]:
        for meal_key in ["breakfast", "lunch", "dinner"]:
            raw_ing.extend(day[meal_key]["ingredients"])
            
    sanitized["shopping_list"] = clean_and_deduplicate_shopping_list(raw_ing)
    return sanitized

def generate_meal_plan(allergies: List[str], preferences: str, days: int = 7, model_name: str = None, temperature: float = 0.3) -> Dict[str, Any]:
    """
    Generate an allergy-safe meal plan using local Ollama model if active,
    or smart cloud generator fallback when deployed on Render / cloud host.
    """
    if not OLLAMA_INSTALLED:
        return generate_smart_fallback_meal_plan(allergies, preferences, days)

    if not model_name:
        available = get_available_models()
        if available:
            model_name = available[0]
        else:
            return generate_smart_fallback_meal_plan(allergies, preferences, days)

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

    try:
        response = ollama.generate(
            model=model_name,
            prompt=prompt,
            format="json",
            options={"temperature": float(temperature)}
        )
        raw_output = response.get("response", "")
        plan = parse_and_validate_json(raw_output)
        return verify_allergen_safety(plan, allergies)

    except Exception:
        return generate_smart_fallback_meal_plan(allergies, preferences, days)

def regenerate_single_day(allergies: List[str], preferences: str, day_label: str, model_name: str = None, temperature: float = 0.5) -> Dict[str, Any]:
    """Regenerate breakfast, lunch, and dinner for a single target day."""
    if not OLLAMA_INSTALLED:
        fallback_plan = generate_smart_fallback_meal_plan(allergies, preferences, 1)
        day_data = fallback_plan["days"][0]
        day_data["day"] = day_label
        return day_data

    if not model_name:
        available = get_available_models()
        if not available:
            fallback_plan = generate_smart_fallback_meal_plan(allergies, preferences, 1)
            day_data = fallback_plan["days"][0]
            day_data["day"] = day_label
            return day_data
        model_name = available[0]

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
        res = ollama.generate(
            model=model_name, 
            prompt=prompt, 
            format="json", 
            options={"temperature": float(temperature)}
        )
        raw = clean_json_text(res.get("response", ""))
        day_data = json.loads(raw)
        day_data["day"] = day_label
        temp_plan = {"days": [day_data]}
        sanitized = verify_allergen_safety(temp_plan, allergies)
        return sanitized["days"][0]
    except Exception:
        fallback_plan = generate_smart_fallback_meal_plan(allergies, preferences, 1)
        day_data = fallback_plan["days"][0]
        day_data["day"] = day_label
        return day_data

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
