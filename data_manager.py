import pandas as pd
import os
import re
from datetime import timedelta

AUDIT_FILE = "daily_audit.csv"
RECIPE_FILE = "recipes.csv"

REQUIRED_COLUMNS = [
    "Date",
    "CPA_Hours",
    "Tech_AI_Hours",
    "Gym",
    "Cardio",
    "Dog_Walks",
    "Dog_Grooming",
    "Diet_Adherence",
    "Supp_Omega3",
    "Supp_Magnesium",
    "Supp_VitD",
    "Supp_Creatine"
]

def load_audit_data():
    if not os.path.isfile(AUDIT_FILE):
        return pd.DataFrame(columns=REQUIRED_COLUMNS)

    df = pd.read_csv(AUDIT_FILE)

    # Ensure all required columns exist
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        for col in missing_cols:
            df[col] = 0 if "Hours" in col or "Walks" in col else False
        # Save back to fix the file structure immediately
        df.to_csv(AUDIT_FILE, index=False)

    return df

def save_audit_data(entry):
    df = load_audit_data()

    # Remove existing entry for the same date to overwrite
    df = df[df['Date'] != entry['Date']]

    # Create new dataframe
    new_entry_df = pd.DataFrame([entry])

    # Concatenate and save
    df = pd.concat([df, new_entry_df], ignore_index=True)
    df.to_csv(AUDIT_FILE, index=False)

def load_recipe_data():
    if not os.path.isfile(RECIPE_FILE):
        return pd.DataFrame(columns=["Name", "Tags", "Ingredients", "Instructions"])
    return pd.read_csv(RECIPE_FILE)

def save_recipe_data(recipe_entry):
    df = load_recipe_data()
    new_df = pd.DataFrame([recipe_entry])
    df = pd.concat([df, new_df], ignore_index=True)
    df.to_csv(RECIPE_FILE, index=False)

def calculate_streaks(df):
    """
    Calculates streaks for CPA, Gym, Dog Care, and Tech.
    Returns a dictionary of streaks.
    """
    if df.empty:
        return {"CPA": 0, "Gym": 0, "Dog": 0, "Tech": 0}

    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date', ascending=False)

    streaks = {"CPA": 0, "Gym": 0, "Dog": 0, "Tech": 0}

    today = pd.to_datetime("today").normalize()

    # Define success criteria
    criteria = {
        "CPA": lambda r: r['CPA_Hours'] > 0,
        "Gym": lambda r: r['Gym'] == True or r['Gym'] == 1,
        "Dog": lambda r: r['Dog_Walks'] > 0, # Assuming at least 1 walk is a "success" for streak
        "Tech": lambda r: r['Tech_AI_Hours'] > 0
    }

    for key, check_func in criteria.items():
        current_streak = 0
        # Check from most recent date backwards
        # Note: If today is not logged, we check yesterday.
        # If today IS logged and success, streak starts today.

        # We need to handle gaps. If there's a gap > 1 day, streak breaks.

        last_date = None
        for idx, row in df.iterrows():
            date = row['Date']

            # Skip future dates if any
            if date > today:
                continue

            # If it's the first date we check
            if last_date is None:
                # If the latest entry is today or yesterday, we can count it.
                # If latest entry is 2 days ago, streak is broken (0).
                diff = (today - date).days
                if diff > 1:
                    break # Streak broken before we started
                last_date = date
            else:
                # Ensure dates are consecutive
                if (last_date - date).days > 1:
                    break
                last_date = date

            if check_func(row):
                current_streak += 1
            else:
                # If we fail the check on a day that should count, streak ends
                # Exception: if today is the first day and we haven't logged it yet (fail),
                # but we are checking streaks based on history...
                # Simpler logic: Streak is consecutive days of SUCCESS ending at today or yesterday.
                break

        streaks[key] = current_streak

    return streaks

def parse_ingredient(line):
    """
    Parses a line like '2 eggs' or '200g chicken' into (quantity, unit, item).
    This is a heuristic parser.
    """
    line = line.strip().lower()
    if not line:
        return None

    # Regex for Number + Unit + Item
    # e.g., 2.5 kg chicken, 2 eggs, 1/2 cup sugar

    # Simplified: Look for leading number
    match = re.match(r"(\d+(\.\d+)?|\d+/\d+)\s*([a-zA-Z]+)?\s+(.*)", line)

    if match:
        qty_str = match.group(1)
        unit = match.group(3) if match.group(3) else ""
        item = match.group(4)

        # Convert fraction to float
        if '/' in qty_str:
            n, d = qty_str.split('/')
            qty = float(n) / float(d)
        else:
            qty = float(qty_str)

        # Common units cleaning
        if unit in ['g', 'gram', 'grams']: unit = 'g'
        if unit in ['kg', 'kilogram']: unit = 'kg'
        if unit in ['ml']: unit = 'ml'
        if unit in ['l', 'liter']: unit = 'l'
        if not unit: unit = 'pcs' # default to pieces if just "2 eggs"

        return {"qty": qty, "unit": unit, "item": item}
    else:
        # No number found, treat as 1 unit
        return {"qty": 1.0, "unit": "pcs", "item": line}

def aggregate_ingredients(ingredient_lines):
    """
    Takes a list of ingredient strings and returns a unified list.
    """
    agg = {} # key: (item_name, unit) -> qty

    for line in ingredient_lines:
        parsed = parse_ingredient(line)
        if parsed:
            key = (parsed['item'], parsed['unit'])
            agg[key] = agg.get(key, 0) + parsed['qty']

    results = []
    for (item, unit), qty in agg.items():
        # Format nicely
        if unit == 'pcs':
            results.append(f"{qty:g} {item}")
        else:
            results.append(f"{qty:g}{unit} {item}")

    return sorted(results)
