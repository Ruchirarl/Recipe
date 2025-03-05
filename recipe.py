import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Setting Streamlit page title
st.set_page_config(page_title="🍽 BiteByType - Meals that fit your personality")

# Loading API keys from Streamlit secrets
SPOONACULAR_API_KEY = st.secrets["SPOONACULAR_API_KEY"]
YELP_API_KEY = st.secrets["YELP_API_KEY"]

# Displaying the app title
st.title("🍽 BiteByType - Meals that fit your personality")

# --- Function to Fetch Wikipedia Beverages ---
@st.cache_data
def get_wikipedia_beverages():
    """Scrapes Wikipedia and extracts beverage data."""
    url = "https://en.wikipedia.org/wiki/Table_of_food_nutrients"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Extracting the correct table (16th table on the page)
    tables = soup.find_all("table", {"class": "wikitable"})
    beverages_table = tables[15]  # Selecting the beverages table

    # Convert HTML table to DataFrame
    df = pd.read_html(str(beverages_table))[0]

    # Rename columns to avoid issues
    df.columns = ["Food", "Measure", "Grams", "Calories", "Protein", "Carb", "Fiber", "Fat", "Sat_fat"]

    # Drop the first row if it's merged content (like "Beverages")
    df = df[df["Food"] != "Beverages"]

    return df

# Fetch Wikipedia beverages
beverages_df = get_wikipedia_beverages()

# --- Function to Suggest a Beverage by Personality ---
def suggest_beverage(personality):
    """Finds a Wikipedia beverage related to a personality (random pick)."""
    if personality in PERSONALITY_TO_CUISINE:
        return beverages_df["Food"].sample(n=1).values[0]  # Pick a random drink
    return "Water"  # Default fallback

# --- NEW: Function to Suggest a Beverage by Meal Type ---
def suggest_beverage_by_meal_type(meal_type):
    """
    Picks a random beverage from the Wikipedia beverages table.
    (Currently not filtering by meal_type—purely random.)
    """
    return beverages_df["Food"].sample(n=1).values[0]

# --- Personality to Cuisine Mapping ---
PERSONALITY_TO_CUISINE = {
    "Openness": ["Japanese", "Indian", "Mediterranean"],
    "Conscientiousness": ["Balanced", "Low-Carb", "Mediterranean"],
    "Extraversion": ["BBQ", "Mexican", "Italian"],
    "Agreeableness": ["Vegetarian", "Comfort Food", "Vegan"],
    "Neuroticism": ["Healthy", "Mediterranean", "Comfort Food"],
    "Adventurous": ["Thai", "Korean", "Ethiopian"],
    "Analytical": ["French", "Greek", "Fusion"],
    "Creative": ["Molecular Gastronomy", "Experimental", "Fusion"],
    "Traditional": ["American", "British", "German"]
}

# --- Diet Types ---
diet_types = ["Gluten Free", "Ketogenic", "Vegetarian", "Vegan", "Paleo", "Whole30"]

@st.cache_data
def fetch_api(url, params):
    """Fetch data from an API and return JSON response."""
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.RequestException:
        return None

# --- Fetch Recipes ---
def get_recipe_by_personality(personality, diet):
    cuisine = PERSONALITY_TO_CUISINE.get(personality, ["Italian"])[0]
    url = "https://api.spoonacular.com/recipes/random"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "number": 1,
        "diet": diet,
        "cuisine": cuisine,
        "instructionsRequired": True
    }
    data = fetch_api(url, params)
    return data.get("recipes", [None])[0] if data else None

# --- Streamlit UI ---
search_type = st.radio(
    "## How would you like to find a recipe?",
    [
        "By Personality",
        "By Ingredient",
        "By Nutrients",
        "Drinks by Personality",
        "Get Drink by Meal Type"  # <-- NEW 5th OPTION
    ],
    index=None
)

recipe = None
suggested_beverage = None

if search_type:
    # --- 1) Recipe by Personality ---
    if search_type == "By Personality":
        personality = st.selectbox("Select your dominant personality trait", list(PERSONALITY_TO_CUISINE.keys()), index=None)
        diet = st.selectbox("Choose your diet preference", diet_types, index=None)

        if st.button("Find Recipe"):
            recipe = get_recipe_by_personality(personality, diet)

    # --- 2) Recipe by Ingredient (Not displayed in your snippet, but presumably in your real code) ---
    elif search_type == "By Ingredient":
        st.write("Your original logic for 'By Ingredient' goes here...")

    # --- 3) Recipe by Nutrients (Not displayed in your snippet, but presumably in your real code) ---
    elif search_type == "By Nutrients":
        st.write("Your original logic for 'By Nutrients' goes here...")

    # --- 4) Drinks by Personality ---
    elif search_type == "Drinks by Personality":
        personality = st.selectbox("Select your dominant personality trait", list(PERSONALITY_TO_CUISINE.keys()), index=None)

        if st.button("Find Drink"):
            suggested_beverage = suggest_beverage(personality)

    # --- 5) Drinks by Meal Type (NEW) ---
    elif search_type == "Get Drink by Meal Type":
        meal_type = st.selectbox("Select a meal type", ["Breakfast", "Lunch", "Dinner", "Snacks"])

        if st.button("Get Drink"):
            suggested_beverage = suggest_beverage_by_meal_type(meal_type)

# --- Display Recipe ---
if recipe:
    st.subheader(f"Recommended Recipe: {recipe.get('title', 'No title')}")
    st.image(recipe.get("image", ""), width=400)
    st.write(f"### Total Preparation Time: {recipe.get('readyInMinutes', 'N/A')} minutes")

# --- Display Beverage ---
if suggested_beverage:
    st.subheader(f"🍹 Suggested Drink: *{suggested_beverage}* (From Wikipedia)")

else:
    st.write("Welcome! Choose a search method above to find a recipe or a drink.")
