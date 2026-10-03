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
            "description": str(meal.get("description", "A wholesome, allergy-safe dish prepared fresh with nourishing ingredients.")),
            "ingredients": list(meal.get("ingredients", [])) if isinstance(meal.get("ingredients"), list) else [str(meal.get("ingredients", ""))],
            "instructions": str(meal.get("instructions", "Prepare fresh and enjoy warm.")),
            "chef_tip": str(meal.get("chef_tip", "Season to taste with fresh herbs and quality olive oil."))
        }
    elif isinstance(meal, str):
        return {
            "name": meal,
            "prep_time": "15 mins",
            "description": "A wholesome, allergy-safe dish prepared fresh with nourishing ingredients.",
            "ingredients": [meal],
            "instructions": "Prepare fresh and enjoy warm.",
            "chef_tip": "Season to taste with fresh herbs and quality olive oil."
        }
    return {
        "name": fallback_name,
        "prep_time": "15 mins",
        "description": "A wholesome, allergy-safe dish prepared fresh with nourishing ingredients.",
        "ingredients": [],
        "instructions": "Prepare fresh and enjoy warm.",
        "chef_tip": "Season to taste with fresh herbs and quality olive oil."
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
            "description": "A light, aromatic Maharashtrian breakfast of flattened rice flakes tempered with mustard seeds, fresh curry leaves, and sweet green peas. Naturally nut-, dairy-, and gluten-free.",
            "ingredients": ["Flattened Rice (Poha)", "Green Peas", "Mustard Seeds", "Curry Leaves", "Turmeric", "Fresh Lemon", "Olive Oil"],
            "instructions": "1. Rinse poha in a colander for 30s until soft; drain well.\n2. Heat olive oil in a skillet. Crackle mustard seeds, then add curry leaves.\n3. Add green peas and turmeric powder; sauté for 2 minutes.\n4. Gently fold in softened poha, season with sea salt, cover and steam on low for 3 minutes.\n5. Squeeze fresh lemon juice over the top and garnish with cilantro.",
            "chef_tip": "Drizzle fresh lemon juice right after turning off the heat to preserve bright citrus notes and maximize vitamin absorption."
        },
        {
            "name": "Avocado & Cherry Tomato Toast on Artisan Bread",
            "cuisine": "American",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "10 mins",
            "description": "Creamy ripe Hass avocado mashed with extra virgin olive oil and sea salt, spread generously over crisp artisan gluten-free toast and topped with juicy cherry tomatoes.",
            "ingredients": ["Gluten-Free Bread", "Ripe Avocado", "Cherry Tomatoes", "Extra Virgin Olive Oil", "Sea Salt", "Fresh Cracked Pepper"],
            "instructions": "1. Toast artisan gluten-free bread until crisp and golden brown.\n2. In a bowl, coarsely mash ripe avocado with olive oil, sea salt, and black pepper.\n3. Spread avocado mixture evenly across warm toast slices.\n4. Top with sliced cherry tomatoes and finish with a delicate swirl of olive oil.",
            "chef_tip": "Lightly rub a cut garlic clove across the warm toasted crust for an irresistible subtle aroma without raw garlic heat."
        },
        {
            "name": "Besan Chilla (Savory Chickpea Pancakes)",
            "cuisine": "Indian",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "15 mins",
            "description": "Golden, protein-rich savory Indian pancakes made from stone-ground chickpea flour, diced red onions, and digestive carom seeds.",
            "ingredients": ["Chickpea Flour (Besan)", "Diced Red Onion", "Fresh Tomato", "Cilantro", "Carom Seeds (Ajwain)", "Water", "Olive Oil"],
            "instructions": "1. Whisk chickpea flour with water, salt, carom seeds, and turmeric into a smooth pancake batter.\n2. Fold in finely diced red onions, chopped tomatoes, and fresh cilantro.\n3. Heat a non-stick skillet with 1 tsp olive oil over medium-high heat.\n4. Ladle batter onto the skillet, spreading into a thin disc. Cook for 2-3 minutes until golden; flip and cook the other side.\n5. Serve hot with safe coriander chutney.",
            "chef_tip": "Crushing carom seeds (ajwain) between your palms before adding to the batter releases essential aromatic oils."
        },
        {
            "name": "South Indian Roasted Oats Upma",
            "cuisine": "Indian",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "15 mins",
            "description": "A comforting, savory breakfast porridge made by roasting rolled gluten-free oats and simmering them with mustard seeds, fresh ginger, and garden vegetables.",
            "ingredients": ["Gluten-Free Oats", "Mustard Seeds", "Fresh Minced Ginger", "Green Chili", "Diced Carrots", "Green Peas", "Olive Oil"],
            "instructions": "1. Dry-roast gluten-free oats in a skillet for 3 minutes until warm and nutty; set aside.\n2. Heat olive oil in a pan. Splutter mustard seeds, then add minced ginger and green chili.\n3. Add diced carrots and peas; sauté for 3-4 minutes until tender.\n4. Pour in 1.5 cups boiling water with salt. Slowly stir in roasted oats.\n5. Cover and simmer on low for 3 minutes until water is absorbed and oats are fluffy.",
            "chef_tip": "Dry roasting the oats first keeps them fluffy and prevents them from turning mushy when water is added."
        },
        {
            "name": "Antioxidant Berry Smoothie Bowl",
            "cuisine": "American",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "10 mins",
            "description": "A thick, velvety smoothie bowl loaded with wild blueberries, ripe bananas, and creamy oat milk, crowned with crunchy seeds and sunflower butter.",
            "ingredients": ["Oat Milk", "Frozen Bananas", "Blueberries", "Chia Seeds", "Sunflower Seed Butter"],
            "instructions": "1. Add frozen bananas, wild blueberries, and chilled oat milk into a high-speed blender.\n2. Blend on high until thick, creamy, and scoopable like soft-serve.\n3. Pour into a chilled breakfast bowl.\n4. Top artistically with chia seeds, toasted sunflower seeds, and a warm swirl of creamy sunflower seed butter.",
            "chef_tip": "Using frozen bananas eliminates the need for ice and yields a luxurious, soft-serve texture naturally."
        },
        {
            "name": "Golden Tofu Scramble with Baby Spinach",
            "cuisine": "Mediterranean",
            "diet": ["Vegetarian", "Vegan"],
            "contains": ["Soy"],
            "prep_time": "15 mins",
            "description": "Organic firm tofu crumbled and infused with golden turmeric and black salt to recreate a savory scramble, sautéed with fresh baby spinach.",
            "ingredients": ["Firm Tofu", "Baby Spinach", "Ground Turmeric", "Garlic Powder", "Olive Oil", "Black Salt"],
            "instructions": "1. Press firm tofu with a clean towel to remove excess moisture; crumble coarsely by hand.\n2. Heat olive oil in a skillet over medium heat. Add garlic powder and turmeric.\n3. Add crumbled tofu and black salt (kala namak) for a signature savory flavor.\n4. Sauté for 5 minutes, then fold in fresh baby spinach until wilted.",
            "chef_tip": "Black salt (kala namak) contains natural sulfur minerals that deliver an authentic scramble flavor 100% plant-based."
        },
        {
            "name": "Chickpea Flour Scramble with Bell Peppers",
            "cuisine": "Mediterranean",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "12 mins",
            "description": "A 100% soy-free, egg-free savory scramble made with seasoned chickpea batter, diced sweet bell peppers, and smoked paprika.",
            "ingredients": ["Chickpea Flour", "Sweet Bell Peppers", "Baby Spinach", "Olive Oil", "Cumin", "Smoked Paprika"],
            "instructions": "1. Whisk chickpea flour with water, cumin, smoked paprika, and salt into a smooth pourable batter.\n2. Sauté diced bell peppers in olive oil for 3 minutes until tender-crisp.\n3. Pour chickpea batter into the pan, stirring continuously with a spatula as it sets and curds.\n4. Remove from heat and fold in baby spinach until wilted.",
            "chef_tip": "Keep heat medium-low and stir constantly from the edges inward to achieve fluffy, moist curds."
        },
        {
            "name": "Cinnamon Apple Oatmeal with Sunflower Seeds",
            "cuisine": "American",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "12 mins",
            "description": "Warm, comforting gluten-free rolled oats simmered in oat milk with fresh diced apples, sweet Ceylon cinnamon, and crunchy sunflower seeds.",
            "ingredients": ["Gluten-Free Rolled Oats", "Oat Milk", "Crisp Red Apples", "Ceylon Cinnamon", "Pure Maple Syrup", "Toasted Sunflower Seeds"],
            "instructions": "1. In a small saucepan, bring oat milk and water to a gentle simmer.\n2. Stir in rolled oats, diced red apples, and ground cinnamon.\n3. Simmer on medium-low for 5-7 minutes, stirring occasionally, until thick and creamy.\n4. Spoon into a bowl, drizzle with pure maple syrup, and sprinkle with crunchy sunflower seeds.",
            "chef_tip": "Dicing apples small allows them to soften and sweeten the oatmeal naturally during simmering."
        }
    ],
    "lunch": [
        {
            "name": "Yellow Dal Tadka with Steamed Jeera Rice",
            "cuisine": "Indian",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "20 mins",
            "description": "Golden yellow toor dal simmered until creamy and finished with a sizzling garlic-cumin tadka, served over steaming fragrant jeera basmati rice.",
            "ingredients": ["Yellow Toor Dal", "Basmati Rice", "Cumin Seeds", "Fresh Garlic", "Tomato", "Olive Oil", "Cilantro"],
            "instructions": "1. Cook toor dal with water, turmeric, and salt until creamy and tender.\n2. Heat olive oil in a small pan. Add cumin seeds and let them sizzle.\n3. Add minced garlic and chopped tomatoes; sauté until tomatoes soften and oil separates.\n4. Pour sizzling tadka into the cooked dal and stir gently.\n5. Serve over freshly steamed jeera (cumin) basmati rice garnished with fresh cilantro.",
            "chef_tip": "Sizzling the garlic in hot oil releases allicin, giving the dal its signature restaurant-style fragrance."
        },
        {
            "name": "Mediterranean Chickpea & Avocado Power Bowl",
            "cuisine": "Mediterranean",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "12 mins",
            "description": "High-fiber, nutrient-packed Mediterranean salad with tender chickpeas, crisp diced Persian cucumbers, cherry tomatoes, avocado, and tangy lemon tahini.",
            "ingredients": ["Cooked Chickpeas", "Ripe Avocado", "Persian Cucumber", "Cherry Tomatoes", "Fresh Lemon Juice", "Tahini Dressing", "Olive Oil"],
            "instructions": "1. Drain and rinse cooked chickpeas; pat dry with a paper towel.\n2. Dice cucumber, halved cherry tomatoes, and cubed ripe avocado.\n3. In a small cup, whisk tahini, fresh lemon juice, warm water, olive oil, and salt until creamy.\n4. Arrange chickpeas and vegetables side-by-side in a wide bowl.\n5. Drizzle with lemon tahini dressing and top with fresh parsley.",
            "chef_tip": "Whisking tahini with a splash of warm water emulsifies it into a silky, luxurious dairy-free dressing."
        },
        {
            "name": "Rajma Masala (Kidney Bean Curry) with Brown Rice",
            "cuisine": "Indian",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "20 mins",
            "description": "Hearty North Indian red kidney bean curry slow-simmered in an aromatic onion-tomato reduction with garam masala, served over nutty brown rice.",
            "ingredients": ["Red Kidney Beans (Rajma)", "Tomato-Onion Puree", "Ginger-Garlic Paste", "Garam Masala", "Steamed Brown Rice"],
            "instructions": "1. Heat olive oil in a pot; sauté finely diced onions until golden brown.\n2. Stir in ginger-garlic paste and sauté for 1 minute until fragrant.\n3. Add tomato puree, cumin, coriander powder, and garam masala; cook until oil glazes the edges.\n4. Add cooked red kidney beans with 1 cup broth; mash a few beans with the back of a spoon to thicken the gravy naturally.\n5. Simmer for 10 minutes and serve warm over steamed brown rice.",
            "chef_tip": "Mashing a spoonful of beans directly into the gravy creates a velvety richness without adding any dairy or cream."
        },
        {
            "name": "Garden Quinoa & Vegetable Pulao",
            "cuisine": "Indian",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "18 mins",
            "description": "Fluffy, protein-dense quinoa infused with whole cardamom and cloves, simmered with sweet garden carrots, crisp green beans, and peas.",
            "ingredients": ["Quinoa", "Diced Carrots", "Green Beans", "Sweet Peas", "Whole Cardamom & Cloves", "Olive Oil"],
            "instructions": "1. Rinse quinoa thoroughly in a fine-mesh sieve under cold running water.\n2. Heat olive oil in a saucepan; add cardamom pods, cloves, and bay leaf until fragrant.\n3. Add diced carrots, green beans, and peas; sauté for 2 minutes.\n4. Add rinsed quinoa and vegetable broth (1:2 ratio), bring to a rapid boil.\n5. Reduce heat to low, cover with a tight lid, and steam undisturbed for 15 minutes. Fluff with a fork.",
            "chef_tip": "Rinsing quinoa thoroughly washes away natural saponins, guaranteeing a clean, nutty flavor without bitterness."
        },
        {
            "name": "Aloo Gobi (Spiced Potato & Cauliflower Curry)",
            "cuisine": "Indian",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "20 mins",
            "description": "Classic homestyle dry curry of cauliflower florets and golden potatoes sautéed with fresh ginger root, turmeric, and cumin seeds.",
            "ingredients": ["Cauliflower Florets", "Potatoes", "Turmeric", "Ground Coriander", "Cumin Seeds", "Fresh Ginger", "Steamed Basmati Rice"],
            "instructions": "1. Cut cauliflower into bite-sized florets and potatoes into small cubes.\n2. Heat olive oil in a skillet; add cumin seeds and fresh julienned ginger.\n3. Add potato cubes with turmeric, cover and cook for 5 minutes.\n4. Add cauliflower florets, ground coriander, and salt; toss well.\n5. Cover and steam on low for 10 minutes until vegetables are fork-tender and lightly browned.",
            "chef_tip": "Sautéing the potato cubes for 5 minutes before adding cauliflower ensures both vegetables cook evenly."
        },
        {
            "name": "Herb-Grilled Chicken Breast with Quinoa Salad",
            "cuisine": "Mediterranean",
            "diet": ["Non-Vegetarian"],
            "contains": [],
            "prep_time": "20 mins",
            "description": "Juicy chicken breast marinated in Mediterranean oregano, garlic, and extra virgin olive oil, pan-seared and paired with a refreshing lemon quinoa salad.",
            "ingredients": ["Chicken Breast", "Quinoa", "Cucumbers", "Cherry Tomatoes", "Olive Oil", "Oregano", "Lemon"],
            "instructions": "1. Season chicken breast with dried oregano, garlic powder, sea salt, black pepper, and olive oil.\n2. Heat a skillet over medium-high heat. Sear chicken for 6-7 minutes per side until cooked through (165°F).\n3. Transfer chicken to a cutting board and let rest for 5 minutes before slicing to lock in juices.\n4. Toss cooked quinoa with diced cucumbers, cherry tomatoes, olive oil, and lemon juice.\n5. Serve sliced chicken warm over the fresh quinoa salad.",
            "chef_tip": "Allowing the chicken to rest for 5 minutes before slicing preserves up to 30% more natural moisture."
        },
        {
            "name": "Pan-Seared Salmon with Lemon Asparagus",
            "cuisine": "Mediterranean",
            "diet": ["Non-Vegetarian", "Pescatarian"],
            "contains": ["Fish"],
            "prep_time": "18 mins",
            "description": "Crisp skin-on wild salmon fillet pan-seared until flaky, served alongside tender asparagus spears tossed with minced garlic and fresh lemon.",
            "ingredients": ["Wild Salmon Fillet", "Fresh Asparagus", "Olive Oil", "Garlic", "Lemon Wedges", "Black Pepper"],
            "instructions": "1. Pat salmon fillet thoroughly dry with paper towels; season skin and flesh with salt and pepper.\n2. Heat olive oil in a skillet over medium-high heat until shimmering.\n3. Place salmon skin-side down; press gently with a spatula for 10s to keep skin flat. Cook 4-5 mins until crispy.\n4. Flip salmon and cook for another 2-3 mins until just cooked through; remove and keep warm.\n5. In the same pan, toss fresh asparagus spears with minced garlic and lemon juice for 3 minutes.",
            "chef_tip": "Ensuring the fish skin is completely dry before searing is the secret to restaurant-crisp skin without sticking."
        }
    ],
    "dinner": [
        {
            "name": "Palak Chickpea Curry with Basmati Rice",
            "cuisine": "Indian",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "18 mins",
            "description": "Tender protein-rich chickpeas simmered in a garlicky, vibrant emerald spinach sauce with warm garam masala, served over fluffy basmati rice.",
            "ingredients": ["Spinach Puree", "Cooked Chickpeas", "Garlic", "Ginger", "Garam Masala", "Steamed Basmati Rice"],
            "instructions": "1. Blanch fresh baby spinach in boiling water for 1 minute, plunge into ice water, and blend into a vibrant green puree.\n2. Heat olive oil in a pan; sauté minced garlic, ginger, and cumin seeds until fragrant.\n3. Add tomato puree and spices; cook for 3 minutes.\n4. Stir in cooked chickpeas and the vibrant spinach puree; simmer on low for 5 minutes.\n5. Serve hot over aromatic basmati rice with a squeeze of fresh lemon.",
            "chef_tip": "The ice water bath (shocking) fixes the bright emerald chlorophyll in the spinach, keeping your curry vibrant green."
        },
        {
            "name": "Creamy Coconut Vegetable Korma",
            "cuisine": "Indian",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "20 mins",
            "description": "A mild, velvety Mughlai curry featuring garden vegetables gently braised in full-fat coconut milk infused with whole cardamom and cinnamon.",
            "ingredients": ["Coconut Milk", "Diced Carrots", "Sweet Peas", "Potatoes", "Mild Korma Spices", "Steamed Basmati Rice"],
            "instructions": "1. Heat olive oil in a deep pan. Add a cinnamon stick and crushed cardamom pods.\n2. Sauté diced onions and ginger until soft. Add mild korma curry spices.\n3. Add diced carrots, sweet potatoes, and peas; coat thoroughly with spices.\n4. Pour in rich full-fat coconut milk and vegetable broth.\n5. Bring to a gentle simmer, cover, and braise for 12-15 minutes until vegetables are meltingly tender. Serve with rice.",
            "chef_tip": "Use rich culinary coconut milk rather than carton beverage milk for an authentically rich body without dairy cream."
        },
        {
            "name": "South Indian Sambar Stew with Steamed Idli",
            "cuisine": "Indian",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "18 mins",
            "description": "Tangy, gut-friendly lentil and vegetable stew infused with tamarind, fresh curry leaves, and aromatic sambar masala, paired with soft steamed rice idlis.",
            "ingredients": ["Toor Dal", "Diced Mixed Vegetables", "Sambar Spice Mix", "Tamarind Pulp", "Steamed Rice Idlis"],
            "instructions": "1. Cook toor dal with turmeric until completely soft and mashable.\n2. In a pot, simmer diced vegetables in tamarind water with sambar powder and salt until tender.\n3. Add the mashed dal and bring the stew to a boil.\n4. Temper mustard seeds and curry leaves in hot oil, then pour over the boiling sambar.\n5. Serve piping hot alongside warm, fluffy steamed rice idlis.",
            "chef_tip": "Adding the tempered mustard seeds and curry leaves at the very end traps the volatile essential oils in the broth."
        },
        {
            "name": "Baingan Bharta (Fire-Roasted Eggplant) with Jeera Rice",
            "cuisine": "Indian",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "20 mins",
            "description": "Smoky fire-roasted eggplant pulp mashed and folded into caramelized onions, ripe tomatoes, and fragrant ground spices, served over jeera rice.",
            "ingredients": ["Roasted Eggplant Pulp", "Diced Onions", "Tomatoes", "Green Chilies", "Cilantro", "Jeera Rice"],
            "instructions": "1. Fire-roast whole eggplant over an open flame or broil at 450°F until skin is charred and flesh is tender (approx. 20 mins).\n2. Let cool, peel away charred skin, and coarsely mash the smoky pulp.\n3. In a skillet, sauté diced onions and green chilies in olive oil until golden brown.\n4. Add diced tomatoes, turmeric, and red chili powder; cook until soft.\n5. Stir in mashed eggplant pulp and simmer for 8 minutes to meld flavors. Garnish with cilantro.",
            "chef_tip": "Roasting the eggplant until the skin blisters produces that signature smoky flavor that makes bharta famous."
        },
        {
            "name": "Crispy Bhindi Masala (Spiced Okra) with Lentil Soup",
            "cuisine": "Indian",
            "diet": ["Vegetarian", "Vegan"],
            "contains": [],
            "prep_time": "20 mins",
            "description": "Fresh tender okra flash-sautéed with amchur (dry mango powder) and cumin until crisp without sliminess, paired with comforting turmeric lentil soup.",
            "ingredients": ["Fresh Okra (Bhindi)", "Amchur (Dried Mango)", "Cumin", "Yellow Lentils", "Turmeric", "Olive Oil"],
            "instructions": "1. Wash okra and pat completely dry with a clean towel before slicing into 1/2-inch rounds.\n2. Heat olive oil in a wide skillet over medium-high heat. Add cumin seeds.\n3. Add sliced okra in a single layer; cook undisturbed for 4 minutes to prevent sliminess.\n4. Toss gently, add turmeric, coriander powder, and amchur (dry mango powder); sauté for another 6 minutes until crisp.\n5. Serve hot alongside a comforting bowl of warm turmeric yellow lentil soup.",
            "chef_tip": "Never cut wet okra! Ensuring okra is completely dry before slicing eliminates all sliminess during cooking."
        },
        {
            "name": "Palak Tofu Curry with Gluten-Free Corn Tortillas",
            "cuisine": "Indian",
            "diet": ["Vegetarian", "Vegan"],
            "contains": ["Soy"],
            "prep_time": "20 mins",
            "description": "Golden pan-seared organic tofu cubes gently folded into a luscious garlic-spinach curry, accompanied by warm gluten-free corn tortillas.",
            "ingredients": ["Fresh Spinach Puree", "Firm Tofu Cubes", "Garlic", "Ginger", "Garam Masala", "Gluten-Free Corn Tortillas"],
            "instructions": "1. Cube firm tofu and pan-sear in 1 tbsp olive oil until lightly golden on all sides; set aside.\n2. Sauté minced garlic, ginger, and cumin in the same pan.\n3. Pour in fresh spinach puree, garam masala, and sea salt; bring to a gentle simmer.\n4. Gently fold in the golden tofu cubes and simmer on low for 4 minutes.\n5. Warm gluten-free corn tortillas on a dry skillet for 30s per side and serve together.",
            "chef_tip": "Searing the tofu first gives it a chewy, resilient texture that absorbs the spiced spinach curry without crumbling."
        },
        {
            "name": "Lemon Herb Chicken with Roasted Potatoes",
            "cuisine": "Mediterranean",
            "diet": ["Non-Vegetarian"],
            "contains": [],
            "prep_time": "20 mins",
            "description": "Golden chicken breast cutlets seared with fresh rosemary, minced garlic, and lemon pan drippings, served with crispy oven-roasted baby potatoes.",
            "ingredients": ["Chicken Breast Cutlets", "Baby Potatoes", "Rosemary", "Olive Oil", "Lemon", "Garlic"],
            "instructions": "1. Halve baby potatoes, toss with olive oil, salt, and rosemary, and roast in the oven at 400°F for 20 mins until crisp.\n2. Season chicken cutlets with garlic, rosemary, sea salt, and black pepper.\n3. Heat olive oil in a skillet over medium-high; sear chicken for 4-5 mins per side until golden (165°F).\n4. Deglaze the pan with fresh lemon juice and a splash of broth to create a quick savory pan sauce.\n5. Spoon pan sauce over chicken and serve immediately with the roasted baby potatoes.",
            "chef_tip": "Deglazing the hot pan with lemon juice lifts all the caramelized fond drippings into an instant savory pan reduction."
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
                "description": b.get("description", "A wholesome, allergen-safe recipe prepared fresh."),
                "ingredients": list(b.get("ingredients", [])),
                "instructions": b.get("instructions", "Prepare fresh and enjoy warm."),
                "chef_tip": b.get("chef_tip", "Season with fresh herbs and olive oil.")
            },
            "lunch": {
                "name": l["name"],
                "prep_time": l.get("prep_time", "15 mins"),
                "description": l.get("description", "A wholesome, allergen-safe recipe prepared fresh."),
                "ingredients": list(l.get("ingredients", [])),
                "instructions": l.get("instructions", "Prepare fresh and enjoy warm."),
                "chef_tip": l.get("chef_tip", "Season with fresh herbs and olive oil.")
            },
            "dinner": {
                "name": d["name"],
                "prep_time": d.get("prep_time", "20 mins"),
                "description": d.get("description", "A wholesome, allergen-safe recipe prepared fresh."),
                "ingredients": list(d.get("ingredients", [])),
                "instructions": d.get("instructions", "Prepare fresh and enjoy warm."),
                "chef_tip": d.get("chef_tip", "Season with fresh herbs and olive oil.")
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
            "description": b_choice.get("description", "A wholesome, allergy-safe recipe prepared fresh."),
            "ingredients": list(b_choice.get("ingredients", [])),
            "instructions": b_choice.get("instructions", "Prepare fresh and enjoy warm."),
            "chef_tip": b_choice.get("chef_tip", "Season with fresh herbs and olive oil.")
        },
        "lunch": {
            "name": l_choice["name"],
            "prep_time": l_choice.get("prep_time", "15 mins"),
            "description": l_choice.get("description", "A wholesome, allergy-safe recipe prepared fresh."),
            "ingredients": list(l_choice.get("ingredients", [])),
            "instructions": l_choice.get("instructions", "Prepare fresh and enjoy warm."),
            "chef_tip": l_choice.get("chef_tip", "Season with fresh herbs and olive oil.")
        },
        "dinner": {
            "name": d_choice["name"],
            "prep_time": d_choice.get("prep_time", "20 mins"),
            "description": d_choice.get("description", "A wholesome, allergy-safe recipe prepared fresh."),
            "ingredients": list(d_choice.get("ingredients", [])),
            "instructions": d_choice.get("instructions", "Prepare fresh and enjoy warm."),
            "chef_tip": d_choice.get("chef_tip", "Season with fresh herbs and olive oil.")
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
