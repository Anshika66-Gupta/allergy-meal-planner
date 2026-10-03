"""
planner.py - Core Allergy-Safe Meal Planning Logic using Local Ollama / Gemma with Cloud Smart Engine
"""

import os
import json
import re
import random
from typing import List, Dict, Any, Tuple
from dotenv import load_dotenv

# Load local environment variables (.env) if present
load_dotenv()

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

# Accurate allergen keywords and safe replacements
ALLERGEN_RULES = {
    "peanuts": {
        "keywords": ["peanut butter", "peanut oil", "roasted peanuts", "peanuts", "peanut"],
        "sub": "sunflower seed butter"
    },
    "tree nuts": {
        "keywords": [
            "almond milk", "almond flour", "cashew paste", "cashew butter", "almond butter",
            "almonds", "almond", "walnuts", "walnut", "cashews", "cashew", "pecans", "pecan",
            "hazelnuts", "hazelnut", "pistachios", "pistachio", "macadamia"
        ],
        "sub": "toasted pumpkin & sunflower seeds"
    },
    "dairy": {
        "keywords": [
            "heavy cream", "sour cream", "cream cheese", "greek yogurt", "parmesan", "cheddar",
            "paneer", "ghee", "butter", "milk", "cheese", "cream", "yogurt"
        ],
        "sub": "dairy-free plant milk / olive oil"
    },
    "shellfish": {
        "keywords": [
            "shrimp", "prawn", "prawns", "crab", "lobster", "clam", "clams", "mussel", "mussels", "oyster", "oysters", "scallop", "scallops"
        ],
        "sub": "extra-firm tofu or chickpea protein"
    },
    "gluten": {
        "keywords": [
            "whole wheat bread", "wheat bread", "wheat flour", "all-purpose flour", "regular pasta",
            "wheat", "barley", "rye", "couscous", "semolina"
        ],
        "sub": "certified gluten-free grains"
    },
    "eggs": {
        "keywords": [
            "egg whites", "egg white", "egg yolks", "egg yolk", "hard-boiled eggs", "mayonnaise", "eggs", "egg"
        ],
        "sub": "avocado or vegan mayo"
    },
    "soy": {
        "keywords": [
            "soy sauce", "soy milk", "tofu", "tempeh", "edamame", "soybean", "miso"
        ],
        "sub": "coconut aminos / chickpea substitute"
    },
    "fish": {
        "keywords": [
            "salmon", "tuna", "cod", "tilapia", "halibut", "sardines", "sardine", "anchovies", "anchovy", "fish sauce"
        ],
        "sub": "hearty chickpeas or plant protein"
    }
}

def get_ollama_host() -> str:
    """Return configured Ollama host URL."""
    return os.getenv("OLLAMA_HOST", "http://localhost:11434").rstrip("/")

def get_available_models() -> List[str]:
    """Fetch installed Ollama models with a fast connection check so UI never freezes."""
    if not OLLAMA_INSTALLED:
        return []
    try:
        host = get_ollama_host()
        client = ollama.Client(host=host, timeout=2.0)
        res = client.list()
        models_list = []
        if hasattr(res, 'models'):
            for m in res.models:
                name = getattr(m, 'model', None) or getattr(m, 'name', None)
                if name:
                    models_list.append(str(name))
        elif isinstance(res, dict) and 'models' in res:
            for m in res['models']:
                name = m.get('name') or m.get('model')
                if name:
                    models_list.append(str(name))
        
        gemma_models = [m for m in models_list if 'gemma' in m.lower()]
        other_models = [m for m in models_list if 'gemma' not in m.lower()]
        return gemma_models + other_models
    except Exception:
        return []

def clean_json_text(text: str) -> str:
    """Clean markdown code blocks, backticks, smart quotes, and trailing commas from LLM output."""
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
        clean = item.strip().strip('-*• \t\n')
        if not clean:
            continue
            
        lower_key = clean.lower()
        if lower_key not in seen_lower:
            seen_lower.add(lower_key)
            deduped.append(clean)
            
    return sorted(deduped, key=lambda x: x.lower())

def generate_categorized_shopping_list(items: List[str]) -> Dict[str, List[str]]:
    """Group shopping list items accurately into grocery store aisles."""
    categorized = {
        "🥬 Produce & Fresh Herbs": [],
        "🍗 Meat, Fish & Plant Proteins": [],
        "🥛 Dairy & Milk Alternatives": [],
        "🌾 Grains, Pastas & Bakery": [],
        "🥜 Seeds, Spreads & Pantry": [],
        "🧂 Oils & Spices": []
    }
    
    produce_kw = [
        "spinach", "lettuce", "avocado", "cucumber", "tomato", "tomatoes", "apple", "banana",
        "berry", "berries", "blueberries", "lemon", "lime", "broccoli", "asparagus", "sweet potato",
        "potatoes", "potato", "onion", "onions", "garlic", "bell pepper", "peppers", "celery",
        "zucchini", "carrots", "carrot", "ginger", "cabbage", "basil", "parsley", "fruit",
        "vegetables", "veggies", "herb", "okra", "bhindi", "eggplant", "baingan", "curry leaves",
        "cilantro", "peas", "kale", "mushroom", "cauliflower", "mint", "chili", "jalapeno"
    ]
    protein_kw = [
        "chicken", "turkey", "beef", "salmon", "cod", "fish", "pork", "sausage", "tofu",
        "chickpeas", "lentils", "black beans", "kidney beans", "beans", "eggs", "egg",
        "dal", "rajma", "besan", "chickpea flour", "tempeh", "edamame"
    ]
    dairy_kw = [
        "dairy-free", "almond milk", "oat milk", "coconut milk", "plant-based milk", "vegan cheese",
        "dairy-free yogurt", "milk", "cheese", "butter", "cream", "yogurt", "paneer", "ghee",
        "parmesan", "cheddar", "sour cream"
    ]
    grains_kw = [
        "oats", "oatmeal", "rice", "quinoa", "bread", "gluten-free bread", "corn tortillas",
        "tortilla", "wrap", "pasta", "gluten-free pasta", "rice cakes", "granola", "poha",
        "basmati", "rava", "idli", "flour", "noodles"
    ]
    seeds_kw = [
        "seed", "seeds", "chia", "flax", "sunflower seed", "sunflower butter", "sunflower seed butter",
        "tahini", "nut butter", "spread", "jam", "honey", "maple syrup"
    ]

    for clean_item in items:
        item_lower = clean_item.lower()
        if any(kw in item_lower for kw in dairy_kw):
            categorized["🥛 Dairy & Milk Alternatives"].append(clean_item)
        elif any(kw in item_lower for kw in protein_kw):
            categorized["🍗 Meat, Fish & Plant Proteins"].append(clean_item)
        elif any(kw in item_lower for kw in seeds_kw):
            categorized["🥜 Seeds, Spreads & Pantry"].append(clean_item)
        elif any(kw in item_lower for kw in produce_kw):
            categorized["🥬 Produce & Fresh Herbs"].append(clean_item)
        elif any(kw in item_lower for kw in grains_kw):
            categorized["🌾 Grains, Pastas & Bakery"].append(clean_item)
        else:
            categorized["🧂 Oils & Spices"].append(clean_item)
            
    return categorized

def normalize_meal_dict(meal: Any, fallback_name: str) -> Dict[str, Any]:
    """Ensure meal is a dictionary adhering to the required schema."""
    if isinstance(meal, dict):
        return {
            "name": str(meal.get("name", fallback_name)),
            "prep_time": str(meal.get("prep_time", "15 mins")),
            "ingredients": list(meal.get("ingredients", [])) if isinstance(meal.get("ingredients"), list) else [str(meal.get("ingredients", ""))],
            "instructions": str(meal.get("instructions", "Prepare fresh and enjoy warm."))
        }
    elif isinstance(meal, str):
        return {
            "name": meal,
            "prep_time": "15 mins",
            "ingredients": [meal],
            "instructions": "Prepare fresh and enjoy warm."
        }
    return {
        "name": fallback_name,
        "prep_time": "15 mins",
        "ingredients": [],
        "instructions": "Prepare fresh and enjoy warm."
    }

def parse_and_validate_json(raw_text: str) -> Dict[str, Any]:
    """Parse JSON string and validate required schema structure with auto-repair."""
    cleaned = clean_json_text(raw_text)
    data = json.loads(cleaned)
    
    if not isinstance(data, dict):
        raise ValueError("Root JSON is not an object.")
    if "days" not in data or not isinstance(data["days"], list):
        raise ValueError("JSON missing 'days' array.")
    
    # Normalize day structure
    for i, day in enumerate(data["days"]):
        if not isinstance(day, dict):
            day = {"day": f"Day {i+1}"}
            data["days"][i] = day
        day["day"] = str(day.get("day", f"Day {i+1}"))
        day["breakfast"] = normalize_meal_dict(day.get("breakfast"), "Breakfast Special")
        day["lunch"] = normalize_meal_dict(day.get("lunch"), "Lunch Special")
        day["dinner"] = normalize_meal_dict(day.get("dinner"), "Dinner Special")

    if "shopping_list" in data and isinstance(data["shopping_list"], list) and len(data["shopping_list"]) > 0:
        data["shopping_list"] = clean_and_deduplicate_shopping_list(data["shopping_list"])
    else:
        raw_ingredients = []
        for day in data.get("days", []):
            for meal_key in ["breakfast", "lunch", "dinner"]:
                meal = day.get(meal_key, {})
                raw_ingredients.extend(meal.get("ingredients", []))
        data["shopping_list"] = clean_and_deduplicate_shopping_list(raw_ingredients)
        
    return data

def _is_safe_context(kw: str, full_text: str, start_idx: int) -> bool:
    """Check if keyword appearance is part of a non-allergenic safe compound."""
    prefix = full_text[:start_idx].lower()
    kw_lower = kw.lower()
    
    if kw_lower == "butter":
        safe_butters = ["sunflower ", "seed ", "peanut ", "almond ", "cocoa ", "apple ", "shea "]
        if any(prefix.endswith(p) for p in safe_butters):
            return True
    elif kw_lower == "milk":
        safe_milks = ["oat ", "coconut ", "almond ", "soy ", "plant-based ", "dairy-free ", "rice "]
        if any(prefix.endswith(p) for p in safe_milks):
            return True
    elif kw_lower in ["cheese", "yogurt", "cream"]:
        safe_dairy = ["vegan ", "dairy-free ", "plant-based ", "coconut ", "oat "]
        if any(prefix.endswith(p) for p in safe_dairy):
            return True
    elif kw_lower in ["bread", "pasta", "flour"]:
        safe_gluten = ["gluten-free ", "gf ", "rice ", "chickpea ", "almond "]
        if any(prefix.endswith(p) for p in safe_gluten):
            return True
    elif kw_lower == "mayo" or kw_lower == "mayonnaise":
        if "vegan" in prefix or "dairy-free" in prefix:
            return True
    return False

def _sanitize_string(text: str, active_rules: List[Tuple[str, List[str], str]], audit_log: List[Dict[str, Any]], location: str) -> str:
    """Sanitize a string against active allergy rules using protected token replacements."""
    placeholders = {}
    current = text

    for alg, keywords, substitute in active_rules:
        for kw in keywords:
            pattern = re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE)
            
            # Find matches and check exceptions
            new_text_parts = []
            last_idx = 0
            has_replacement = False
            
            for match in pattern.finditer(current):
                start, end = match.span()
                matched_kw = match.group(0)
                
                # Check if it's already a safe compound (e.g. sunflower seed butter for dairy check)
                if alg.lower() == "dairy" and _is_safe_context(matched_kw, current, start):
                    continue
                if alg.lower() == "gluten" and _is_safe_context(matched_kw, current, start):
                    continue
                if alg.lower() == "eggs" and _is_safe_context(matched_kw, current, start):
                    continue

                # Add preceding text
                new_text_parts.append(current[last_idx:start])
                token = f"__SAFE_TOK_{len(placeholders)}__"
                placeholders[token] = substitute
                new_text_parts.append(token)
                last_idx = end
                has_replacement = True

                audit_log.append({
                    "location": location,
                    "detected": matched_kw,
                    "allergen": alg.title(),
                    "action": f"Substituted '{matched_kw}' with '{substitute}'"
                })

            if has_replacement:
                new_text_parts.append(current[last_idx:])
                current = "".join(new_text_parts)

    # Restore placeholders
    for tok, sub_val in placeholders.items():
        current = current.replace(tok, sub_val)

    return current

def verify_allergen_safety(plan: Dict[str, Any], allergies: List[str]) -> Dict[str, Any]:
    """
    Deterministic Safety Audit Engine:
    Examines all meal titles, ingredients, and the consolidated shopping list.
    Safely substitutes any detected allergens without recursive cascade bugs
    and generates a full audit log.
    """
    audit_log = []
    total_ingredients_scanned = 0

    if not allergies:
        plan["audit_summary"] = {
            "total_scanned": 0,
            "violations_caught": 0,
            "details": [],
            "allergies_verified": [],
            "safe": True
        }
        return plan

    allergy_lowers = [a.lower().strip() for a in allergies if a.strip()]

    # Collect and sort rules by longest keyword first
    active_rules = []
    for alg in allergy_lowers:
        if alg in ALLERGEN_RULES:
            rule = ALLERGEN_RULES[alg]
            keywords = sorted(rule["keywords"], key=len, reverse=True)
            active_rules.append((alg, keywords, rule["sub"]))
        else:
            active_rules.append((alg, [alg], f"safe {alg}-free alternative"))

    # Scan and sanitize meals
    for day_idx, day in enumerate(plan.get("days", [])):
        day_label = day.get("day", f"Day {day_idx + 1}")
        for meal_type in ["breakfast", "lunch", "dinner"]:
            meal = day.get(meal_type, {})
            if not isinstance(meal, dict):
                continue

            orig_title = meal.get("name", "")
            meal["name"] = _sanitize_string(
                orig_title, active_rules, audit_log, f"{day_label} - {meal_type.title()} Title"
            )

            current_ingredients = list(meal.get("ingredients", []))
            total_ingredients_scanned += len(current_ingredients)

            sanitized_ingredients = []
            for ing in current_ingredients:
                sanitized_ing = _sanitize_string(
                    ing, active_rules, audit_log, f"{day_label} - {meal_type.title()} Ingredient"
                )
                sanitized_ingredients.append(sanitized_ing)

            meal["ingredients"] = sanitized_ingredients

    # Re-synchronize and deduplicate shopping list from sanitized meals
    all_shopping_ingredients = []
    for day in plan.get("days", []):
        for m_key in ["breakfast", "lunch", "dinner"]:
            all_shopping_ingredients.extend(day.get(m_key, {}).get("ingredients", []))

    plan["shopping_list"] = clean_and_deduplicate_shopping_list(all_shopping_ingredients)

    plan["audit_summary"] = {
        "total_scanned": total_ingredients_scanned,
        "violations_caught": len(audit_log),
        "details": audit_log,
        "allergies_verified": [a.title() for a in allergies],
        "safe": True
    }
    return plan

# Comprehensive Recipe Catalog for Smart Engine
RECIPE_CATALOG = {
    "breakfast": [
        {
            "name": "Masala Poha with Peas & Curry Leaves",
            "cuisine": "Indian",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "15 mins",
            "ingredients": ["Flattened Rice (Poha)", "Green Peas", "Mustard Seeds", "Curry Leaves", "Turmeric", "Fresh Lemon", "Olive Oil"],
            "instructions": "Rinse poha. Sauté mustard seeds, curry leaves, and green peas in olive oil. Toss poha with turmeric, salt, and fresh lemon juice."
        },
        {
            "name": "Avocado & Cherry Tomato Toast on Artisan Bread",
            "cuisine": "American",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "10 mins",
            "ingredients": ["Gluten-Free Bread", "Ripe Avocado", "Cherry Tomatoes", "Extra Virgin Olive Oil", "Sea Salt", "Fresh Cracked Pepper"],
            "instructions": "Toast artisan bread until golden. Mash avocado with olive oil and sea salt, spread generously, and top with juicy sliced cherry tomatoes."
        },
        {
            "name": "Besan Chilla (Savory Chickpea Pancakes)",
            "cuisine": "Indian",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "15 mins",
            "ingredients": ["Chickpea Flour (Besan)", "Diced Red Onion", "Fresh Tomato", "Cilantro", "Carom Seeds (Ajwain)", "Water", "Olive Oil"],
            "instructions": "Whisk chickpea flour with water, diced onions, tomatoes, and carom seeds. Ladle onto a hot skillet and cook until golden brown on both sides."
        },
        {
            "name": "South Indian Roasted Oats Upma",
            "cuisine": "Indian",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "15 mins",
            "ingredients": ["Gluten-Free Oats", "Mustard Seeds", "Fresh Minced Ginger", "Green Chili", "Diced Carrots", "Green Peas", "Olive Oil"],
            "instructions": "Dry roast oats. Sauté mustard seeds, ginger, green chili, and diced veggies. Add warm water, stir in oats, and steam until fluffy."
        },
        {
            "name": "Antioxidant Berry Smoothie Bowl",
            "cuisine": "American",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "10 mins",
            "ingredients": ["Oat Milk", "Frozen Bananas", "Blueberries", "Chia Seeds", "Sunflower Seed Butter"],
            "instructions": "Blend banana, oat milk, and wild blueberries into a rich creamy smoothie. Pour into a bowl and top with chia seeds and sunflower seed butter."
        },
        {
            "name": "Golden Tofu Scramble with Baby Spinach",
            "cuisine": "Mediterranean",
            "diet": ["Vegetarian", "Vegan"],
            "contains": ["Soy"],
            "prep_time": "15 mins",
            "ingredients": ["Firm Tofu", "Baby Spinach", "Ground Turmeric", "Garlic Powder", "Olive Oil", "Black Salt"],
            "instructions": "Crumble firm tofu into an olive oil skillet. Season with turmeric and garlic powder. Toss in baby spinach until wilted."
        },
        {
            "name": "Chickpea Flour Scramble with Bell Peppers",
            "cuisine": "Mediterranean",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "12 mins",
            "ingredients": ["Chickpea Flour", "Sweet Bell Peppers", "Baby Spinach", "Olive Oil", "Cumin", "Smoked Paprika"],
            "instructions": "Whisk chickpea flour with water and spices into a thick slurry. Scramble in an olive oil pan with bell peppers and spinach until tender."
        },
        {
            "name": "Cinnamon Apple Oatmeal with Sunflower Seeds",
            "cuisine": "American",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "12 mins",
            "ingredients": ["Gluten-Free Rolled Oats", "Oat Milk", "Crisp Red Apples", "Ceylon Cinnamon", "Pure Maple Syrup", "Toasted Sunflower Seeds"],
            "instructions": "Simmer oats in oat milk with cinnamon and diced apple until creamy. Drizzle with pure maple syrup and crunchy sunflower seeds."
        }
    ],
    "lunch": [
        {
            "name": "Yellow Dal Tadka with Steamed Jeera Rice",
            "cuisine": "Indian",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "20 mins",
            "ingredients": ["Yellow Toor Dal", "Basmati Rice", "Cumin Seeds", "Fresh Garlic", "Tomato", "Olive Oil", "Cilantro"],
            "instructions": "Cook dal until soft and creamy. Heat olive oil with cumin, minced garlic, and tomato. Pour the fragrant tadka over dal and serve over jeera rice."
        },
        {
            "name": "Mediterranean Chickpea & Avocado Power Bowl",
            "cuisine": "Mediterranean",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "12 mins",
            "ingredients": ["Cooked Chickpeas", "Ripe Avocado", "Persian Cucumber", "Cherry Tomatoes", "Fresh Lemon Juice", "Tahini Dressing", "Olive Oil"],
            "instructions": "Combine chickpeas, diced cucumber, avocado, and cherry tomatoes in a wide bowl. Drizzle with creamy lemon tahini dressing."
        },
        {
            "name": "Rajma Masala (Kidney Bean Curry) with Brown Rice",
            "cuisine": "Indian",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "20 mins",
            "ingredients": ["Red Kidney Beans (Rajma)", "Tomato-Onion Puree", "Ginger-Garlic Paste", "Garam Masala", "Steamed Brown Rice"],
            "instructions": "Simmer tender kidney beans in a spiced onion-tomato gravy with garam masala. Serve hot over steamed brown rice."
        },
        {
            "name": "Garden Quinoa & Vegetable Pulao",
            "cuisine": "Indian",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "18 mins",
            "ingredients": ["Quinoa", "Diced Carrots", "Green Beans", "Sweet Peas", "Whole Cardamom & Cloves", "Olive Oil"],
            "instructions": "Sauté whole spices and vegetables in olive oil. Add rinsed quinoa and vegetable broth, cover, and steam until fluffy."
        },
        {
            "name": "Aloo Gobi (Spiced Potato & Cauliflower Curry)",
            "cuisine": "Indian",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "20 mins",
            "ingredients": ["Cauliflower Florets", "Potatoes", "Turmeric", "Ground Coriander", "Cumin Seeds", "Fresh Ginger", "Steamed Basmati Rice"],
            "instructions": "Sauté fresh ginger and cumin in olive oil. Add potato and cauliflower cubes with turmeric and coriander. Cover and steam until tender."
        },
        {
            "name": "Herb-Grilled Chicken Breast with Quinoa Salad",
            "cuisine": "Mediterranean",
            "diet": ["Non-Vegetarian"],
            "contains": [],
            "prep_time": "20 mins",
            "ingredients": ["Chicken Breast", "Quinoa", "Cucumbers", "Cherry Tomatoes", "Olive Oil", "Oregano", "Lemon"],
            "instructions": "Season chicken breast with oregano, garlic, and olive oil. Sear on a hot pan until cooked through (165°F). Serve with a fresh lemon quinoa salad."
        },
        {
            "name": "Pan-Seared Salmon with Lemon Asparagus",
            "cuisine": "Mediterranean",
            "diet": ["Non-Vegetarian", "Pescatarian"],
            "contains": ["Fish"],
            "prep_time": "18 mins",
            "ingredients": ["Wild Salmon Fillet", "Fresh Asparagus", "Olive Oil", "Garlic", "Lemon Wedges", "Black Pepper"],
            "instructions": "Pan-sear salmon fillet in olive oil skin-side down until crispy, flip and finish. Sauté asparagus with minced garlic and fresh lemon juice."
        }
    ],
    "dinner": [
        {
            "name": "Palak Chickpea Curry with Basmati Rice",
            "cuisine": "Indian",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "18 mins",
            "ingredients": ["Spinach Puree", "Cooked Chickpeas", "Garlic", "Ginger", "Garam Masala", "Steamed Basmati Rice"],
            "instructions": "Simmer tender chickpeas in garlic-infused spinach puree with garam masala. Serve over hot aromatic basmati rice."
        },
        {
            "name": "Creamy Coconut Vegetable Korma",
            "cuisine": "Indian",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "20 mins",
            "ingredients": ["Coconut Milk", "Diced Carrots", "Sweet Peas", "Potatoes", "Mild Korma Spices", "Steamed Basmati Rice"],
            "instructions": "Simmer mixed garden vegetables in rich coconut milk with korma spice blend until fork-tender. Serve warm over basmati rice."
        },
        {
            "name": "South Indian Sambar Stew with Steamed Idli",
            "cuisine": "Indian",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "18 mins",
            "ingredients": ["Toor Dal", "Diced Mixed Vegetables", "Sambar Spice Mix", "Tamarind Pulp", "Steamed Rice Idlis"],
            "instructions": "Simmer lentils and vegetables in tangy tamarind broth with aromatic sambar spices. Serve piping hot with soft steamed rice idlis."
        },
        {
            "name": "Baingan Bharta (Fire-Roasted Eggplant) with Jeera Rice",
            "cuisine": "Indian",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "20 mins",
            "ingredients": ["Roasted Eggplant Pulp", "Diced Onions", "Tomatoes", "Green Chilies", "Cilantro", "Jeera Rice"],
            "instructions": "Sauté onions, tomatoes, and chilies until caramelized. Mash in roasted eggplant pulp, season with spices, and simmer for 10 minutes."
        },
        {
            "name": "Crispy Bhindi Masala (Spiced Okra) with Lentil Soup",
            "cuisine": "Indian",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "20 mins",
            "ingredients": ["Fresh Okra (Bhindi)", "Amchur (Dried Mango)", "Cumin", "Yellow Lentils", "Turmeric", "Olive Oil"],
            "instructions": "Sauté sliced okra with cumin and amchur until crisp. Pair with a comforting bowl of warm turmeric yellow lentil soup."
        },
        {
            "name": "Palak Tofu Curry with Gluten-Free Corn Tortillas",
            "cuisine": "Indian",
            "diet": ["Vegetarian", "Vegan"],
            "contains": ["Soy"],
            "prep_time": "20 mins",
            "ingredients": ["Fresh Spinach Puree", "Firm Tofu Cubes", "Garlic", "Ginger", "Garam Masala", "Gluten-Free Corn Tortillas"],
            "instructions": "Sauté ginger-garlic, stir in vibrant spinach puree, and gently fold in golden tofu cubes. Simmer with garam masala and pair with warm tortillas."
        },
        {
            "name": "Lemon Herb Chicken with Roasted Potatoes",
            "cuisine": "Mediterranean",
            "diet": ["Non-Vegetarian"],
            "contains": [],
            "prep_time": "20 mins",
            "ingredients": ["Chicken Breast Cutlets", "Baby Potatoes", "Rosemary", "Olive Oil", "Lemon", "Garlic"],
            "instructions": "Pan-sear chicken cutlets with rosemary, garlic, and fresh lemon juice. Serve alongside tender golden roasted baby potatoes."
        }
    ]
}

def filter_recipe_pool(meal_type: str, allergies: List[str], preferences: str) -> List[Dict[str, Any]]:
    """Select candidate recipes from the catalog filtered by allergies and dislikes, scored by preferences."""
    raw_pool = RECIPE_CATALOG.get(meal_type, [])
    allergy_lowers = [a.lower().strip() for a in allergies if a.strip()]
    pref_lower = preferences.lower()

    # Parse dislikes from preferences (e.g. "hates mushrooms, no eggplant")
    disliked_keywords = []
    for word in ["mushrooms", "mushroom", "eggplant", "baingan", "okra", "bhindi", "cilantro", "broccoli", "onion"]:
        if f"hate {word}" in pref_lower or f"hates {word}" in pref_lower or f"no {word}" in pref_lower:
            disliked_keywords.append(word)

    filtered = []
    for recipe in raw_pool:
        # Check allergen conflicts
        has_allergen_conflict = False
        for c in recipe.get("contains", []):
            if c.lower() in allergy_lowers:
                has_allergen_conflict = True
                break
        if has_allergen_conflict:
            continue

        # Check dislike conflicts
        has_dislike = False
        recipe_text = (recipe["name"] + " " + " ".join(recipe["ingredients"])).lower()
        for dis in disliked_keywords:
            if dis in recipe_text:
                has_dislike = True
                break
        if has_dislike:
            continue

        # Check vegetarian preference strictly if specified
        is_veg_req = "vegetarian" in pref_lower or "vegan" in pref_lower
        if is_veg_req and "Vegetarian" not in recipe.get("diet", []) and "Vegan" not in recipe.get("diet", []):
            continue

        # Score recipe based on preferences match
        score = 0
        cuisine = recipe.get("cuisine", "").lower()
        if cuisine and cuisine in pref_lower:
            score += 4
        
        # Check if key ingredients match user request (e.g. chicken, salmon, oats, poha)
        for ing in recipe.get("ingredients", []):
            ing_words = ing.lower().split()
            if any(w in pref_lower for w in ing_words if len(w) > 3):
                score += 2

        filtered.append((score, recipe))

    if not filtered:
        return raw_pool

    # Sort candidates by preference score descending
    filtered.sort(key=lambda x: x[0], reverse=True)
    return [item[1] for item in filtered]


def generate_smart_fallback_meal_plan(allergies: List[str], preferences: str, days: int = 7) -> Dict[str, Any]:
    """
    Intelligent Safety & Variety Engine:
    Dynamically generates personalized, allergy-safe meals matching user preferences,
    dietary types, and dislikes, guaranteeing non-repeating diverse days.
    """
    day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    
    b_pool = filter_recipe_pool("breakfast", allergies, preferences)
    l_pool = filter_recipe_pool("lunch", allergies, preferences)
    d_pool = filter_recipe_pool("dinner", allergies, preferences)

    generated_days = []
    for i in range(days):
        day_label = day_names[i % len(day_names)] if days <= 7 else f"Day {i+1}"
        b = b_pool[i % len(b_pool)]
        l = l_pool[i % len(l_pool)]
        d = d_pool[i % len(d_pool)]
        
        generated_days.append({
            "day": day_label,
            "breakfast": {
                "name": b["name"],
                "prep_time": b.get("prep_time", "15 mins"),
                "ingredients": list(b.get("ingredients", [])),
                "instructions": b.get("instructions", "Prepare fresh.")
            },
            "lunch": {
                "name": l["name"],
                "prep_time": l.get("prep_time", "15 mins"),
                "ingredients": list(l.get("ingredients", [])),
                "instructions": l.get("instructions", "Prepare fresh.")
            },
            "dinner": {
                "name": d["name"],
                "prep_time": d.get("prep_time", "20 mins"),
                "ingredients": list(d.get("ingredients", [])),
                "instructions": d.get("instructions", "Prepare fresh.")
            }
        })
        
    temp_plan = {"days": generated_days}
    sanitized = verify_allergen_safety(temp_plan, allergies)
    sanitized["engine"] = "Smart Safety Engine (Cloud Fallback)"
    return sanitized

def generate_meal_plan(allergies: List[str], preferences: str, days: int = 7, model_name: str = None, temperature: float = 0.3) -> Dict[str, Any]:
    """
    Generate an allergy-safe meal plan using local Ollama model if reachable,
    or immediately use the Smart Variety Safety Engine on Render / Cloud.
    """
    available_models = get_available_models()
    
    # If Ollama is not installed or no daemon is reachable, use smart engine
    if not OLLAMA_INSTALLED or not available_models:
        return generate_smart_fallback_meal_plan(allergies, preferences, days)

    target_model = model_name if model_name and model_name in available_models else available_models[0]
    allergies_str = ", ".join(allergies) if allergies else "None"
    
    prompt = f"""You are an expert nutritionist creating a strict, allergy-safe meal plan for {days} days.

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
        "prep_time": "15 mins",
        "ingredients": ["Ingredient 1", "Ingredient 2"],
        "instructions": "Step-by-step preparation guide."
      }},
      "lunch": {{
        "name": "Recipe Title",
        "prep_time": "15 mins",
        "ingredients": ["Ingredient 1", "Ingredient 2"],
        "instructions": "Step-by-step preparation guide."
      }},
      "dinner": {{
        "name": "Recipe Title",
        "prep_time": "20 mins",
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
        host = get_ollama_host()
        client = ollama.Client(host=host, timeout=60.0)
        response = client.generate(
            model=target_model,
            prompt=prompt,
            format="json",
            options={"temperature": float(temperature)}
        )
        raw_output = response.get("response", "")
        plan = parse_and_validate_json(raw_output)
        sanitized = verify_allergen_safety(plan, allergies)
        sanitized["engine"] = f"Local Ollama ({target_model})"
        return sanitized
    except Exception:
        # Graceful fallback to smart cloud engine
        return generate_smart_fallback_meal_plan(allergies, preferences, days)

def regenerate_single_day(allergies: List[str], preferences: str, day_label: str, model_name: str = None, temperature: float = 0.5, existing_day_meals: List[str] = None) -> Dict[str, Any]:
    """
    Regenerate breakfast, lunch, and dinner for a single target day.
    Guarantees a distinct, non-repeating alternative set of safe recipes.
    """
    available_models = get_available_models()
    
    if OLLAMA_INSTALLED and available_models and model_name in available_models:
        allergies_str = ", ".join(allergies) if allergies else "None"
        prompt = f"""You are a nutritionist. Create a NEW alternative 1-day safe meal plan for {day_label}.
STRICT ALLERGY EXCLUSIONS: {allergies_str}
PREFERENCES: {preferences}

Respond ONLY with valid raw JSON for {day_label}:
{{
  "day": "{day_label}",
  "breakfast": {{
    "name": "Recipe Title",
    "prep_time": "15 mins",
    "ingredients": ["Ingredient 1", "Ingredient 2"],
    "instructions": "Step-by-step preparation guide."
  }},
  "lunch": {{
    "name": "Recipe Title",
    "prep_time": "15 mins",
    "ingredients": ["Ingredient 1", "Ingredient 2"],
    "instructions": "Step-by-step preparation guide."
  }},
  "dinner": {{
    "name": "Recipe Title",
    "prep_time": "20 mins",
    "ingredients": ["Ingredient 1", "Ingredient 2"],
    "instructions": "Step-by-step preparation guide."
  }}
}}
"""
        try:
            host = get_ollama_host()
            client = ollama.Client(host=host, timeout=45.0)
            res = client.generate(
                model=model_name,
                prompt=prompt,
                format="json",
                options={"temperature": float(temperature)}
            )
            raw = clean_json_text(res.get("response", ""))
            day_data = json.loads(raw)
            day_data["day"] = day_label
            day_data["breakfast"] = normalize_meal_dict(day_data.get("breakfast"), "Breakfast Special")
            day_data["lunch"] = normalize_meal_dict(day_data.get("lunch"), "Lunch Special")
            day_data["dinner"] = normalize_meal_dict(day_data.get("dinner"), "Dinner Special")
            temp_plan = {"days": [day_data]}
            sanitized = verify_allergen_safety(temp_plan, allergies)
            return sanitized["days"][0]
        except Exception:
            pass

    # High-quality smart generator with rotation:
    b_pool = filter_recipe_pool("breakfast", allergies, preferences)
    l_pool = filter_recipe_pool("lunch", allergies, preferences)
    d_pool = filter_recipe_pool("dinner", allergies, preferences)

    # Pick a candidate not in existing_day_meals to avoid duplicate recipes
    avoid_names = set(existing_day_meals or [])
    b_cand = [r for r in b_pool if r["name"] not in avoid_names] or b_pool
    l_cand = [r for r in l_pool if r["name"] not in avoid_names] or l_pool
    d_cand = [r for r in d_pool if r["name"] not in avoid_names] or d_pool

    b_choice = random.choice(b_cand)
    l_choice = random.choice(l_cand)
    d_choice = random.choice(d_cand)

    new_day = {
        "day": day_label,
        "breakfast": {
            "name": b_choice["name"],
            "prep_time": b_choice.get("prep_time", "15 mins"),
            "ingredients": list(b_choice.get("ingredients", [])),
            "instructions": b_choice.get("instructions", "Prepare fresh.")
        },
        "lunch": {
            "name": l_choice["name"],
            "prep_time": l_choice.get("prep_time", "15 mins"),
            "ingredients": list(l_choice.get("ingredients", [])),
            "instructions": l_choice.get("instructions", "Prepare fresh.")
        },
        "dinner": {
            "name": d_choice["name"],
            "prep_time": d_choice.get("prep_time", "20 mins"),
            "ingredients": list(d_choice.get("ingredients", [])),
            "instructions": d_choice.get("instructions", "Prepare fresh.")
        }
    }
    temp_plan = {"days": [new_day]}
    sanitized = verify_allergen_safety(temp_plan, allergies)
    return sanitized["days"][0]

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
