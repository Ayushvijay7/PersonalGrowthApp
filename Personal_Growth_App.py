import streamlit as st
import pandas as pd
import time
import requests
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import date, datetime
import streamlit.components.v1 as components
import data_manager as dm

# --- CONFIGURATION ---
st.set_page_config(page_title="Growth Engine", layout="wide", page_icon="🚀")

# Load CSS
with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

# --- SESSION STATE INITIALIZATION ---
if 'cpa_timer_running' not in st.session_state:
    st.session_state.cpa_timer_running = False
if 'tech_timer_running' not in st.session_state:
    st.session_state.tech_timer_running = False

if 'cpa_start_time' not in st.session_state:
    st.session_state.cpa_start_time = 0
if 'tech_start_time' not in st.session_state:
    st.session_state.tech_start_time = 0

if 'cpa_elapsed' not in st.session_state:
    st.session_state.cpa_elapsed = 0
if 'tech_elapsed' not in st.session_state:
    st.session_state.tech_elapsed = 0

# --- HELPER FUNCTIONS ---
def get_quote(api_key=None):
    # Fallback quotes
    quotes = [
        "The only way to do great work is to love what you do.",
        "Success is not final, failure is not fatal: it is the courage to continue that counts.",
        "Discipline is choosing between what you want now and what you want most."
    ]
    if api_key:
        try:
             # In a real app, use requests.get("https://zenquotes.io/api/today") or similar
             # For now, we return a deterministic quote
             return quotes[date.today().day % len(quotes)]
        except:
            pass
    return quotes[date.today().day % len(quotes)]

def timer_component(key_prefix, label, is_running, elapsed_time):
    st.markdown(f"### {label}")

    # Calculate display time
    current_session = 0
    if is_running:
        current_session = time.time() - st.session_state[f"{key_prefix}_start_time"]

    total_seconds = int(elapsed_time + current_session)
    hours, rem = divmod(total_seconds, 3600)
    mins, secs = divmod(rem, 60)

    # Large Timer Display
    st.markdown(f"""
    <div style="text-align: center; font-size: 3em; font-family: monospace; color: #2c3e50; background: #ecf0f1; border-radius: 10px; padding: 10px;">
        {hours:02d}:{mins:02d}:{secs:02d}
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("▶️ Start", key=f"{key_prefix}_start", disabled=is_running):
            st.session_state[f"{key_prefix}_timer_running"] = True
            st.session_state[f"{key_prefix}_start_time"] = time.time()
            st.rerun()

    with c2:
        if st.button("II Pause", key=f"{key_prefix}_pause", disabled=not is_running):
            st.session_state[f"{key_prefix}_timer_running"] = False
            st.session_state[f"{key_prefix}_elapsed"] += time.time() - st.session_state[f"{key_prefix}_start_time"]
            st.rerun()

    with c3:
        if st.button("🔄 Reset", key=f"{key_prefix}_reset"):
            st.session_state[f"{key_prefix}_timer_running"] = False
            st.session_state[f"{key_prefix}_elapsed"] = 0
            st.rerun()

    if is_running:
        time.sleep(1)
        st.rerun()


# --- SIDEBAR ---
st.sidebar.title("🛠️ Growth Engine")
nav = st.sidebar.radio("Navigate", ["Dashboard", "Recipe Vault", "Grocery List", "Settings"])

if nav == "Dashboard":
    # --- HEADER ---
    quote = get_quote(st.session_state.get('api_key'))
    st.markdown(f"""
    <div class="dashboard-card" style="text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
        <h3>🌟 Quote of the Day</h3>
        <p style="font-size: 1.2em; font-style: italic;">"{quote}"</p>
    </div>
    """, unsafe_allow_html=True)

    # --- METRICS ROW ---
    df = dm.load_audit_data()
    streaks = dm.calculate_streaks(df)

    m1, m2, m3, m4 = st.columns(4)
    with m1: st.metric("CPA Streak", f"{streaks['CPA']} Days")
    with m2: st.metric("Gym Streak", f"{streaks['Gym']} Days")
    with m3: st.metric("Dog Care", f"{streaks['Dog']} Days")
    with m4: st.metric("Tech Upskill", f"{streaks['Tech']} Days")

    st.divider()

    # --- MAIN ACTION AREA ---
    col_timers, col_audit = st.columns([1, 1.5])

    with col_timers:
        st.subheader("⚡ Focus Zone")
        with st.expander("📚 CPA Study Timer", expanded=True):
            timer_component("cpa", "CPA Study", st.session_state.cpa_timer_running, st.session_state.cpa_elapsed)

        with st.expander("💻 Tech AI Upskill", expanded=True):
            timer_component("tech", "Tech AI Study", st.session_state.tech_timer_running, st.session_state.tech_elapsed)

    with col_audit:
        st.subheader("📝 Daily Audit Log")
        with st.form("audit_form"):
            d = st.date_input("Date", date.today())

            # Auto-fill from timers
            cpa_val = round(st.session_state.cpa_elapsed / 3600, 2)
            tech_val = round(st.session_state.tech_elapsed / 3600, 2)

            c1, c2 = st.columns(2)
            with c1:
                cpa_input = st.number_input("CPA Hours", 0.0, 24.0, cpa_val, step=0.5)
                gym_input = st.checkbox("🏋️ Gym / Strength")
                cardio_input = st.checkbox("🏃 Cheeni Walks (Cardio)")
            with c2:
                tech_input = st.number_input("Tech AI Hours", 0.0, 24.0, tech_val, step=0.5)
                dog_walks = st.number_input("🐕 Dog Walks", 0, 5, 2)
                dog_groom = st.checkbox("✂️ Dog Grooming")

            st.markdown("**💊 Supplements & Diet**")
            s1, s2, s3, s4 = st.columns(4)
            with s1: omega = st.checkbox("Omega 3")
            with s2: mag = st.checkbox("Magnesium")
            with s3: vitd = st.checkbox("Vit D3")
            with s4: creat = st.checkbox("Creatine")

            diet = st.checkbox("🥗 Healthy Eating (No Sugar/Fried)")

            if st.form_submit_button("Save Day's Audit"):
                entry = {
                    "Date": str(d),
                    "CPA_Hours": cpa_input,
                    "Tech_AI_Hours": tech_input,
                    "Gym": gym_input,
                    "Cardio": cardio_input,
                    "Dog_Walks": dog_walks,
                    "Dog_Grooming": dog_groom,
                    "Diet_Adherence": diet,
                    "Supp_Omega3": omega,
                    "Supp_Magnesium": mag,
                    "Supp_VitD": vitd,
                    "Supp_Creatine": creat
                }
                dm.save_audit_data(entry)
                st.success("✅ Progress Saved!")

    # --- ANALYTICS SECTION ---
    if not df.empty:
        st.divider()
        st.subheader("📈 Growth Analytics")

        df['Date'] = pd.to_datetime(df['Date'])
        df = df.sort_values('Date')

        # 1. Study Hours Stacked Bar
        st.write("### 📚 Study Hours Distribution")
        study_df = df[['Date', 'CPA_Hours', 'Tech_AI_Hours']].melt('Date', var_name='Type', value_name='Hours')
        fig_bar = px.bar(study_df, x='Date', y='Hours', color='Type', title="Daily Study Hours", barmode='stack')
        st.plotly_chart(fig_bar, use_container_width=True)

        # 2. Habit Heatmap (Simulated with Scatter for now or Heatmap if we pivot)
        st.write("### 🔥 Habit Consistency")

        # Prepare data for heatmap: Date vs Habit
        habit_cols = ['Gym', 'Cardio', 'Diet_Adherence', 'Dog_Walks', 'Dog_Grooming', 'Supp_Omega3']
        # Convert boolean/counts to 1/0 for heatmap intensity
        heatmap_data = []
        for idx, row in df.iterrows():
            d_str = row['Date'].strftime('%Y-%m-%d')
            for habit in habit_cols:
                val = 1 if row[habit] else 0
                if habit == 'Dog_Walks' and row[habit] > 0: val = 1 # Normalize
                heatmap_data.append({'Date': d_str, 'Habit': habit, 'Done': val})

        if heatmap_data:
            hm_df = pd.DataFrame(heatmap_data)
            fig_hm = px.density_heatmap(hm_df, x='Date', y='Habit', z='Done', color_continuous_scale='Greens', title="Habit Heatmap")
            st.plotly_chart(fig_hm, use_container_width=True)

elif nav == "Recipe Vault":
    st.title("👨‍🍳 Healthy Kitchen Vault")
    tab1, tab2 = st.tabs(["Add New Recipe", "Browse Vault"])

    with tab1:
        with st.form("recipe_form"):
            name = st.text_input("Recipe Name")
            tags = st.multiselect("Category", ["High Protein", "Low Carb", "Quick", "Meal Prep"])
            ingredients = st.text_area("Ingredients (One per line, e.g., '2 eggs', '200g chicken')")
            instructions = st.text_area("Steps")
            if st.form_submit_button("Save to Vault"):
                if name and ingredients:
                    dm.save_recipe_data({"Name": name, "Tags": ", ".join(tags), "Ingredients": ingredients, "Instructions": instructions})
                    st.success(f"'{name}' saved!")

    with tab2:
        recipes_df = dm.load_recipe_data()
        if not recipes_df.empty:
            search = st.text_input("🔍 Search", "")
            filtered = recipes_df[recipes_df['Name'].str.contains(search, case=False)]
            for idx, row in filtered.iterrows():
                with st.expander(f"📖 {row['Name']}"):
                    st.write(f"**Category:** {row['Tags']}")
                    st.write("**Ingredients:**")
                    st.write(row['Ingredients'])
                    st.write("**Steps:**")
                    st.write(row['Instructions'])
        else:
            st.info("No recipes found. Add one!")

elif nav == "Grocery List":
    st.title("🛒 Smart Grocery List")
    recipes_df = dm.load_recipe_data()

    if not recipes_df.empty:
        selected = st.multiselect("Plan your meals:", recipes_df['Name'].tolist())
        if selected:
            all_raw_lines = []
            for r in selected:
                items = recipes_df[recipes_df['Name'] == r]['Ingredients'].values[0]
                all_raw_lines.extend([i.strip() for i in str(items).split('\n') if i.strip()])

            # Smart Aggregation
            aggregated_list = dm.aggregate_ingredients(all_raw_lines)

            st.markdown("### Your Consolidated List")
            for item in aggregated_list:
                st.checkbox(item, key=f"shop_{item}")

            st.divider()
            st.caption("Remember: No sugar, no fried food, high carb is a no-go.")
    else:
        st.warning("Add recipes to the vault first!")

elif nav == "Settings":
    st.title("⚙️ Settings")
    st.write("Configure your external integrations here.")
    key = st.text_input("API Key (for Quotes)", type="password", value=st.session_state.get('api_key', ''))
    if key:
        st.session_state['api_key'] = key
        st.success("API Key saved for this session.")
