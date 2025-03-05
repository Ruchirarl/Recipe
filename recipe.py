import streamlit as st
import requests
import os
from bs4 import BeautifulSoup
import random
import pandas as pd

# ──────────────────────────────────────────────────────────
#                     APP SETUP
# ──────────────────────────────────────────────────────────

st.set_page_config(page_title="🍽 BiteByType - Meals that fit your personality")

# Loading API keys securely from Streamlit secrets
SPOONACULAR_API_KEY = st.secrets["SPOONACULAR_API_KEY"]
YELP_API_KEY = st.secrets["YELP_API_KEY"]

# Displaying the app title
st.title("🍽 BiteByType - Meals that fit your personality")

st.markdown("""
## 🥗 Welcome to BiteByType!
Discover personalized recipes & drinks based on your personality, dietary needs, and preferences! 🥦🍲🥤

🔍 How It Works  
- Choose *By Personality 🎭, **By Ingredient 🥑, **By Nutrients 🏋, **By Meal Type 🍽, or **Drinks by Personality 🍹*  
- Get *recipe recommendations & nearby restaurants*  
- Explore *beverages based on Wikipedia data*  

Let's find your next favorite meal! 🍽✨
""")

# ──────────────────────────────────────────────────────────
#               PERSONALITY TO CUISINE MAPPING
# ──────────────────────────────────────────────────────────

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

diet_types = ["Gluten Free", "Ketogenic", "Vegetarian", "Vegan", "Paleo", "Whole30"]

# ──────────────────────────────────────────────────────────
#               API FETCHING UTILITIES
# ──────────────────────────────────────────────────────────

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

# ──────────────────────────────────────────────────────────
#               FETCH RECIPES FROM SPOONACULAR
# ──────────────────────────────────────────────────────────

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

# ──────────────────────────────────────────────────────────
#               FETCH BEVERAGES FROM WIKIPEDIA
# ──────────────────────────────────────────────────────────

@st.cache_data
def get_wikipedia_beverages():
    """Scrapes Wikipedia and extracts beverage data."""
    url = "https://en.wikipedia.org/wiki/Table_of_food_nutrients"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Extracting the correct table (16th table on the page)
    tables = soup.find_all("table", {"class": "wikitable"})
    beverages_table = tables[15]  # Beverages table

    # Convert HTML table to DataFrame
    df = pd.read_html(str(beverages_table))[0]

    # Rename columns to avoid issues
    df.columns = ["Food", "Measure", "Grams", "Calories", "Protein", "Carb", "Fiber", "Fat", "Sat_fat"]

    # Drop the first row if it's merged content (like "Beverages")
    df = df[df["Food"] != "Beverages"]

    return df

# Fetch Wikipedia beverages
beverages_df = get_wikipedia_beverages()

def suggest_beverage(personality):
    """Finds a Wikipedia beverage related to a personality."""
    if personality in PERSONALITY_TO_CUISINE:
        return beverages_df["Food"].sample(n=1).values[0]  # Pick a random drink
    return "Water"  # Default fallback

# ──────────────────────────────────────────────────────────
#               STREAMLIT UI - RADIO BUTTONS
# ──────────────────────────────────────────────────────────

search_type = st.radio(
    "## How would you like to find a recipe?",
    ["By Personality", "By Ingredient", "By Nutrients", "By Meal Type", "Drinks by Personality"],
    index=None
)

recipe = None
suggested_beverage = None

if search_type:
    # ──────────────────────────────────────────────────────────
    #       RECIPES BY PERSONALITY
    # ──────────────────────────────────────────────────────────
    if search_type == "By Personality":
        personality = st.selectbox("Select your dominant personality trait", list(PERSONALITY_TO_CUISINE.keys()), index=None)
        diet = st.selectbox("Choose your diet preference", diet_types, index=None)

        if st.button("Find Recipe"):
            recipe = get_recipe_by_personality(personality, diet)

    # ──────────────────────────────────────────────────────────
    #       DRINKS BY PERSONALITY
    # ──────────────────────────────────────────────────────────
    elif search_type == "Drinks by Personality":
        personality = st.selectbox("Select your dominant personality trait", list(PERSONALITY_TO_CUISINE.keys()), index=None)

        if st.button("Find Drink"):
            suggested_beverage = suggest_beverage(personality)

# ──────────────────────────────────────────────────────────
#               DISPLAY RESULTS
# ──────────────────────────────────────────────────────────

if recipe:
    st.subheader(f"Recommended Recipe: {recipe.get('title', 'No title')}")
    st.image(recipe.get("image", ""), width=400)
    st.write(f"### Total Preparation Time: {recipe.get('readyInMinutes', 'N/A')} minutes")

if suggested_beverage:
    st.subheader(f"🍹 Suggested Drink: *{suggested_beverage}* (From Wikipedia)")

else:
    st.write("Welcome! Choose a search method above to find a recipe or a drink.")