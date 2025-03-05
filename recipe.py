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
YELP_API_KEY = st.secrets["YELP_API_KEY"]  # Not used here, but available if needed

# ───────────────────────────────────────────────────────────
# Main Title & Introduction
# ───────────────────────────────────────────────────────────
st.title("🍽 BiteByType - Meals that fit your personality")

st.markdown(
    """
    ## 🥗 Welcome to BiteByType!
    Discover recipes and drinks based on **personality**, **nutrient needs**, **ingredient**, 
    **meal type**, or simply your **personality** for drinks (from Wikipedia)!  
    
    **Menu**:
    1. **By Personality** (Spoonacular)  
    2. **By Nutrients** (Spoonacular)  
    3. **By Ingredient** (Spoonacular)  
    4. **By Meal Type** (AllRecipes – no max prep time)  
    5. **Drink by Personality** (Wikipedia)  
    
    Let's get started! 🍽
    """
)

# ───────────────────────────────────────────────────────────
# 1) Personality-to-Cuisine Mapping
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
# 2) Diet Types (for Spoonacular)
# ───────────────────────────────────────────────────────────
diet_types = [
    "Gluten Free", "Ketogenic", "Vegetarian", "Lacto-Vegetarian",
    "Ovo-Vegetarian", "Vegan", "Pescetarian", "Paleo",
    "Primal", "Low FODMAP", "Whole30"
]

# ───────────────────────────────────────────────────────────
# 3) Wikipedia Beverages (Drink by Personality)
# ───────────────────────────────────────────────────────────
@st.cache_data
def get_wikipedia_beverages():
    """
    Scrapes 'Table of food nutrients' from Wikipedia, focusing on
    the 16th table (beverages). Returns a DataFrame.
    """
    url = "https://en.wikipedia.org/wiki/Table_of_food_nutrients"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    tables = soup.find_all("table", {"class": "wikitable"})
    beverages_table = tables[15]  # The 16th wikitable on the page

    df = pd.read_html(str(beverages_table))[0]
    df.columns = ["Food", "Measure", "Grams", "Calories", "Protein",
                  "Carb", "Fiber", "Fat", "Sat_fat"]

    # Remove any header rows labeled 'Beverages'
    df = df[df["Food"] != "Beverages"]
    return df

beverages_df = get_wikipedia_beverages()

def suggest_beverage(personality):
    """
    Picks a random beverage from the Wikipedia table if 
    'personality' is in PERSONALITY_TO_CUISINE, else returns Water.
    """
    if personality in PERSONALITY_TO_CUISINE:
        return beverages_df["Food"].sample(n=1).values[0]
    return "Water"

# ───────────────────────────────────────────────────────────
# 4) AllRecipes Scraper (By Meal Type)
# ───────────────────────────────────────────────────────────
@st.cache_data
def scrape_allrecipes(meal_type_url):
    """
    Fetches a random recipe from AllRecipes.com for the given meal_type_url.
    Attempts to parse some nutrition info from the page as well.
    """
    headers = {"User-Agent": "Mozilla/5.0"}
    resp = requests.get(meal_type_url, headers=headers)
    if resp.status_code != 200:
        return None

    soup = BeautifulSoup(resp.text, "lxml")
    links = soup.select("a[href*='/recipe/']")
    if not links:
        return None

    recipe_url = random.choice(links)["href"]
    recipe_resp = requests.get(recipe_url, headers=headers)
    if recipe_resp.status_code != 200:
        return None

    recipe_soup = BeautifulSoup(recipe_resp.text, "lxml")

    # Title
    title_tag = recipe_soup.find("h1")
    title = title_tag.text.strip() if title_tag else "Unknown Recipe"

    # Image
    image_tag = recipe_soup.select_one("img.card__img")
    image_url = image_tag.get("data-src", image_tag.get("src", "")) if image_tag else ""

    # Ingredients -> Convert to Spoonacular-like structure
    raw_ingredients = [i.get_text(strip=True) for i in recipe_soup.select(".mm-recipes-structured-ingredients__list-item")]
    extended_ingredients = [{"original": ing} for ing in raw_ingredients]

    # Instructions -> Single string
    step_texts = [s.get_text(strip=True) for s in recipe_soup.select(".mntl-sc-block-html")]
    instructions = "\n".join(step_texts) if step_texts else "No instructions available."

    # Parse nutrition from AllRecipes if available
    parsed_nutrients = []
    nutrition_table = recipe_soup.select_one(".mm-recipes-nutrition-facts-label__table")
    if nutrition_table:
        for row in nutrition_table.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) == 2:
                nutrient_name = cols[0].get_text(strip=True)
                nutrient_value = cols[1].get_text(strip=True)
                parsed_nutrients.append({
                    "name": nutrient_name,
                    "amount": nutrient_value,
                    "unit": ""
                })

    # Return in a Spoonacular-like format
    return {
        "title": title,
        "image": image_url,
        "extendedIngredients": extended_ingredients,
        "instructions": instructions,
        "nutrition": {
            "nutrients": parsed_nutrients
        }
    }

# ───────────────────────────────────────────────────────────
# 5) Spoonacular API Helpers
# ───────────────────────────────────────────────────────────
@st.cache_data
def fetch_api(url, params):
    """Generic GET request for Spoonacular or other APIs; returns JSON."""
    try:
        resp = requests.get(url, params=params)
        if resp.status_code == 200:
            return resp.json()
        return None
    except requests.RequestException:
        return None

def get_recipe_details_by_id(recipe_id):
    """
    Fetches a Spoonacular recipe's full details (ingredients,
    instructions, nutrition) by its ID.
    """
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    params = {"apiKey": SPOONACULAR_API_KEY, "includeNutrition": True}
    return fetch_api(url, params)

# Personality-based (Spoonacular)
def get_recipe_by_personality(personality, diet):
    """
    Random recipe from Spoonacular, matching cuisine from the personality
    and applying the chosen diet.
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

# Nutrient-based (Spoonacular)
def get_recipe_by_nutrients(nutrient, min_val, max_val, max_time):
    """
    Search Spoonacular by nutrient constraints. e.g. minCalories=100, maxCalories=500.
    If a result is found, get full details by ID.
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
        recipe_id = data[0]["id"]
        return get_recipe_details_by_id(recipe_id)
    return None

# Ingredient-based (Spoonacular)
def get_recipe_by_ingredient(ingredient, max_time):
    """
    Fetch Spoonacular recipe by including a specific ingredient
    and restricting total prep time to 'max_time'.
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
# User Options (5 total, in the order you requested)
# ───────────────────────────────────────────────────────────
search_type = st.radio(
    "## Choose Your Option:",
    [
        "By Personality",       # 1
        "By Nutrients",         # 2
        "By Ingredient",        # 3
        "By Meal Type",         # 4 (AllRecipes)
        "Drink by Personality"  # 5 (Wikipedia)
    ]
)

recipe = None
drink = None

# 1) By Personality (Spoonacular)
if search_type == "By Personality":
    personality = st.selectbox("Pick your personality trait", list(PERSONALITY_TO_CUISINE.keys()))
    diet = st.selectbox("Choose your diet preference", diet_types)

    if st.button("Find Recipe"):
        recipe = get_recipe_by_personality(personality, diet)

# 2) By Nutrients (Spoonacular)
elif search_type == "By Nutrients":
    nutrient = st.selectbox("Nutrient to filter by", ["Calories", "Protein", "Fat"])
    min_value = st.number_input(f"Min {nutrient}", min_value=10, value=100)
    max_value = st.number_input(f"Max {nutrient}", min_value=10, value=500)
    max_time = st.slider("Max preparation time (minutes)", 5, 120, 30)

    if st.button("Find Recipe"):
        recipe = get_recipe_by_nutrients(nutrient, min_value, max_value, max_time)

# 3) By Ingredient (Spoonacular)
elif search_type == "By Ingredient":
    ingredient = st.text_input("Enter an ingredient")
    max_time = st.slider("Max preparation time (minutes)", 5, 120, 30)

    if st.button("Find Recipe"):
        recipe = get_recipe_by_ingredient(ingredient, max_time)

# 4) By Meal Type (AllRecipes) – NO max prep time
elif search_type == "By Meal Type":
    st.write("Select a meal type to fetch a random recipe from AllRecipes (no max prep time).")
    meal_types = {
        "Breakfast": "https://www.allrecipes.com/recipes/78/breakfast-and-brunch/",
        "Lunch": "https://www.allrecipes.com/recipes/17561/lunch/",
        "Dinner": "https://www.allrecipes.com/recipes/17562/dinner/",
        "Snacks": "https://www.allrecipes.com/recipes/76/appetizers-and-snacks/"
    }
    meal_choice = st.selectbox("Meal Type", list(meal_types.keys()))

    if st.button("Find Recipe"):
        recipe = scrape_allrecipes(meal_types[meal_choice])

# 5) Drink by Personality (Wikipedia)
elif search_type == "Drink by Personality":
    personality_choice = st.selectbox("Pick your personality trait", list(PERSONALITY_TO_CUISINE.keys()))

    if st.button("Find Drink"):
        drink = suggest_beverage(personality_choice)

# ───────────────────────────────────────────────────────────
# Display the selected Recipe (Spoonacular or AllRecipes)
# ───────────────────────────────────────────────────────────
if recipe:
    st.subheader(f"Recommended Recipe: {recipe.get('title', 'No title')}")
    
    # Show image if available
    if recipe.get("image"):
        st.image(recipe["image"], width=400)
    
    # Show prep time
    st.write(f"### Total Preparation Time: {recipe.get('readyInMinutes', 'N/A')} minutes")

    # Show ingredients
    st.write("### Ingredients:")
    for ing in recipe.get("extendedIngredients", []):
        st.write(f"- {ing['original']}")

    # Show instructions
    st.write("### Instructions:")
    st.write(recipe.get("instructions", "No instructions available."))

    # Show nutrition if present
    if "nutrition" in recipe and "nutrients" in recipe["nutrition"]:
        nutrients_list = recipe["nutrition"]["nutrients"]
        if len(nutrients_list) > 0:
            st.write("### Nutrition Information:")
            for n in nutrients_list:
                st.write(f"- {n['name']}: {n['amount']} {n['unit']}")
        else:
            st.write("No nutrition data found.")

# ───────────────────────────────────────────────────────────
# Display the selected Drink (Wikipedia)
# ───────────────────────────────────────────────────────────
if drink:
    st.subheader(f"🍹 Suggested Drink: {drink}")

# Show a friendly message if no recipe/drink has been chosen yet
if not recipe and not drink:
    st.write("Feel free to pick an option above to discover a new recipe or a drink!")
