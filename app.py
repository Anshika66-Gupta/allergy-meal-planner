"""
app.py - Clean & Friendly Streamlit UI for Allergy-Safe Meal Planner
"""

import streamlit as st
import planner

# Streamlit Page Config
st.set_page_config(
    page_title="Meal Planner for Anny",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling
st.markdown("""
<style>
    .stApp {
        background-color: #0F172A;
        color: #F8FAFC;
        font-family: 'Inter', system-ui, -apple-system, sans-serif;
    }
    .header-box {
        background: linear-gradient(135deg, #1E293B 0%, #0F172A 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 24px;
    }
    .welcome-msg {
        background-color: #064E3B;
        color: #34D399;
        border: 1px solid #059669;
        padding: 10px 16px;
        border-radius: 8px;
        font-size: 1rem;
        font-weight: 600;
        margin-top: 12px;
        display: block;
    }
    .badge-tag {
        background-color: #450A0A;
        color: #FCA5A5;
        border: 1px solid #991B1B;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 0.85rem;
        font-weight: 600;
        margin-right: 6px;
        display: inline-block;
    }
    .badge-offline {
        background-color: #064E3B;
        color: #34D399;
        border: 1px solid #059669;
        padding: 4px 10px;
        border-radius: 8px;
        font-size: 0.85rem;
        font-weight: 600;
        float: right;
    }
    .meal-box {
        background-color: #1E293B;
        border-radius: 10px;
        padding: 16px;
        height: 100%;
        border-left: 4px solid #3B82F6;
        margin-bottom: 12px;
    }
    .meal-box.breakfast { border-left-color: #F59E0B; }
    .meal-box.lunch { border-left-color: #10B981; }
    .meal-box.dinner { border-left-color: #6366F1; }
</style>
""", unsafe_allow_html=True)

# Initialize Session State
if "meal_plan" not in st.session_state:
    st.session_state.meal_plan = None

# Sidebar Controls pre-configured for Anny
st.sidebar.title("👤 Friend & Diet Setup")

friend_name = st.sidebar.text_input(
    "Friend's Name", 
    value=planner.DEFAULT_FRIEND["name"]
)

# Multiselect presets + custom text input
allergy_presets = ["Peanuts", "Tree Nuts", "Shellfish", "Dairy", "Gluten", "Eggs", "Soy"]
selected_allergies = st.sidebar.multiselect(
    "Select Allergies",
    options=allergy_presets,
    default=planner.DEFAULT_FRIEND["allergies"]
)

custom_allergies_text = st.sidebar.text_input(
    "Additional Allergies (comma-separated)",
    value=""
)

# Combine allergies
allergies_list = list(selected_allergies)
if custom_allergies_text:
    for extra in custom_allergies_text.split(","):
        clean_extra = extra.strip()
        if clean_extra and clean_extra not in allergies_list:
            allergies_list.append(clean_extra)

preferences = st.sidebar.text_area(
    "Dietary Preferences",
    value=planner.DEFAULT_FRIEND["preferences"],
    height=100
)

num_days = st.sidebar.slider(
    "Number of Days",
    min_value=1,
    max_value=7,
    value=planner.DEFAULT_FRIEND["days"]
)

# Model / Engine selector
available_models = planner.get_available_models()
if available_models:
    selected_model = st.sidebar.selectbox("Model Engine", options=available_models, index=0)
    badge_label = f"🟢 Local Gemma ({selected_model})"
else:
    selected_model = "gemma3:1b"
    st.sidebar.info("🟢 Allergy Guard Engine (Cloud Mode)")
    badge_label = "🟢 100% Safe (Cloud Mode)"

# Big Generate Plan Button
generate_btn = st.sidebar.button("✨ Generate Plan", type="primary", use_container_width=True)

# Allergies String for Welcome Message
allergies_text_str = ", ".join(allergies_list) if allergies_list else "allergies"

# Personal Header with Welcome Message
st.markdown(f"""
<div class="header-box">
    <span class="badge-offline">{badge_label}</span>
    <h1 style="margin: 0; color: #F8FAFC;">🥗 Meal Planner for {friend_name}</h1>
    <div class="welcome-msg">
        ❤️ Built especially for {friend_name} so you never have to worry about {allergies_text_str} again.
    </div>
    <div style="margin-top: 14px;">
        <strong>Strict Exclusions:</strong> 
        {' '.join([f'<span class="badge-tag">🚫 {a}</span>' for a in allergies_list]) if allergies_list else '<span>None</span>'}
    </div>
</div>
""", unsafe_allow_html=True)

# Handle Plan Generation
if generate_btn:
    with st.spinner(f"🤖 Generating {num_days}-day meal plan for {friend_name}..."):
        try:
            plan = planner.generate_meal_plan(
                allergies=allergies_list,
                preferences=preferences,
                days=num_days,
                model_name=selected_model
            )
            st.session_state.meal_plan = plan
            st.success(f"🎉 Created a {num_days}-day meal plan for {friend_name}!")
        except Exception as e:
            st.error(f"⚠️ {str(e)}")

# Display Meal Plan Day by Day
if st.session_state.meal_plan:
    plan = st.session_state.meal_plan
    days = plan.get("days", [])
    
    st.subheader(f"📅 {friend_name}'s Weekly Plan ({len(days)} Days)")
    
    for idx, day in enumerate(days):
        day_label = day.get("day", f"Day {idx + 1}")
        
        with st.expander(f"🗓️ {day_label}", expanded=(idx == 0)):
            col1, col2, col3 = st.columns(3)
            
            # Breakfast
            with col1:
                b = day.get("breakfast", {})
                st.markdown(f"""
                <div class="meal-box breakfast">
                    <h4 style="margin: 0 0 8px 0; color: #F59E0B;">🥣 Breakfast</h4>
                    <strong style="font-size: 1.05rem; color: #F8FAFC;">{b.get('name', 'Breakfast')}</strong>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("**Ingredients:**")
                for ing in b.get("ingredients", []):
                    st.write(f"- {ing}")
                if b.get("instructions"):
                    st.caption(f"**Instructions:** {b.get('instructions')}")

            # Lunch
            with col2:
                l = day.get("lunch", {})
                st.markdown(f"""
                <div class="meal-box lunch">
                    <h4 style="margin: 0 0 8px 0; color: #10B981;">🥗 Lunch</h4>
                    <strong style="font-size: 1.05rem; color: #F8FAFC;">{l.get('name', 'Lunch')}</strong>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("**Ingredients:**")
                for ing in l.get("ingredients", []):
                    st.write(f"- {ing}")
                if l.get("instructions"):
                    st.caption(f"**Instructions:** {l.get('instructions')}")

            # Dinner
            with col3:
                d = day.get("dinner", {})
                st.markdown(f"""
                <div class="meal-box dinner">
                    <h4 style="margin: 0 0 8px 0; color: #6366F1;">🍲 Dinner</h4>
                    <strong style="font-size: 1.05rem; color: #F8FAFC;">{d.get('name', 'Dinner')}</strong>
                </div>
                """, unsafe_allow_html=True)
                st.markdown("**Ingredients:**")
                for ing in d.get("ingredients", []):
                    st.write(f"- {ing}")
                if d.get("instructions"):
                    st.caption(f"**Instructions:** {d.get('instructions')}")

            st.markdown("<br>", unsafe_allow_html=True)
            
            # Regenerate Single Day Button
            if st.button(f"🔄 Regenerate {day_label}", key=f"regen_{idx}"):
                with st.spinner(f"Regenerating {day_label} for {friend_name}..."):
                    new_day = planner.regenerate_single_day(
                        allergies=allergies_list,
                        preferences=preferences,
                        day_label=day_label,
                        model_name=selected_model
                    )
                    st.session_state.meal_plan["days"][idx] = new_day
                    st.session_state.meal_plan = planner.update_shopping_list(st.session_state.meal_plan)
                    st.toast(f"Updated {day_label}!", icon="✨")
                    st.rerun()

    # Shopping List at the Bottom (Copyable)
    st.markdown("---")
    st.subheader(f"🛒 Consolidated Shopping List for {friend_name}")
    st.caption("Consolidated list of all required ingredients across all days (click copy icon at top right of box).")
    
    shopping_items = plan.get("shopping_list", [])
    if shopping_items:
        formatted_list = f"=== Weekly Shopping List for {friend_name} ===\n" + "\n".join([f"- {item}" for item in shopping_items])
        st.code(formatted_list, language="markdown")
    else:
        st.info("No shopping list items available.")

else:
    st.info(f"👈 Customize {friend_name}'s allergies and preferences in the sidebar, then click **'Generate Plan'**!")
