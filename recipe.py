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
YELP_API_KEY = st.secrets["YELP_API_KEY"]  # If needed, not used here

# ───────────────────────────────────────────────────────────
# Main Title & Introduction
# ───────────────────────────────────────────────────────────
st.title("🍽 BiteByType - Meals that fit your personality")

st.markdown(
    """
    ## 🥗 Welcome to BiteByType!
    Here, you can discover recipes (or drinks!) tailored to 
    your **personality**, **nutrient goals**, **preferred ingredients**, 
    or **meal type**. 

    **Available Search Methods**:
    1. **By Personality** (Spoonacular)  
    2. **By Nutrients** (Spoonacular)  
    3. **By Ingredient** (Spoonacular)  
    4. **By Meal Type** (AllRecipes)  
    5. **Drink by Personality** (Wikipedia)
    """
)

# ───────────────────────────────────────────────────────────
# 1) Personality-to-Cuisine Mapping (Spoonacular)
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
# 2) Diet Types (Spoonacular)
# ───────────────────────────────────────────────────────────
diet_types = [
    "Gluten Free", "Ketogenic", "Vegetarian", "Lacto-Vegetarian", 
    "Ovo-Vegetarian", "Vegan", "Pescetarian", "Paleo", 
    "Primal", "Low FODMAP", "Whole30"
]

# ───────────────────────────────────────────────────────────
# 3) Wikipedia Beverages for "Drink by Personality"
# ───────────────────────────────────────────────────────────
@st.cache_data
def get_wikipedia_beverages():
    """
    Scrapes a Wikipedia table for beverage data. Returns a DataFrame.
    (Table #16 on the 'Table_of_food_nutrients' page, known for "Beverages".)
    """
    url = "https://en.wikipedia.org/wiki/Table_of_food_nutrients"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    all_tables = soup.find_all("table", {"class": "wikitable"})
    beverages_table = all_tables[15]  # The 16th wikitable

    df = pd.read_html(str(beverages_table))[0]
    df.columns = ["Food", "Measure", "Grams", "Calories", "Protein", "Carb", "Fiber", "Fat", "Sat_fat"]

    # Drop the header-row if it's labeled 'Beverages'
    df = df[df["Food"] != "Beverages"]

    return df

beverages_df = get_wikipedia_beverages()

def suggest_beverage(personality):
    """
    Picks a random beverage from 'beverages_df' for the given personality.
    Currently, personality is only used to confirm existence in the dict.
    If unrecognized, returns 'Water'.
    """
    if personality in PERSONALITY_TO_CUISINE:
        return beverages_df["Food"].sample(n=1).values[0]
    return "Water"

# ───────────────────────────────────────────────────────────
# 4) AllRecipes Scraper for "By Meal Type"
# ───────────────────────────────────────────────────────────
@st.cache_data
def scrape_allrecipes(meal_type_url):
    """
    Fetches a random recipe from AllRecipes.com for the given meal_type_url.
    Returns a dict with keys that match Spoonacular's recipe structure.
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(meal_type_url, headers=headers)
    if resp.status_code != 200:
        return None

    soup = BeautifulSoup(resp.text, "lxml")
    all_links = soup.select("a[href*='/recipe/']")
    if not all_links:
        return None

    recipe_url = random.choice(all_links)["href"]
    recipe_resp = requests.get(recipe_url, headers=headers)
    if recipe_resp.status_code != 200:
        return None

    recipe_soup = BeautifulSoup(recipe_resp.text, "lxml")

    # Extract Title
    title_tag = recipe_soup.find("h1")
    title = title_tag.text.strip() if title_tag else "Unknown Recipe"

    # Extract Image
    image_tag = recipe_soup.select_one("img.card__img")
    image_url = image_tag.get("data-src", image_tag.get("src", "")) if image_tag else ""

    # Extract Ingredients -> Turn them into extendedIngredients
    ings = [i.get_text(strip=True) for i in recipe_soup.select(".mm-recipes-structured-ingredients__list-item")]
    extended_ingredients = [{"original": ing} for ing in ings]

    # Extract Instructions -> Combine them into a single string
    steps = [s.get_text(strip=True) for s in recipe_soup.select(".mntl-sc-block-html")]
    instructions = "\n".join(steps) if steps else "No instructions available."

    # Return a dict resembling Spoonacular's format
    return {
        "title": title,
        "image": image_url,
        "readyInMinutes": "N/A (AllRecipes doesn't specify)",
        "extendedIngredients": extended_ingredients,
        "instructions": instructions,
        "nutrition": {
            "nutrients": []  # AllRecipes doesn't consistently provide structured macros
        }
    }

# ───────────────────────────────────────────────────────────
# 5) Spoonacular API Helper
# ───────────────────────────────────────────────────────────
@st.cache_data
def fetch_api(url, params):
    """Generic helper to make a GET request and return JSON if successful."""
    try:
        r = requests.get(url, params=params)
        if r.status_code == 200:
            return r.json()
        return None
    except requests.RequestException:
        return None

def get_recipe_details_by_id(recipe_id):
    """
    Get full details (ingredients, instructions, nutrition) from Spoonacular by ID.
    """
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    params = {"apiKey": SPOONACULAR_API_KEY, "includeNutrition": True}
    return fetch_api(url, params)

# ───────────────────────────────────────────────────────────
# Spoonacular "By Personality" (Recipe)
# ───────────────────────────────────────────────────────────
def get_recipe_by_personality(personality, diet):
    """
    Fetch a random recipe from Spoonacular aligned with a personality's cuisine 
    and the user's selected diet.
    """
    cuisine_list = PERSONALITY_TO_CUISINE.get(personality, ["Italian"])
    cuisine = cuisine_list[0] if cuisine_list else "Italian"
    url = "https://api.spoonacular.com/recipes/random"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "number": 1,
        "diet": diet,
        "cuisine": cuisine,
        "instructionsRequired": True
    }
    data = fetch_api(url, params)
    if data and "recipes" in data:
        return data["recipes"][0]
    return None

# ───────────────────────────────────────────────────────────
# Spoonacular "By Nutrients" (Recipe)
# ───────────────────────────────────────────────────────────
def get_recipe_by_nutrients(nutrient, min_val, max_val, max_time):
    """
    Fetch a Spoonacular recipe given a certain nutrient range and maximum prep time.
    Nutrient can be "Calories", "Protein", or "Fat".
    """
    url = "https://api.spoonacular.com/recipes/findByNutrients"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "addRecipeNutrition": True,
        f"min{nutrient}": min_val,
        f"max{nutrient}": max_val,
        "maxReadyTime": max_time,
        "number": 1
    }
    data = fetch_api(url, params)
    if data and len(data) > 0:
        # each item in 'data' is a partial recipe; fetch details
        first_recipe_id = data[0]["id"]
        return get_recipe_details_by_id(first_recipe_id)
    return None

# ───────────────────────────────────────────────────────────
# Spoonacular "By Ingredient" (Recipe)
# ───────────────────────────────────────────────────────────
def get_recipe_by_ingredient(ingredient, max_time):
    """
    Fetch a Spoonacular recipe given an ingredient and a max prep time.
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
    if data and "results" in data and len(data["results"]) > 0:
        r_id = data["results"][0]["id"]
        return get_recipe_details_by_id(r_id)
    return None

# ───────────────────────────────────────────────────────────
# UI: Let the user select which approach they want
#     (In the exact order requested)
# ───────────────────────────────────────────────────────────
search_type = st.radio(
    "## Please choose one of the following options:",
    [
        "By Personality",
        "By Nutrients",
        "By Ingredient",
        "By Meal Type",
        "Drink by Personality"
    ]
)

recipe = None  # Will hold Spoonacular/AllRecipes result
drink = None   # Will hold suggested beverage from Wikipedia

# ───────────────────────────────────────────────────────────
# 1) By Personality (Spoonacular Recipe)
# ───────────────────────────────────────────────────────────
if search_type == "By Personality":
    personality_choice = st.selectbox("Pick your personality trait", list(PERSONALITY_TO_CUISINE.keys()))
    diet_choice = st.selectbox("Choose a diet preference", diet_types)

    if st.button("Find Recipe"):
        recipe = get_recipe_by_personality(personality_choice, diet_choice)

# ───────────────────────────────────────────────────────────
# 2) By Nutrients (Spoonacular Recipe)
# ───────────────────────────────────────────────────────────
elif search_type == "By Nutrients":
    nutrient = st.selectbox("Nutrient to filter by", ["Calories", "Protein", "Fat"])
    min_value = st.number_input(f"Min {nutrient}", min_value=10, value=100)
    max_value = st.number_input(f"Max {nutrient}", min_value=10, value=500)
    max_time = st.slider("Max prep time (minutes)", 5, 120, 30)

    if st.button("Find Recipe"):
        recipe = get_recipe_by_nutrients(nutrient, min_value, max_value, max_time)

# ───────────────────────────────────────────────────────────
# 3) By Ingredient (Spoonacular Recipe)
# ───────────────────────────────────────────────────────────
elif search_type == "By Ingredient":
    ingredient_input = st.text_input("Enter an ingredient")
    max_prep_time = st.slider("Max preparation time (minutes)", 5, 120, 30)

    if st.button("Find Recipe"):
        recipe = get_recipe_by_ingredient(ingredient_input, max_prep_time)

# ───────────────────────────────────────────────────────────
# 4) By Meal Type (AllRecipes)
# ───────────────────────────────────────────────────────────
elif search_type == "By Meal Type":
    st.write("Select a meal type to fetch a random recipe from AllRecipes:")
    meal_types = {
        "Breakfast": "https://www.allrecipes.com/recipes/78/breakfast-and-brunch/",
        "Lunch": "https://www.allrecipes.com/recipes/17561/lunch/",
        "Dinner": "https://www.allrecipes.com/recipes/17562/dinner/",
        "Snacks": "https://www.allrecipes.com/recipes/76/appetizers-and-snacks/"
    }
    meal_choice = st.selectbox("Choose a Meal Type", list(meal_types.keys()))

    if st.button("Find Recipe"):
        recipe = scrape_allrecipes(meal_types[meal_choice])

# ───────────────────────────────────────────────────────────
# 5) Drink by Personality (Wikipedia)
# ───────────────────────────────────────────────────────────
elif search_type == "Drink by Personality":
    personality_for_drink = st.selectbox("Select your personality trait", list(PERSONALITY_TO_CUISINE.keys()))

    if st.button("Find Drink"):
        drink = suggest_beverage(personality_for_drink)

# ───────────────────────────────────────────────────────────
# Display the chosen Recipe (if any)
# ───────────────────────────────────────────────────────────
if recipe:
    st.subheader(f"Recommended Recipe: {recipe.get('title', 'No title')}")
    
    # Image (if available)
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

    # Nutrition (if any)
    if "nutrition" in recipe and "nutrients" in recipe["nutrition"]:
        st.write("### Nutrition Information:")
        for n in recipe["nutrition"]["nutrients"]:
            st.write(f"- {n['name']}: {n['amount']} {n['unit']}")

# ───────────────────────────────────────────────────────────
# Display the chosen Drink (if any)
# ───────────────────────────────────────────────────────────
if drink:
    st.subheader(f"🍹 Suggested Drink: {drink}")

# If neither recipe nor drink is selected yet, show a welcome message
if not recipe and not drink:
    st.write("Choose one of the options above to get a recipe or a drink!")
