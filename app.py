import streamlit as st
import time

from data_dictionary import DataManager
from PriceEngine import PriceEngine
from ShoppingProcessor import ShoppingProcessor
from AIService import AIFactory

# -- Config --
st.set_page_config(page_title="AI Chef", page_icon="👨‍🍳", layout="centered")

# -- Auth --
def check_password():
    """Returns `True` if the user had the correct password."""
    if "password_correct" not in st.session_state:
        st.session_state["password_correct"] = False

    if st.session_state["password_correct"]:
        return True

    # Show input for password.
    st.title("👨‍🍳 Smart Supermarkt Assistant")
    st.markdown("Please enter the family PIN to access the app.")
    
    pwd = st.text_input("Enter App PIN", type="password")
    if st.button("Login"):
        # We try to read APP_PIN from secrets, default to "1234" if not set
        expected_pin = "1234"
        try:
            expected_pin = st.secrets.get("APP_PIN", "1234")
        except:
            pass # if secrets.toml is missing or malformed
            
        if pwd == expected_pin:
            st.session_state["password_correct"] = True
            st.rerun()
        else:
            st.error("Incorrect PIN")
    return False

if not check_password():
    st.stop()

# FORCE CLEAR CACHE TO FIX DATA LOADING BUG
st.cache_resource.clear()

# -- Caching Backend --
@st.cache_resource(show_spinner="Initializing Supermarket Data...")
def get_backend():
    data_manager = DataManager()
    price_engine = PriceEngine(data_manager)
    shopping_processor = ShoppingProcessor(data_manager, price_engine)
    return data_manager, price_engine, shopping_processor

data_manager, price_engine, shopping_processor = get_backend()

# -- UI Tabs --
st.title("👨‍🍳 AI Chef")

tab1, tab2, tab3 = st.tabs(["AI Recipe Suggestion", "Modify Recipe", "Manual Shopping List"])

with tab1:
    st.header("Generate a Budget Recipe")
    
    col1, col2 = st.columns(2)
    with col1:
        budget = st.number_input("Budget (€)", min_value=1.0, value=15.0, step=1.0)
        portions = st.number_input("Portions", min_value=1, value=2, step=1)
    with col2:
        cuisine = st.text_input("Cuisine (e.g. Italian, Thai)", value="Italian")
        ai_model = st.selectbox("AI Model", ["Gemini (3.1 Flash-Lite)", "OpenAI (GPT-4o)"])

    # Supermarkets
    st.subheader("Preferred Supermarkets")
    st.caption(f"DEBUG: Dataset length: {len(price_engine.dataset)} | Bonus items: {len(price_engine.bonus_items_keys)} | Error: {price_engine.last_error}")
    
    available_sms = {sm_id: conf.name for sm_id, conf in data_manager.supermarkets.items() if sm_id != "aldi"}
    
    selected_sms_names = st.multiselect(
        "Select supermarkets", 
        options=list(available_sms.values()), 
        default=list(available_sms.values())
    )
    
    selected_sms_ids = [sm_id for sm_id, name in available_sms.items() if name in selected_sms_names]
    
    max_supermarkets = st.number_input("Max Supermarkets to Visit", min_value=1, max_value=max(1, len(available_sms)), value=max(1, len(available_sms)))
    
    partial_list = st.text_area("Optional: Ingredients you already have or want to use (comma separated)")

    if st.button("Generate Bonus Recipe", type="primary"):
        if not selected_sms_ids:
            st.error("Please select at least one supermarket.")
        else:
            with st.spinner("Fetching best discounts and budget staples..."):
                bonus_items = price_engine.get_hybrid_budget_items(selected_sms_ids, limit=20)
                
            st.success(f"Found {len(bonus_items)} budget items!")
            
            # Setup AI
            api_key = ""
            if "OpenAI" in ai_model:
                api_key = st.secrets["OPENAI_API_KEY"]
            else:
                api_key = st.secrets["GEMINI_API_KEY"]
                
            if not api_key:
                st.error(f"Missing API Key for {ai_model} in `.streamlit/secrets.toml`.")
            else:
                try:
                    from AIService import OpenAIService, GeminiService
                    if "OpenAI" in ai_model:
                        ai_service = OpenAIService(api_key)
                    else:
                        ai_service = GeminiService(api_key)
                except Exception as e:
                    st.error(f"Failed to initialize AI: {e}")
                    st.stop()
                
            partial_items = [i.strip() for i in partial_list.split(",")] if partial_list else []
            
            with st.chat_message("assistant"):
                st.markdown("Cooking up your recipe...")
                generator = ai_service.suggest_recipe_by_budget(
                    budget=budget, 
                    portions=portions, 
                    partial_list=partial_items, 
                    cuisine=cuisine, 
                    bonus_items=list(set(bonus_items)),
                    max_supermarkets=int(max_supermarkets)
                )
                
                recipe_text = st.write_stream(generator)
                st.session_state["last_recipe"] = recipe_text
                
                # Generate PDF immediately in background
                from PDFGenerator import PDFGenerator
                try:
                    pdf_gen = PDFGenerator()
                    pdf_path = pdf_gen.generate_recipe_pdf(recipe_text)
                    with open(pdf_path, "rb") as f:
                        st.session_state["recipe_pdf"] = f.read()
                except Exception as e:
                    st.error(f"Could not generate PDF: {e}")

    if "recipe_pdf" in st.session_state:
        st.download_button("📥 Download Recipe as PDF", st.session_state["recipe_pdf"], file_name="budget_recipe.pdf", mime="application/pdf")

with tab2:
    st.header("Modify Last Recipe")
    if "last_recipe" not in st.session_state:
        st.info("Generate a recipe first before modifying.")
    else:
        st.markdown("**Original Recipe Preview:**")
        with st.expander("Show Original Recipe"):
            st.markdown(st.session_state["last_recipe"])
            
        modification = st.text_area("What do you want to change? (e.g. 'Make it vegetarian', 'Replace chicken with tofu')")
        
        if st.button("Modify Recipe", type="primary"):
            if modification:
                ai_type = "openai" if "OpenAI" in ai_model else "gemini"
                if "OpenAI" in ai_model:
                    api_key = st.secrets["OPENAI_API_KEY"]
                else:
                    api_key = st.secrets["GEMINI_API_KEY"]
                    
                if not api_key:
                    st.error(f"Missing API Key for {ai_model} in `.streamlit/secrets.toml`.")
                    st.stop()
                    
                from AIService import OpenAIService, GeminiService
                if "OpenAI" in ai_model:
                    ai_service = OpenAIService(api_key)
                else:
                    ai_service = GeminiService(api_key)
                
                with st.chat_message("assistant"):
                    generator = ai_service.modify_recipe(
                        original_recipe=st.session_state["last_recipe"],
                        modification_prompt=modification,
                        shopping_list=[]
                    )
                    new_recipe = st.write_stream(generator)
                    st.session_state["last_recipe"] = new_recipe
                    
                    from PDFGenerator import PDFGenerator
                    try:
                        pdf_gen = PDFGenerator()
                        pdf_path = pdf_gen.generate_recipe_pdf(new_recipe)
                        with open(pdf_path, "rb") as f:
                            st.session_state["mod_recipe_pdf"] = f.read()
                    except Exception as e:
                        st.error(f"Could not generate PDF: {e}")

        if "mod_recipe_pdf" in st.session_state:
            st.download_button("📥 Download Modified Recipe as PDF", st.session_state["mod_recipe_pdf"], file_name="budget_recipe.pdf", mime="application/pdf")

with tab3:
    st.header("✨ AI Parser Shopping List")
    st.write("Paste your raw, messy grocery list or recipe ingredients. The AI will parse it and calculate the cheapest supermarket!")
    
    # Session state for two-step workflow
    if "parsed_items" not in st.session_state:
        st.session_state["parsed_items"] = []
    if "calc_results" not in st.session_state:
        st.session_state["calc_results"] = None
        
    raw_list = st.text_area("Paste your list here:")
    
    if st.button("Parse List", type="secondary", key="parse_list_btn"):
        if not raw_list.strip():
            st.warning("Please paste a list first.")
        else:
            api_key = ""
            if "OpenAI" in ai_model:
                api_key = st.secrets.get("OPENAI_API_KEY", "")
            else:
                api_key = st.secrets.get("GEMINI_API_KEY", "")
                
            if not api_key:
                st.error(f"Missing API Key for {ai_model} in `.streamlit/secrets.toml`.")
            else:
                try:
                    from AIService import OpenAIService, GeminiService
                    if "OpenAI" in ai_model:
                        ai_service = OpenAIService(api_key)
                    else:
                        ai_service = GeminiService(api_key)
                        
                    with st.spinner(f"Parsing list using {ai_model}..."):
                        parsed_list = ai_service.parse_free_text_list(raw_list, data_manager)
                        
                        # Register DYNAMIC items into DataManager
                        if parsed_list:
                            from data_dictionary import Ingredient, IngredientTranslation, Category, Unit
                            for i in parsed_list:
                                ing_id = i.get("id")
                                if ing_id and ing_id.startswith("DYNAMIC:"):
                                    dutch_name = ing_id.split(":", 1)[1].strip()
                                    new_id = f"dynamic_{dutch_name.replace(' ', '_').lower()}"
                                    i["id"] = new_id # Replace the ID in the parsed list
                                    
                                    if new_id not in data_manager.ingredients:
                                        dyn_ing = Ingredient(
                                            id=new_id,
                                            translations=IngredientTranslation(dutch_name, dutch_name, dutch_name, dutch_name),
                                            category=Category.PANTRY,
                                            expected_unit=Unit.PIECE,
                                            default_variant=dutch_name,
                                            default_brand_preference="cheapest",
                                            available_variants=[dutch_name],
                                            tags=[]
                                        )
                                        data_manager.ingredients[new_id] = dyn_ing
                        
                        st.session_state["parsed_items"] = parsed_list
                        st.session_state["calc_results"] = None # Reset calculations
                except Exception as e:
                    st.error(f"AI Parsing failed: {e}")
                    st.session_state["parsed_items"] = []

    # Stage 1: Edit Parsed Items
    if st.session_state["parsed_items"]:
        st.subheader("1. Review and Edit Ingredients")
        st.caption("Fix any mistakes or adjust quantities before calculating the route.")
        
        # Format for data_editor
        edit_data = []
        for i in st.session_state["parsed_items"]:
            ing_id = i.get("id", "")
            unit_str = "piece"
            if not ing_id.startswith("DYNAMIC:"):
                ing_obj = data_manager.get_ingredient(ing_id)
                if ing_obj:
                    unit_str = ing_obj.expected_unit.value
            edit_data.append({"Ingredient ID": ing_id, "Amount": float(i.get("amount", 1)), "Unit (e.g. g, ml, piece)": unit_str})
            
        import pandas as pd
        edited_df = st.data_editor(
            pd.DataFrame(edit_data),
            num_rows="dynamic",
            use_container_width=True,
            disabled=("Unit (e.g. g, ml, piece)",) # Don't let them edit the unit directly, it's just for display
        )
        
        st.subheader("2. Compare Supermarkets")
        available_sms = {sm_id: conf.name for sm_id, conf in data_manager.supermarkets.items()}
        manual_sms_names = st.multiselect(
            "Select supermarkets to compare", 
            options=list(available_sms.values()), 
            default=list(available_sms.values()),
            key="manual_sms_select"
        )
        manual_sms_ids = [sm_id for sm_id, name in available_sms.items() if name in manual_sms_names]
        
        if st.button("Calculate Route", type="primary", key="calc_prices"):
            if not manual_sms_ids:
                st.warning("Please select at least one supermarket.")
            elif edited_df.empty:
                st.warning("Your ingredient list is empty.")
            else:
                raw_items = edited_df["Ingredient ID"].tolist()
                raw_amounts = dict(zip(edited_df["Ingredient ID"], edited_df["Amount"]))
                
                items = []
                amounts = {}
                from data_dictionary import Ingredient, IngredientTranslation, Category, Unit
                
                for item_id in raw_items:
                    clean_id = item_id
                    if item_id.startswith("DYNAMIC:"):
                        dutch_name = item_id.split(":", 1)[1].strip()
                        clean_id = f"dynamic_{dutch_name.replace(' ', '_').lower()}"
                        
                        if clean_id not in data_manager.ingredients:
                            dyn_ing = Ingredient(
                                id=clean_id,
                                translations=IngredientTranslation(dutch_name, dutch_name, dutch_name, dutch_name),
                                category=Category.PANTRY,
                                expected_unit=Unit.PIECE,
                                default_variant=dutch_name,
                                default_brand_preference="cheapest",
                                available_variants=[dutch_name],
                                tags=[]
                            )
                            data_manager.ingredients[clean_id] = dyn_ing
                    
                    items.append(clean_id)
                    amounts[clean_id] = raw_amounts[item_id]
                
                with st.spinner("Calculating prices across supermarkets..."):
                    results = shopping_processor.process_shopping_list(items, amounts, manual_sms_ids)
                    st.session_state["calc_results"] = results
                    st.rerun()

    # Stage 2: View and Override Results
    if st.session_state["calc_results"]:
        results = st.session_state["calc_results"]
        if not results or not results.get("items"):
            st.error("Could not find prices for these items.")
        else:
            st.subheader("3. Final Shopping Route")
            
            # Recalculate total cost based on active selections
            total_cost = sum(item["total_price"] for item in results["items"])
            st.success(f"🏆 Optimal Shopping Route: **€{total_cost:.2f}**")
            
            auto_snap = st.checkbox("Auto-snap all other items to the same supermarket when I change a brand", value=True)
            
            # Helper function for dropdown changes
            def override_item(item_idx, selected_alt_str):
                # Find the alternative in the list
                item = st.session_state["calc_results"]["items"][item_idx]
                target_sm = None
                
                for alt in item["alternatives"]:
                    alt_str = f"{alt['name']} ({alt['unit_size']}) - €{alt['price']} [{data_manager.get_supermarket(alt['supermarket']).name}]"
                    if alt_str == selected_alt_str:
                        target_sm = alt["supermarket"]
                        # Override the optimal choice with this alternative
                        item["name"] = alt["name"]
                        item["price"] = alt["price"]
                        item["supermarket"] = alt["supermarket"]
                        item["is_bonus"] = alt["is_bonus"]
                        
                        # Recalculate packages needed for the new alternative size
                        import math
                        package_size = alt.get("parsed_amount", 1.0)
                        if item.get("expected_unit") in ["g", "ml"] and alt.get("natural_unit") in ["KG", "L"]:
                            package_size = package_size * 1000.0
                            
                        qty = float(item.get("amount", 1.0))
                        new_packages = math.ceil(qty / package_size) if package_size > 0 else 1
                        
                        item["packages_needed"] = new_packages
                        item["total_price"] = alt["price"] * new_packages
                        break
                        
                if auto_snap and target_sm:
                    # Snap all OTHER items to this target_sm
                    import math
                    for other_idx, other_item in enumerate(st.session_state["calc_results"]["items"]):
                        if other_idx == item_idx:
                            continue
                            
                        best_alt = None
                        for other_alt in other_item["alternatives"]:
                            if other_alt["supermarket"] == target_sm:
                                if best_alt is None or other_alt["unit_price"] < best_alt["unit_price"]:
                                    best_alt = other_alt
                                    
                        if best_alt:
                            other_item["name"] = best_alt["name"]
                            other_item["price"] = best_alt["price"]
                            other_item["supermarket"] = best_alt["supermarket"]
                            other_item["is_bonus"] = best_alt["is_bonus"]
                            
                            p_size = best_alt.get("parsed_amount", 1.0)
                            if other_item.get("expected_unit") in ["g", "ml"] and best_alt.get("natural_unit") in ["KG", "L"]:
                                p_size = p_size * 1000.0
                                
                            qty = float(other_item.get("amount", 1.0))
                            n_pkg = math.ceil(qty / p_size) if p_size > 0 else 1
                            other_item["packages_needed"] = n_pkg
                            other_item["total_price"] = best_alt["price"] * n_pkg
            
            # Display items with dropdowns for alternatives
            items_by_sm = {}
            for idx, item in enumerate(results.get("items", [])):
                sm = item["supermarket"]
                if sm not in items_by_sm:
                    items_by_sm[sm] = []
                items_by_sm[sm].append((idx, item))
                
            for sm_id, sm_items in items_by_sm.items():
                sm_name = data_manager.get_supermarket(sm_id).name if data_manager.get_supermarket(sm_id) else sm_id
                sm_total = sum(i["total_price"] for _, i in sm_items)
                
                with st.expander(f"🛒 {sm_name}: €{sm_total:.2f} ({len(sm_items)} items)", expanded=True):
                    for idx, item in sm_items:
                        bonus_str = "🎁 " if item.get("is_bonus") else ""
                        
                        # Build options string
                        options = []
                        current_val = None
                        for alt in item["alternatives"]:
                            alt_sm_name = data_manager.get_supermarket(alt["supermarket"]).name
                            alt_str = f"{alt['name']} ({alt['unit_size']}) - €{alt['price']} [{alt_sm_name}]"
                            options.append(alt_str)
                            
                            if alt["name"] == item["name"] and alt["supermarket"] == item["supermarket"] and alt["price"] == item["price"]:
                                current_val = alt_str
                                
                        if not current_val and options:
                            current_val = options[0]
                            
                        selected = st.selectbox(
                            f"{bonus_str}{item['amount']}x {item['ingredient_id']} (Needs {item['packages_needed']} packages)", 
                            options=options, 
                            index=options.index(current_val) if current_val in options else 0,
                            key=f"alt_{idx}"
                        )
                        
                        if selected != current_val:
                            override_item(idx, selected)
                            st.rerun()
                            
            if results.get("missing_items"):
                st.warning(f"Could not find these items in any selected supermarket: {', '.join(results['missing_items'])}")
