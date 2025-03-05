import streamlit as st
import requests
import os
from bs4 import BeautifulSoup
import pandas as pd
import random

# Setting up the Streamlit page with a friendly title
st.set_page_config(page_title="🍽 BiteByType - Meals that fit your personality")

# Loading API keys safely from Streamlit secrets
SPOONACULAR_API_KEY = st.secrets["SPOONACULAR_API_KEY"]
YELP_API_KEY = st.secrets["YELP_API_KEY"]  # Not used here, but available if needed

# Displaying the main title and explaining the app
st.title("🍽 BiteByType - Meals that fit your personality")
st.markdown(
    """
    ## 🥗 Welcome to BiteByType!
    Here, you can explore **five different ways** to discover new recipes or drinks. 
    Choose an approach below and let the app guide you!

    1. **By Personality** (Spoonacular)
    2. **By Nutrients** (Spoonacular)
    3. **By Ingredient** (Spoonacular)
    4. **By Meal Type** (AllRecipes)
    5. **Drink by Personality** (Wikipedia)
    """
)

# Personality-to-cuisine mapping for Spoonacular recipe suggestions
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

# List of possible diet types used by Spoonacular
diet_types = [
    "Gluten Free", "Ketogenic", "Vegetarian", "Lacto-Vegetarian",
    "Ovo-Vegetarian", "Vegan", "Pescetarian", "Paleo",
    "Primal", "Low FODMAP", "Whole30"
]

# Using Wikipedia to find beverages for the "Drink by Personality" option
@st.cache_data
def get_wikipedia_beverages():
    """
    Scraping Wikipedia's 'Table of food nutrients' page to 
    retrieve a list of beverages from the 16th wikitable.
    """
    url = "https://en.wikipedia.org/wiki/Table_of_food_nutrients"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")
    
    tables = soup.find_all("table", {"class": "wikitable"})
    beverages_table = tables[15]
    
    df = pd.read_html(str(beverages_table))[0]
    df.columns = ["Food", "Measure", "Grams", "Calories", "Protein", "Carb", "Fiber", "Fat", "Sat_fat"]
    
    # Excluding any header row labeled 'Beverages'
    df = df[df["Food"] != "Beverages"]
    return df

beverages_df = get_wikipedia_beverages()

def suggest_beverage(personality):
    """
    Picking a random beverage from our Wikipedia table if the personality is valid.
    Returning 'Water' if the personality is unrecognized.
    """
    if personality in PERSONALITY_TO_CUISINE:
        return beverages_df["Food"].sample(n=1).values[0]
    return "Water"

# Using AllRecipes to fetch recipes by meal type (e.g., Breakfast, Lunch, Dinner, Snacks)
@st.cache_data
def scrape_allrecipes(meal_type_url):
    """
    Grabbing a random recipe from AllRecipes for a specific meal type.
    Parsing the HTML to gather title, image, ingredients, instructions, 
    and any available nutrition info.
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
    
    title_tag = recipe_soup.find("h1")
    title = title_tag.text.strip() if title_tag else "Unknown Recipe"
    
    image_tag = recipe_soup.select_one("img.card__img")
    image_url = image_tag.get("data-src", image_tag.get("src", "")) if image_tag else ""
    
    raw_ingredients = [i.get_text(strip=True) for i in recipe_soup.select(".mm-recipes-structured-ingredients__list-item")]
    extended_ingredients = [{"original": ing} for ing in raw_ingredients]
    
    steps = [s.get_text(strip=True) for s in recipe_soup.select(".mntl-sc-block-html")]
    instructions = "\n".join(steps) if steps else "No instructions available."
    
    parsed_nutrients = []
    nutrition_table = recipe_soup.select_one(".mm-recipes-nutrition-facts-label__table")
    if nutrition_table:
        for row in nutrition_table.find_all("tr"):
            cols = row.find_all("td")
            if len(cols) == 2:
                n_name = cols[0].get_text(strip=True)
                n_value = cols[1].get_text(strip=True)
                parsed_nutrients.append({
                    "name": n_name,
                    "amount": n_value,
                    "unit": ""
                })
    
    return {
        "title": title,
        "image": image_url,
        "readyInMinutes": "N/A (AllRecipes)",
        "extendedIngredients": extended_ingredients,
        "instructions": instructions,
        "nutrition": {
            "nutrients": parsed_nutrients
        }
    }

# Simplifying our calls to the Spoonacular API
@st.cache_data
def fetch_api(url, params):
    """
    Calling API with given params and returning JSON data if it succeeds.
    """
    try:
        resp = requests.get(url, params=params)
        if resp.status_code == 200:
            return resp.json()
        return None
    except requests.RequestException:
        return None

def get_recipe_details_by_id(recipe_id):
    """
    Retrieving full details about a Spoonacular recipe by ID,
    including ingredients, instructions, and nutrition.
    """
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    params = {"apiKey": SPOONACULAR_API_KEY, "includeNutrition": True}
    return fetch_api(url, params)

def get_recipe_by_personality(personality, diet):
    """
    Getting a random Spoonacular recipe that matches a personality-based cuisine 
    and aligns with a selected diet.
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

def get_recipe_by_nutrients(nutrient, min_val, max_val, max_time):
    """
    Searching for a Spoonacular recipe by specifying nutrient constraints 
    (like 'Calories', 'Protein', or 'Fat') and a max cooking time.
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

def get_recipe_by_ingredient(ingredient, max_time):
    """
    Finding a Spoonacular recipe that includes a certain ingredient and 
    stays within a chosen maximum preparation time.
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
        return get_recipe_details_by_id(data["results"][0]["id"])
    return None

# Providing five main search approaches
search_type = st.radio(
    "## Please choose how you'd like to find a recipe or drink:",
    [
        "By Personality",       # 1
        "By Nutrients",         # 2
        "By Ingredient",        # 3
        "By Meal Type",         # 4
        "Drink by Personality"  # 5
    ]
)

recipe = None
drink = None

# 1) By Personality (Spoonacular)
if search_type == "By Personality":
    personality = st.selectbox("Pick your personality trait", list(PERSONALITY_TO_CUISINE.keys()))
    diet = st.selectbox("Pick a diet preference", diet_types)

    if st.button("Find Recipe"):
        recipe = get_recipe_by_personality(personality, diet)

# 2) By Nutrients (Spoonacular)
elif search_type == "By Nutrients":
    nutrient = st.selectbox("Nutrient to filter by", ["Calories", "Protein", "Fat"])
    min_val = st.number_input(f"Min {nutrient}", min_value=10, value=100)
    max_val = st.number_input(f"Max {nutrient}", min_value=10, value=500)
    max_time = st.slider("Max preparation time (minutes)", 5, 120, 30)

    if st.button("Find Recipe"):
        recipe = get_recipe_by_nutrients(nutrient, min_val, max_val, max_time)

# 3) By Ingredient (Spoonacular)
elif search_type == "By Ingredient":
    ingredient = st.text_input("Type in an ingredient (e.g., chicken, tofu, etc.)")
    max_time = st.slider("Max preparation time (minutes)", 5, 120, 30)

    if st.button("Find Recipe"):
        recipe = get_recipe_by_ingredient(ingredient, max_time)

# 4) By Meal Type (AllRecipes)
elif search_type == "By Meal Type":
    st.write("Selecting a meal type below to fetch a random recipe from AllRecipes.")
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
    personality_for_drink = st.selectbox("Pick your personality trait", list(PERSONALITY_TO_CUISINE.keys()))

    if st.button("Find Drink"):
        drink = suggest_beverage(personality_for_drink)

# Showing the final recipe if found
if recipe:
    st.subheader(f"Recommended Recipe: {recipe.get('title', 'No title')}")
    if recipe.get("image"):
        st.image(recipe["image"], width=400)
    st.write(f"### Total Preparation Time: {recipe.get('readyInMinutes', 'N/A')} minutes")

    st.write("### Ingredients:")
    for ing in recipe.get("extendedIngredients", []):
        st.write(f"- {ing['original']}")

    st.write("### Instructions:")
    st.write(recipe.get("instructions", "No instructions available."))

    if "nutrition" in recipe and "nutrients" in recipe["nutrition"]:
        nutrients_list = recipe["nutrition"]["nutrients"]
        if nutrients_list:
            st.write("### Nutrition Information:")
            for n in nutrients_list:
                st.write(f"- {n['name']}: {n['amount']} {n['unit']}")
        else:
            st.write("No nutrition data available.")

# Displaying the beverage 
if drink:
    st.subheader(f"🍹 Suggested Drink: {drink}")

if not recipe and not drink:
    st.write("Pick an option above to start exploring recipes or beverages!")
