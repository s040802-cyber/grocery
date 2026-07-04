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
        ai_model = st.selectbox("AI Model", ["OpenAI (GPT-4o)", "Gemini (3.5 Flash)"])

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
    
    raw_list = st.text_area("Paste your list here:")
    
    st.subheader("Compare Supermarkets")
    available_sms = {sm_id: conf.name for sm_id, conf in data_manager.supermarkets.items()}
    manual_sms_names = st.multiselect(
        "Select supermarkets to compare", 
        options=list(available_sms.values()), 
        default=list(available_sms.values()),
        key="manual_sms_select"
    )
    
    manual_sms_ids = [sm_id for sm_id, name in available_sms.items() if name in manual_sms_names]
    
    if st.button("Parse & Calculate", type="primary", key="calc_prices"):
        if not raw_list.strip():
            st.warning("Please paste a list first.")
        elif not manual_sms_ids:
            st.warning("Please select at least one supermarket.")
        else:
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
                        
                    with st.spinner(f"Parsing list using {ai_model}..."):
                        parsed_list = ai_service.parse_free_text_list(raw_list, data_manager)
                except Exception as e:
                    st.error(f"AI Parsing failed: {e}")
                    parsed_list = []
                        
                if parsed_list:
                    items = [i.get("id") for i in parsed_list if "id" in i]
                    amounts = {i.get("id"): i.get("amount", 1) for i in parsed_list if "id" in i}
                    
                    st.success(f"Parsed {len(items)} items: {', '.join(items)}")
                    
                    with st.spinner("Calculating prices across supermarkets..."):
                        results = shopping_processor.process_shopping_list(items, amounts, manual_sms_ids)
                        
                    if not results or not results.get("items"):
                        st.error("Could not find prices for these items.")
                    else:
                        total_cost = results.get('total_cost', 0)
                        st.success(f"🏆 Optimal Shopping Route: **€{total_cost:.2f}**")
                        
                        items_by_sm = {}
                        for item in results.get("items", []):
                            sm = item["supermarket"]
                            if sm not in items_by_sm:
                                items_by_sm[sm] = []
                            items_by_sm[sm].append(item)
                            
                        for sm_id, sm_items in items_by_sm.items():
                            sm_name = data_manager.get_supermarket(sm_id).name if data_manager.get_supermarket(sm_id) else sm_id
                            sm_total = sum(i["total_price"] for i in sm_items)
                            with st.expander(f"🛒 {sm_name}: €{sm_total:.2f} ({len(sm_items)} items)", expanded=True):
                                for item in sm_items:
                                    bonus_str = "🎁 BONUS " if item.get("is_bonus") else ""
                                    st.markdown(f"- **{item['name']}** (x{item['packages_needed']}): {bonus_str}€{item['total_price']:.2f}")
                                    
                        if results.get("missing_items"):
                            st.warning(f"Could not find these items in any selected supermarket: {', '.join(results['missing_items'])}")
