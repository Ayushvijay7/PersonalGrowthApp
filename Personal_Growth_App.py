import streamlit as st
import pandas as pd
import os
import time
from datetime import date, datetime

# --- CONFIGURATION & FILE SETUP ---
st.set_page_config(page_title="CA to AI Growth Tracker", layout="wide", page_icon="🚀")

AUDIT_FILE = "daily_audit.csv"
RECIPE_FILE = "recipes.csv"

# Session State for Timer Logic
if 'timer_running' not in st.session_state:
    st.session_state.timer_running = False
if 'start_time' not in st.session_state:
    st.session_state.start_time = 0
if 'elapsed_time' not in st.session_state:
    st.session_state.elapsed_time = 0

# Helper function to save audit data
def save_audit_data(entry):
    if not os.path.isfile(AUDIT_FILE):
        df = pd.DataFrame([entry])
        df.to_csv(AUDIT_FILE, index=False)
    else:
        df = pd.read_csv(AUDIT_FILE)
        df = df[df['Date'] != entry['Date']] 
        df = pd.concat([df, pd.DataFrame([entry])], ignore_index=False)
        df.to_csv(AUDIT_FILE, index=False)

def save_recipe_data(recipe_entry):
    recipe_df = pd.DataFrame([recipe_entry])
    if not os.path.isfile(RECIPE_FILE):
        recipe_df.to_csv(RECIPE_FILE, index=False)
    else:
        pd.concat([pd.read_csv(RECIPE_FILE), recipe_df]).to_csv(RECIPE_FILE, index=False)

# --- SIDEBAR NAVIGATION ---
st.sidebar.title("🛠️ Growth Engine")
page = st.sidebar.radio("Navigation", ["Daily Audit", "Recipe Vault", "Grocery List Generator"])
st.sidebar.divider()

# --- PAGE 1: DAILY AUDIT & TIMER ---
if page == "Daily Audit":
    st.title("📊 Daily Audit & Growth")
    
    # FOCUS TIMER SECTION
    st.subheader("⏱️ CPA Focus Timer")
    t_col1, t_col2, t_col3 = st.columns([1, 1, 2])
    
    with t_col1:
        if st.button("▶️ Start Session"):
            st.session_state.timer_running = True
            st.session_state.start_time = time.time() - st.session_state.elapsed_time
            
        if st.button("⏹️ Stop/Pause"):
            st.session_state.timer_running = False

    with t_col2:
        if st.button("🔄 Reset Timer"):
            st.session_state.timer_running = False
            st.session_state.elapsed_time = 0
            
    with t_col3:
        if st.session_state.timer_running:
            st.session_state.elapsed_time = time.time() - st.session_state.start_time
            # Auto-rerun to update the clock
            time.sleep(1)
            st.rerun()
            
        mins, secs = divmod(int(st.session_state.elapsed_time), 60)
        hours = mins // 60
        mins = mins % 60
        st.header(f"{hours:02d}:{mins:02d}:{secs:02d}")
        st.caption("Keep this tab open while you study.")

    st.divider()

    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Today's Audit")
        d = st.date_input("Date", date.today())
        # Suggest hours based on the timer if it was used
        suggested_hrs = round(st.session_state.elapsed_time / 3600, 2)
        cpa = st.number_input("CPA Study (Hours)", 0.0, 12.0, suggested_hrs, step=0.5)
        
        gym = st.checkbox("Strength Training")
        cardio = st.checkbox("Cheeni Walks (Cardio)")
        
        st.write("**Supplements**")
        s1 = st.checkbox("Omega 3")
        s2 = st.checkbox("Magnesium")
        s3 = st.checkbox("Vitamin D3/E")
        s4 = st.checkbox("Creatine/Protein")
        
        if st.button("Save Today's Audit", use_container_width=True):
            new_data = {
                "Date": str(d),
                "CPA_Hours": cpa,
                "Gym": gym,
                "Cardio": cardio,
                "Supps_Complete": all([s1, s2, s3, s4])
            }
            save_audit_data(new_data)
            st.success("Audit Logged! Don't forget your Gua Sha tonight.")

    with col2:
        st.subheader("Progress Analytics")
        if os.path.isfile(AUDIT_FILE):
            data = pd.read_csv(AUDIT_FILE)
            data['Date'] = pd.to_datetime(data['Date'])
            data = data.sort_values('Date')
            st.line_chart(data.set_index("Date")["CPA_Hours"])
            
            total_study = data['CPA_Hours'].sum()
            st.metric("Total CPA Hours Invested", f"{total_study} hrs")
        else:
            st.info("Your growth data will appear here once you log your first day.")

# --- PAGE 2: RECIPE VAULT ---
elif page == "Recipe Vault":
    st.title("👨‍🍳 Healthy Kitchen Vault")
    tab1, tab2 = st.tabs(["Add New Recipe", "Browse Vault"])

    with tab1:
        with st.form("recipe_form"):
            name = st.text_input("Recipe Name")
            tags = st.multiselect("Category", ["High Protein", "Low Carb", "Quick", "Meal Prep"])
            ingredients = st.text_area("Ingredients (One per line)")
            instructions = st.text_area("Steps")
            if st.form_submit_button("Save to Vault"):
                if name and ingredients:
                    save_recipe_data({"Name": name, "Tags": ", ".join(tags), "Ingredients": ingredients, "Instructions": instructions})
                    st.success(f"'{name}' saved!")

    with tab2:
        if os.path.isfile(RECIPE_FILE):
            recipes_df = pd.read_csv(RECIPE_FILE)
            search = st.text_input("🔍 Search", "")
            filtered = recipes_df[recipes_df['Name'].str.contains(search, case=False)]
            for idx, row in filtered.iterrows():
                with st.expander(f"📖 {row['Name']}"):
                    st.write(f"**Category:** {row['Tags']}")
                    st.write("**Ingredients:**")
                    st.write(row['Ingredients'])
                    st.write("**Steps:**")
                    st.write(row['Instructions'])

# --- PAGE 3: GROCERY LIST GENERATOR ---
elif page == "Grocery List Generator":
    st.title("🛒 Smart Grocery List")
    if os.path.isfile(RECIPE_FILE):
        recipes_df = pd.read_csv(RECIPE_FILE)
        selected = st.multiselect("Plan your meals:", recipes_df['Name'].tolist())
        if selected:
            all_items = []
            for r in selected:
                items = recipes_df[recipes_df['Name'] == r]['Ingredients'].values[0]
                all_items.extend([i.strip() for i in str(items).split('\n') if i.strip()])
            
            unique_items = sorted(list(set(all_items)))
            for item in unique_items:
                st.checkbox(item, key=f"shop_{item}")
            st.divider()
            st.caption("Remember: No sugar, no fried food, high carb is a no-go.")
    else:
        st.warning("Add recipes to the vault first!")

# --- FOOTER ---
st.sidebar.markdown("---")
st.sidebar.caption(f"Target: 9 AM Wakeup | Last Audit: {date.today()}")
