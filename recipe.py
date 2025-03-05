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

# Function to fetch beverages from Wikipedia dynamically
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

    return df

# Fetch Wikipedia beverages
beverages_df = get_wikipedia_beverages()

# Debug: Show the first few rows to inspect structure
st.write("Wikipedia Beverages Data:", beverages_df.head())

# Suggest beverage based on personality
def suggest_beverage(personality):
    """Finds a Wikipedia beverage related to a personality."""
    if personality in PERSONALITY_TO_CUISINE:
        beverage_options = beverages_df["Food"].sample(n=1).values[0]  # Pick random drink
        return beverage_options
    return "Water"  # Default

# Personality to Cuisine Mapping
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

# Diet Types
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

# Fetch Recipes Based on User Selection
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

# Streamlit UI
search_type = st.radio(
    "## How would you like to find a recipe?",
    ["By Personality", "By Ingredient", "By Nutrients"],
    index=None
)

recipe = None
suggested_beverage = None

if search_type:
    if search_type == "By Personality":
        personality = st.selectbox(
            "Select your dominant personality trait",
            list(PERSONALITY_TO_CUISINE.keys()),
            index=None
        )
        diet = st.selectbox("Choose your diet preference", diet_types, index=None)

        if st.button("Find Recipe"):
            recipe = get_recipe_by_personality(personality, diet)
            suggested_beverage = suggest_beverage(personality)  # Fetch from Wikipedia

if recipe:
    st.subheader(f"Recommended Recipe: {recipe.get('title', 'No title')}")
    st.image(recipe.get("image", ""), width=400)
    st.write(f"### Total Preparation Time: {recipe.get('readyInMinutes', 'N/A')} minutes")

    if suggested_beverage:
        st.write(f"### Suggested Beverage: *{suggested_beverage}* 🍹 (From Wikipedia)")

else:
    st.write("Welcome! Choose a search method above to find a recipe that suits you.")