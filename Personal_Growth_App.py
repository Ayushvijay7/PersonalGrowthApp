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
import ai_utils
import io

# --- CONFIGURATION ---
st.set_page_config(page_title="Growth Engine", layout="wide", page_icon="🚀")

# Load CSS
import os
css_path = os.path.join(os.path.dirname(__file__), "style.css")
if os.path.exists(css_path):
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
else:
    st.warning("style.css not found. UI may look different.")

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
if 'api_key' not in st.session_state:
    st.session_state.api_key = ""

# --- HELPER FUNCTIONS ---
def get_quote(api_key=None):
    # Fallback quotes
    quotes = [
        "The only way to do great work is to love what you do.",
        "Success is not final, failure is not fatal: it is the courage to continue that counts.",
        "Discipline is choosing between what you want now and what you want most."
    ]
    # Simple logic: use deterministic quote unless complex logic needed
    return quotes[date.today().day % len(quotes)]

def timer_component(key_prefix, label, is_running, elapsed_time):
    st.markdown(f"### {label}")
    
    # JS-driven timer
    timer_html = f"""
    <div id="timer_{key_prefix}" style="text-align: center; font-size: 3em; font-family: monospace; color: #2c3e50; background: #ecf0f1; border-radius: 10px; padding: 10px;">
        Calculating...
    </div>
    <script>
    function updateTimer() {{
        const startTime = {st.session_state.get(f"{key_prefix}_start_time", 0)};
        const elapsedStored = {elapsed_time};
        const isRunning = {str(is_running).lower()};
        
        let totalSeconds = elapsedStored;
        if (isRunning) {{
            const now = Date.now() / 1000;
            totalSeconds += (now - startTime);
        }}
        
        const hours = Math.floor(totalSeconds / 3600);
        const mins = Math.floor((totalSeconds % 3600) / 60);
        const secs = Math.floor(totalSeconds % 60);
        
        const pad = (n) => n < 10 ? '0' + n : n;
        const timeString = `${{pad(hours)}}:${{pad(mins)}}:${{pad(secs)}}`;
        
        const el = document.getElementById("timer_{key_prefix}");
        if (el) {{
            el.innerText = timeString;
        }}
    }}
    
    setInterval(updateTimer, 1000);
    updateTimer(); 
    </script>
    """
    components.html(timer_html, height=100)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("▶️ Start", key=f"{key_prefix}_start", disabled=is_running):
            st.session_state[f"{key_prefix}_timer_running"] = True
            st.session_state[f"{key_prefix}_start_time"] = time.time()
            st.rerun()
            
    with c2:
        if st.button("II Pause", key=f"{key_prefix}_pause", disabled=not is_running):
            st.session_state[f"{key_prefix}_timer_running"] = False
            # Add session time to elapsed
            st.session_state[f"{key_prefix}_elapsed"] += time.time() - st.session_state[f"{key_prefix}_start_time"]
            st.rerun()
            
    with c3:
        if st.button("🔄 Reset", key=f"{key_prefix}_reset"):
            st.session_state[f"{key_prefix}_timer_running"] = False
            st.session_state[f"{key_prefix}_elapsed"] = 0
            st.rerun()


# --- HEADER & NAVIGATION ---
st.title("🚀 Growth Engine")

tabs = st.tabs(["📊 Dashboard", "🏋️ Gym Tracker", "📈 Analysis", "👨‍🍳 Recipes", "🛒 Grocery", "⚙️ Settings"])

with tabs[0]: # DASHBOARD
    # --- QUOTE ---
    quote = get_quote(st.session_state.api_key)
    st.markdown(f"""
    <div class="dashboard-card" style="text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;">
        <h3>🌟 Quote of the Day</h3>
        <p style="font-size: 1.2em; font-style: italic;">"{quote}"</p>
    </div>
    """, unsafe_allow_html=True)
    
    # --- METRICS ---
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
            
        st.subheader("🍗 Protein Tracker")
        with st.form("protein_form"):
            p_name = st.text_input("Food Item", placeholder="e.g. Chicken Breast")
            c1, c2, c3 = st.columns(3)
            with c1: p_qty = st.number_input("Qty", 0.0, step=0.5, value=1.0)
            with c2: p_unit = st.text_input("Unit", value="pcs")
            with c3: p_g = st.number_input("Protein (g)", 0.0, step=1.0)
            
            if st.form_submit_button("Add Protein"):
                if p_name and p_g > 0:
                    dm.save_protein_entry({
                        "Date": str(date.today()),
                        "Food_Name": p_name,
                        "Quantity": p_qty,
                        "Unit": p_unit,
                        "Protein_g": p_g
                    })
                    st.success(f"Added {p_g}g protein!")
                    st.rerun()

        # Show Today's Total
        today_protein = dm.get_daily_protein_total(str(date.today()))
        st.metric("Today's Protein Intake", f"{today_protein}g")

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

with tabs[1]: # GYM TRACKER (New)
    st.header("🏋️ Gym Workout Tracker")
    
    st.markdown("### 🎙️ AI Quick Log")
    st.info("Record your voice or type your workout to auto-fill the form below. Requires Google Gemini API Key.")
    
    api_key_valid = bool(st.session_state.api_key)
    
    # Audio Input (New Streamlit Feature)
    audio_val = st.audio_input("Record Workout Summary")
    
    # Text Input fallback
    text_val = st.text_area("Or type here...", placeholder="I did 3 sets of Bench Press at 80kg for 8 reps. Target muscle was Chest.")
    
    ai_data = {}
    
    if st.button("✨ Process with AI", disabled=not api_key_valid):
        with st.spinner("Analyzing..."):
            transcript = None
            if audio_val:
                transcript, err = ai_utils.transcribe_audio(audio_val, st.session_state.api_key)
                if err:
                    st.error(f"Transcription Error: {err}")
                else:
                    st.write(f"**Transcript:** {transcript}")
                    text_val = transcript # use transcript for parsing
            
            if text_val:
                ai_data, err = ai_utils.parse_workout_text(text_val, st.session_state.api_key)
                if err:
                    st.error(f"Parsing Error: {err}")
                else:
                    st.success("Data extracted!")
            else:
                st.warning("Please provide audio or text.")

    st.divider()
    st.markdown("### 📝 Log Entry")
    
    with st.form("gym_form"):
        # Auto-fill logic
        def get_val(key, default):
            return ai_data.get(key, default) if ai_data else default
            
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            g_date = st.date_input("Day", date.today())
            g_exercise = st.text_input("Exercise", value=get_val("Exercise", ""))
            g_muscle = st.text_input("Target Muscle", value=get_val("Target_Muscle", ""))
            g_region = st.selectbox("Region", ["Upper Body", "Lower Body", "Core", "Full Body", "Cardio"], index=0) # AI mapping is harder for index, leave manual or default
        
        with col_g2:
            g_sets_reps = st.text_input("Target Sets x Reps", value=get_val("Target_Sets_Reps", ""))
            c_w1, c_w2 = st.columns(2)
            with c_w1: g_min_w = st.number_input("Min Weight (kg)", value=float(get_val("Min_Weight", 0.0)))
            with c_w2: g_max_w = st.number_input("Max Weight (kg)", value=float(get_val("Max_Weight", 0.0)))
            g_reps = st.text_input("Actual Reps", value=str(get_val("Reps", "")))
            
        g_notes = st.text_area("Notes", value=get_val("Notes", ""))
        
        if st.form_submit_button("Save Workout Log"):
            entry = {
                "Date": str(g_date),
                "Exercise": g_exercise,
                "Target_Muscle": g_muscle,
                "Region": g_region,
                "Target_Sets_Reps": g_sets_reps,
                "Min_Weight": g_min_w,
                "Max_Weight": g_max_w,
                "Reps": g_reps,
                "Notes": g_notes
            }
            dm.save_workout_entry(entry)
            st.success("Workout Logged!")


with tabs[2]: # ANALYSIS
    st.header("📈 Deep Dive Analysis")
    
    # Audit History
    st.subheader("🗓️ Task History")
    audit_df = dm.load_audit_data()
    if not audit_df.empty:
        st.dataframe(audit_df.sort_values("Date", ascending=False), use_container_width=True)
        # Charts... (Existing)
        col_charts_1, col_charts_2 = st.columns(2)
        with col_charts_1:
             # 1. Study Hours Stacked Bar
            st.write("### 📚 Study Hours")
            audit_df['Date'] = pd.to_datetime(audit_df['Date'])
            audit_df = audit_df.sort_values('Date')
            study_df = audit_df[['Date', 'CPA_Hours', 'Tech_AI_Hours']].melt('Date', var_name='Type', value_name='Hours')
            fig_bar = px.bar(study_df, x='Date', y='Hours', color='Type', title="Daily Study Hours", barmode='stack')
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with col_charts_2:
            # 2. Habit Heatmap
            st.write("### 🔥 Habit Consistency")
            habit_cols = ['Gym', 'Cardio', 'Diet_Adherence', 'Dog_Walks', 'Dog_Grooming', 'Supp_Omega3']
            heatmap_data = []
            for idx, row in audit_df.iterrows():
                d_str = row['Date'].strftime('%Y-%m-%d')
                for habit in habit_cols:
                    val = 1 if row[habit] else 0
                    if habit == 'Dog_Walks' and row[habit] > 0: val = 1
                    heatmap_data.append({'Date': d_str, 'Habit': habit, 'Done': val})
            
            if heatmap_data:
                hm_df = pd.DataFrame(heatmap_data)
                fig_hm = px.density_heatmap(hm_df, x='Date', y='Habit', z='Done', color_continuous_scale='Greens', title="Habit Heatmap")
                st.plotly_chart(fig_hm, use_container_width=True)
    else:
        st.info("No audit data yet.")
        
    st.divider()
    
    # Protein History
    st.subheader("🍗 Protein Intake")
    p_df = dm.load_protein_log()
    if not p_df.empty:
        p_df['Date'] = pd.to_datetime(p_df['Date'])
        daily_p = p_df.groupby('Date')['Protein_g'].sum().reset_index()
        fig_p = px.line(daily_p, x='Date', y='Protein_g', markers=True, title="Daily Protein Intake (g)")
        fig_p.add_hline(y=150, line_dash="dash", line_color="green", annotation_text="Target (150g)")
        st.plotly_chart(fig_p, use_container_width=True)
    else:
        st.info("No protein logs yet.")
        
    st.divider()
    
    # Gym Analytics
    st.subheader("🏋️ Gym History")
    gym_df = dm.load_workout_log()
    if not gym_df.empty:
        st.dataframe(gym_df, use_container_width=True)
        
        # Download Button (Excel)
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            gym_df.to_excel(writer, index=False, sheet_name='Workouts')
            
        st.download_button(
            label="📥 Download History (Excel)",
            data=buffer.getvalue(),
            file_name="gym_history.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("No workout logs yet.")

with tabs[3]: # RECIPES
    st.header("👨‍🍳 Healthy Kitchen Vault")
    subtabs = st.tabs(["Add New Recipe", "Browse Vault"])
    # ... (Existing Recipe Code) ...
    with subtabs[0]:
        with st.form("recipe_form"):
            name = st.text_input("Recipe Name")
            tags = st.multiselect("Category", ["High Protein", "Low Carb", "Quick", "Meal Prep"])
            ingredients = st.text_area("Ingredients (One per line, e.g., '2 eggs', '200g chicken')")
            instructions = st.text_area("Steps")
            if st.form_submit_button("Save to Vault"):
                if name and ingredients:
                    dm.save_recipe_data({"Name": name, "Tags": ", ".join(tags), "Ingredients": ingredients, "Instructions": instructions})
                    st.success(f"'{name}' saved!")

    with subtabs[1]:
        recipes_df = dm.load_recipe_data()
        if not recipes_df.empty:
            search = st.text_input("🔍 Search Recipes", "")
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

with tabs[4]: # GROCERY
    st.header("🛒 Smart Grocery List")
    recipes_df = dm.load_recipe_data()
    # ... (Existing Grocery Code) ...
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

with tabs[5]: # SETTINGS
    st.header("⚙️ Settings")
    st.write("Configure external integrations.")
    
    # Updated Label for Clarity
    key = st.text_input("Google Gemini API Key (for Voice/AI Features & Quotes)", type="password", value=st.session_state.api_key)
    if key:
        st.session_state.api_key = key
        st.success("API Key saved!")
    
    st.divider()
    st.sidebar.info("Navigation moved to top tabs.")
