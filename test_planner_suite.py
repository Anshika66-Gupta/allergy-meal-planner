"""
test_planner_suite.py - Comprehensive Unit & Integration Test Suite for Allergy-Safe Meal Planner
"""

import sys
import planner

def run_tests():
    print("🧪 Running Comprehensive Test Suite...")
    passed = 0
    total = 0

    def assert_test(cond, name):
        nonlocal passed, total
        total += 1
        if cond:
            print(f"  ✅ PASS: {name}")
            passed += 1
        else:
            print(f"  ❌ FAIL: {name}")
            sys.exit(1)

    # Test 1: Model check is non-blocking and returns list
    models = planner.get_available_models()
    assert_test(isinstance(models, list), "get_available_models returns a list")

    # Test 2: Peanut and Dairy substitution separation (No cascade corruption)
    sample_plan = {
        "days": [{
            "day": "Monday",
            "breakfast": {
                "name": "Peanut Butter Toast with Butter",
                "ingredients": ["Peanut butter", "Dairy butter", "Whole wheat bread", "Sunflower seed butter", "Oat milk"]
            },
            "lunch": {
                "name": "Shrimp & Crab Salad",
                "ingredients": ["Shrimp", "Crab", "Mayonnaise"]
            },
            "dinner": {
                "name": "Paneer Makhani",
                "ingredients": ["Paneer", "Heavy cream", "Cashew paste"]
            }
        }]
    }

    sanitized = planner.verify_allergen_safety(
        sample_plan, 
        ["Peanuts", "Dairy", "Gluten", "Shellfish", "Eggs", "Tree Nuts"]
    )
    b_ing = sanitized["days"][0]["breakfast"]["ingredients"]
    l_ing = sanitized["days"][0]["lunch"]["ingredients"]
    d_ing = sanitized["days"][0]["dinner"]["ingredients"]

    assert_test("Sunflower seed butter" in b_ing, "Sunflower seed butter preserved without dairy conversion")
    assert_test("Oat milk" in b_ing, "Oat milk preserved without dairy conversion")
    assert_test(not any("peanut" in i.lower() for i in b_ing), "Peanut butter eliminated from ingredients")
    assert_test(not any("shrimp" in i.lower() or "crab" in i.lower() for i in l_ing), "Shellfish eliminated from ingredients")
    assert_test(not any("paneer" in i.lower() or "cream" in i.lower() or "cashew" in i.lower() for i in d_ing), "Dairy and cashew eliminated from dinner")

    # Test 3: Audit Log Accuracy
    audit = sanitized.get("audit_summary", {})
    assert_test(audit.get("safe") is True, "Audit log reports 100% safe")
    assert_test(audit.get("violations_caught", 0) > 0, f"Audit caught {audit.get('violations_caught')} violations")
    assert_test(isinstance(audit.get("details"), list), "Audit details list populated")

    # Test 4: Shopping list sanitization and deduplication
    shop = sanitized.get("shopping_list", [])
    assert_test(len(shop) > 0, "Shopping list populated")
    assert_test(not any("peanut" in s.lower() for s in shop), "No peanuts in shopping list")
    assert_test(not any("shrimp" in s.lower() for s in shop), "No shellfish in shopping list")
    assert_test(shop == sorted(shop, key=str.lower), "Shopping list is sorted alphabetically")

    # Test 5: Aisle Categorization
    aisles = planner.generate_categorized_shopping_list(shop)
    assert_test("🥬 Produce & Fresh Herbs" in aisles, "Produce aisle exists")
    assert_test("🍗 Meat, Fish & Plant Proteins" in aisles, "Protein aisle exists")
    assert_test("🥛 Dairy & Milk Alternatives" in aisles, "Dairy alternatives aisle exists")
    assert_test("🌾 Grains, Pastas & Bakery" in aisles, "Grains aisle exists")

    # Test 6: Anny's 7-Day Plan Generation
    anny_plan = planner.generate_meal_plan(
        allergies=planner.DEFAULT_FRIEND["allergies"],
        preferences=planner.DEFAULT_FRIEND["preferences"],
        days=7
    )
    assert_test(len(anny_plan["days"]) == 7, "Generated exactly 7 days for Anny")
    
    # Check that mushrooms and forbidden allergens are absent across all 7 days
    all_meal_text = " ".join([
        d["breakfast"]["name"] + " " + " ".join(d["breakfast"]["ingredients"]) + " " +
        d["lunch"]["name"] + " " + " ".join(d["lunch"]["ingredients"]) + " " +
        d["dinner"]["name"] + " " + " ".join(d["dinner"]["ingredients"])
        for d in anny_plan["days"]
    ]).lower()

    assert_test("mushroom" not in all_meal_text, "Anny's dislike (mushrooms) respected across all 7 days")
    assert_test("peanut" not in all_meal_text, "Peanuts absent across all 7 days")
    assert_test("shrimp" not in all_meal_text, "Shellfish absent across all 7 days")

    # Test 7: Single Day Regeneration guarantees a different meal
    monday_orig_breakfast = anny_plan["days"][0]["breakfast"]["name"]
    regen_monday = planner.regenerate_single_day(
        allergies=planner.DEFAULT_FRIEND["allergies"],
        preferences=planner.DEFAULT_FRIEND["preferences"],
        day_label="Monday",
        existing_day_meals=[monday_orig_breakfast]
    )
    assert_test(regen_monday["day"] == "Monday", "Regenerated day retains day label Monday")
    assert_test(regen_monday["breakfast"]["name"] != monday_orig_breakfast, "Regenerated day provides a new meal")

    # Test 8: Preference Scoring (Chicken & Mediterranean)
    med_plan = planner.generate_meal_plan(
        allergies=["Peanuts"],
        preferences="Mediterranean, loves chicken breast",
        days=3
    )
    lunch_name = med_plan["days"][0]["lunch"]["name"]
    assert_test("chicken" in lunch_name.lower(), f"Non-veg preference honored: {lunch_name}")

    # Test 9: Malformed JSON Repair
    malformed_json = '''
    ```json
    {
      "days": [
        {
          "day": "Monday",
          "breakfast": "Oatmeal with berries",
          "lunch": {"name": "Lentil Soup", "ingredients": ["Lentils", "Carrots"], "prep_time": "15 mins", "instructions": "Boil"},
          "dinner": {"name": "Veggie Stir Fry", "ingredients": ["Tofu", "Broccoli"], "prep_time": "20 mins", "instructions": "Stir fry"}
        }
      ],
      "shopping_list": ["Oatmeal", "Berries", "Lentils", "Carrots", "Tofu", "Broccoli",]
    }
    ```
    '''
    parsed = planner.parse_and_validate_json(malformed_json)
    assert_test(isinstance(parsed["days"][0]["breakfast"], dict), "String meal normalized to dict")
    assert_test(parsed["days"][0]["breakfast"]["name"] == "Oatmeal with berries", "Normalized meal preserves title")
    assert_test(len(parsed["shopping_list"]) == 6, "Trailing comma in JSON repaired")

    # Test 10: PDF Export Generation
    import pdf_export
    shop_pdf = pdf_export.generate_shopping_list_pdf("Anny", ["Peanuts", "Dairy"], aisles, checked_items={"Fresh Spinach"})
    assert_test(isinstance(shop_pdf, bytes) and len(shop_pdf) > 1000, "Grocery list PDF generated successfully")
    assert_test(shop_pdf.startswith(b"%PDF"), "Grocery list PDF starts with standard %PDF header")

    plan_pdf = pdf_export.generate_meal_plan_pdf("Anny", ["Peanuts", "Dairy"], "Vegetarian", anny_plan)
    assert_test(isinstance(plan_pdf, bytes) and len(plan_pdf) > 1000, "Meal plan PDF generated successfully")
    assert_test(plan_pdf.startswith(b"%PDF"), "Meal plan PDF starts with standard %PDF header")

    print(f"\n🎉 ALL {total} TESTS PASSED CLEANLY! (100% SUCCESS)")

if __name__ == "__main__":
    run_tests()

