import streamlit as st
import requests
import os
from bs4 import BeautifulSoup
import pandas as pd
import random

# ───────────────────────────────────────────────────────────
# Streamlit Page Configuration
# ───────────────────────────────────────────────────────────
st.set_page_config(page_title="🍽 BiteByType - Meals that fit your personality")

# ───────────────────────────────────────────────────────────
# Load API Keys from Streamlit Secrets
# ───────────────────────────────────────────────────────────
SPOONACULAR_API_KEY = st.secrets["SPOONACULAR_API_KEY"]
YELP_API_KEY = st.secrets["YELP_API_KEY"]  # Not used in this snippet, but available if needed

# ───────────────────────────────────────────────────────────
# Main Title & Intro
# ───────────────────────────────────────────────────────────
st.title("🍽 BiteByType - Meals that fit your personality")

st.markdown(
    """
    ## 🥗 Welcome to BiteByType!
    BiteByType is your personalized meal finder, helping you discover recipes tailored to your 
    personality, dietary preferences, and nutritional needs! 🥦🍲

    **Features**:
    1. **By Personality (Recipe)** – from Spoonacular
    2. **By Ingredient (Recipe)** – from Spoonacular
    3. **By Nutrients (Recipe)** – from Spoonacular
    4. **Drinks by Personality** – from Wikipedia
    5. **Get Drink by Meal Type** – from Wikipedia
    
    Let's find your next favorite meal (or drink)! 🍽✨
    """
)

# ───────────────────────────────────────────────────────────
# Personality-to-Cuisine Mapping (for Spoonacular)
# ───────────────────────────────────────────────────────────
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

# ───────────────────────────────────────────────────────────
# Diet Types
# ───────────────────────────────────────────────────────────
diet_types = [
    "Gluten Free", "Ketogenic", "Vegetarian", "Lacto-Vegetarian",
    "Ovo-Vegetarian", "Vegan", "Pescetarian", "Paleo",
    "Primal", "Low FODMAP", "Whole30"
]

# ───────────────────────────────────────────────────────────
# Wikipedia Beverages (for personality & meal type drinks)
# ───────────────────────────────────────────────────────────
@st.cache_data
def get_wikipedia_beverages():
    """
    Scrapes Wikipedia's 'Table of food nutrients' page and extracts
    the beverages table as a Pandas DataFrame.
    """
    url = "https://en.wikipedia.org/wiki/Table_of_food_nutrients"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # The beverages table is the 16th wikitable on that page
    tables = soup.find_all("table", {"class": "wikitable"})
    beverages_table = tables[15]

    # Convert the HTML table to a DataFrame
    df = pd.read_html(str(beverages_table))[0]

    # Rename columns for clarity
    df.columns = ["Food", "Measure", "Grams", "Calories", "Protein", "Carb", "Fiber", "Fat", "Sat_fat"]

    # Remove any row that's just "Beverages" or merged headers
    df = df[df["Food"] != "Beverages"]

    return df

beverages_df = get_wikipedia_beverages()

def suggest_beverage(personality):
    """
    Returns a random beverage from the Wikipedia table.
    If the personality is recognized, we random-pick from the DF;
    otherwise default to 'Water'.
    """
    if personality in PERSONALITY_TO_CUISINE:
        return beverages_df["Food"].sample(n=1).values[0]
    return "Water"

def suggest_beverage_by_meal_type(meal_type):
    """
    Returns a random beverage from the Wikipedia table.
    (Currently not filtering specifically by meal_type – purely random.)
    """
    return beverages_df["Food"].sample(n=1).values[0]

# ───────────────────────────────────────────────────────────
# Spoonacular API Helper (cached)
# ───────────────────────────────────────────────────────────
@st.cache_data
def fetch_api(url, params):
    """
    Make a GET request to Spoonacular (or other) with given params.
    Return JSON if successful, None otherwise.
    """
    try:
        r = requests.get(url, params=params)
        if r.status_code == 200:
            return r.json()
        return None
    except requests.RequestException:
        return None

# ───────────────────────────────────────────────────────────
# Spoonacular: By Personality (Recipe)
# ───────────────────────────────────────────────────────────
def get_recipe_by_personality(personality, diet):
    """
    Fetch a random recipe from Spoonacular that aligns with a 
    certain personality-cuisine and specified diet.
    """
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

# ───────────────────────────────────────────────────────────
# Spoonacular: By Ingredient (Recipe)
# ───────────────────────────────────────────────────────────
def get_recipe_by_ingredient(ingredient, max_time):
    """
    Fetch a Spoonacular recipe that includes a certain ingredient
    and can be prepared within 'max_time' minutes.
    """
    url = "https://api.spoonacular.com/recipes/complexSearch"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "includeIngredients": ingredient,
        "maxReadyTime": max_time,
        "number": 1,
        "instructionsRequired": True
    }
    data = fetch_api(url, params)
    if data and data.get("results"):
        # We'll get more details about the first result
        recipe_id = data["results"][0]["id"]
        return get_recipe_details_by_id(recipe_id)
    return None

# ───────────────────────────────────────────────────────────
# Spoonacular: By Nutrients (Recipe)
# ───────────────────────────────────────────────────────────
def get_recipe_by_nutrients(nutrient, min_value, max_value, max_time):
    """
    Fetch a Spoonacular recipe by specifying nutrient constraints 
    (calories, protein, or fat) within certain min/max values, plus max prep time.
    """
    url = "https://api.spoonacular.com/recipes/findByNutrients"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "addRecipeNutrition": True,
        f"min{nutrient}": min_value,
        f"max{nutrient}": max_value,
        "maxReadyTime": max_time,
        "number": 1
    }
    data = fetch_api(url, params)
    if data and len(data) > 0:
        # data is a list of recipes, we take the first
        recipe_id = data[0]["id"]
        return get_recipe_details_by_id(recipe_id)
    return None

def get_recipe_details_by_id(recipe_id):
    """
    Given a Spoonacular recipe ID, fetch full details including 
    extended ingredients, instructions, and nutrition.
    """
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "includeNutrition": True
    }
    return fetch_api(url, params)

# ───────────────────────────────────────────────────────────
# Streamlit UI: 5 Options
# ───────────────────────────────────────────────────────────
search_type = st.radio(
    "## How would you like to find something?",
    [
        "By Personality",
        "By Ingredient",
        "By Nutrients",
        "Drinks by Personality",
        "Get Drink by Meal Type"
    ],
    index=None
)

recipe = None
suggested_beverage = None

if search_type:
    # 1) By Personality (Recipe)
    if search_type == "By Personality":
        personality = st.selectbox("Select your dominant personality trait", list(PERSONALITY_TO_CUISINE.keys()))
        diet = st.selectbox("Choose your diet preference", diet_types)

        if st.button("Find Recipe"):
            recipe = get_recipe_by_personality(personality, diet)

    # 2) By Ingredient (Recipe)
    elif search_type == "By Ingredient":
        ingredient = st.text_input("Enter an ingredient (e.g. chicken, tomato, etc.)")
        max_time = st.slider("Max preparation time (minutes)", 5, 120, 30)

        if st.button("Find Recipe"):
            recipe = get_recipe_by_ingredient(ingredient, max_time)

    # 3) By Nutrients (Recipe)
    elif search_type == "By Nutrients":
        nutrient = st.selectbox("Choose a nutrient", ["Calories", "Protein", "Fat"])
        min_value = st.number_input(f"Min {nutrient}", min_value=10, value=100)
        max_value = st.number_input(f"Max {nutrient}", min_value=10, value=500)
        max_time = st.slider("Max preparation time (minutes)", 5, 120, 30)

        if st.button("Find Recipe"):
            recipe = get_recipe_by_nutrients(nutrient, min_value, max_value, max_time)

    # 4) Drinks by Personality (Wikipedia random)
    elif search_type == "Drinks by Personality":
        personality = st.selectbox("Select your dominant personality trait", list(PERSONALITY_TO_CUISINE.keys()))

        if st.button("Find Drink"):
            suggested_beverage = suggest_beverage(personality)

    # 5) Get Drink by Meal Type (Wikipedia random)
    elif search_type == "Get Drink by Meal Type":
        meal_type = st.selectbox("Choose a Meal Type", ["Breakfast", "Lunch", "Dinner", "Snacks"])

        if st.button("Get Drink"):
            suggested_beverage = suggest_beverage_by_meal_type(meal_type)

# ───────────────────────────────────────────────────────────
# Display the Spoonacular Recipe (if found)
# ───────────────────────────────────────────────────────────
if recipe:
    st.subheader(f"Recommended Recipe: {recipe.get('title', 'No title')}")
    # Image
    if recipe.get("image"):
        st.image(recipe["image"], width=400)
    # Prep Time
    st.write(f"### Total Preparation Time: {recipe.get('readyInMinutes', 'N/A')} minutes")
    # Ingredients
    st.write("### Ingredients:")
    for ing in recipe.get("extendedIngredients", []):
        st.write(f"- {ing['original']}")
    # Instructions
    st.write("### Instructions:")
    st.write(recipe.get("instructions", "No instructions available."))
    # Nutrition
    if "nutrition" in recipe and "nutrients" in recipe["nutrition"]:
        st.write("### Nutrition Information:")
        for n in recipe["nutrition"]["nutrients"]:
            st.write(f"- {n['name']}: {n['amount']} {n['unit']}")

# ───────────────────────────────────────────────────────────
# Display the Suggested Beverage (if found)
# ───────────────────────────────────────────────────────────
if suggested_beverage:
    st.subheader(f"🍹 Suggested Drink: {suggested_beverage}")

# ───────────────────────────────────────────────────────────
# If no search done, show a welcome message
# ───────────────────────────────────────────────────────────
if not recipe and not suggested_beverage:
    st.write("Welcome! Choose one of the options above to discover recipes or drinks.")
