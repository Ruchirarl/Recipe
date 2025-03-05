import streamlit as st  # Importing Streamlit for building the web app
import requests  # Importing requests to make API calls
import os  # Importing os to manage environment variables (not needed here since Streamlit secrets are used)
from bs4 import BeautifulSoup  # Importing BeautifulSoup for web scraping
import random  # Importing random to select recipes randomly

# Setting Streamlit page title and favicon
st.set_page_config(page_title="🍽 BiteByType - Meals that fit your personality")

# Loading API keys securely from Streamlit secrets
SPOONACULAR_API_KEY = st.secrets["SPOONACULAR_API_KEY"]  # API key for fetching recipes
YELP_API_KEY = st.secrets["YELP_API_KEY"]  # API key for fetching restaurant recommendations

# Displaying the app title on the web page
st.title("🍽 BiteByType - Meals that fit your personality")

st.markdown(
    """
    ## 🥗 Welcome to BiteByType!
    BiteByType is your personalized meal finder, helping you discover recipes tailored to your personality, dietary preferences, and nutritional needs! 🥦🍲
    
    🔍 How It Works:
    - Choose a recipe By Personality 🎭, By Ingredient 🥑, or By Nutrients 🏋‍♂.
    - Find recipes that match your taste and lifestyle!
    - Explore restaurants nearby serving similar cuisines!
    
    Let's find your next favorite meal! 🍽✨
    """
)

# Mapping personality traits to specific cuisines
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

# List of supported diet types for filtering recipes
diet_types = [
    "Gluten Free", "Ketogenic", "Vegetarian", "Lacto-Vegetarian", "Ovo-Vegetarian", "Vegan",
    "Pescetarian", "Paleo", "Primal", "Low FODMAP", "Whole30"
]

@st.cache_data
def fetch_api(url, params):
    """Fetches data from an API and returns JSON response."""
    try:
        response = requests.get(url, params=params)
        return response.json() if response.status_code == 200 else None
    except requests.RequestException:
        return None

def get_recipe_by_personality(personality, diet):
    """Fetch a recipe based on personality and diet preferences."""
    cuisine = PERSONALITY_TO_CUISINE.get(personality, ["Italian"])[0]
    url = "https://api.spoonacular.com/recipes/random"
    params = {"apiKey": SPOONACULAR_API_KEY, "number": 1, "diet": diet, "cuisine": cuisine, "instructionsRequired": True}
    data = fetch_api(url, params)
    return data.get("recipes", [None])[0] if data else None

def get_recipe_by_ingredient(ingredient, max_time):
    """Fetch a recipe based on an ingredient and max preparation time."""
    url = "https://api.spoonacular.com/recipes/complexSearch"
    params = {"apiKey": SPOONACULAR_API_KEY, "includeIngredients": ingredient, "maxReadyTime": max_time, "number": 1}
    data = fetch_api(url, params)
    return get_recipe_details_by_id(data["results"][0]["id"]) if data and data.get("results") else None

def get_recipe_by_nutrients(nutrient, min_value, max_value, max_time):
    """Fetch a recipe based on nutritional content."""
    url = "https://api.spoonacular.com/recipes/findByNutrients"
    params = {"apiKey": SPOONACULAR_API_KEY, f"min{nutrient}": min_value, f"max{nutrient}": max_value, "maxReadyTime": max_time, "number": 1}
    data = fetch_api(url, params)
    return get_recipe_details_by_id(data[0]["id"]) if data else None

def get_recipe_details_by_id(recipe_id):
    """Fetch detailed recipe information by ID."""
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    params = {"apiKey": SPOONACULAR_API_KEY, "includeNutrition": True}
    return fetch_api(url, params)

@st.cache_data
def get_restaurants(location, cuisine):
    """Fetch nearby restaurants using Yelp API."""
    url = "https://api.yelp.com/v3/businesses/search"
    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    params = {"term": cuisine, "location": location, "limit": 5}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        return response.json().get("businesses", []) if response.status_code == 200 else []
    except requests.RequestException:
        return []

# Search Type UI
search_type = st.radio("## How would you like to find a recipe?", ["By Personality", "By Ingredient", "By Nutrients"])

recipe = None
if search_type == "By Personality":
    personality = st.selectbox("Select your personality trait", list(PERSONALITY_TO_CUISINE.keys()))
    diet = st.selectbox("Choose your diet preference", diet_types)
    if st.button("Find Recipe"):
        recipe = get_recipe_by_personality(personality, diet)

elif search_type == "By Ingredient":
    ingredient = st.text_input("Enter an ingredient")
    max_time = st.slider("Max preparation time (minutes)", 5, 120, 30)
    if st.button("Find Recipe"):
        recipe = get_recipe_by_ingredient(ingredient, max_time)

elif search_type == "By Nutrients":
    nutrient = st.selectbox("Choose a nutrient", ["Calories", "Protein", "Fat"])
    min_value = st.number_input(f"Min {nutrient}", min_value=10, value=100)
    max_value = st.number_input(f"Max {nutrient}", min_value=10, value=500)
    max_time = st.slider("Max preparation time (minutes)", 5, 120, 30)
    if st.button("Find Recipe"):
        recipe = get_recipe_by_nutrients(nutrient, min_value, max_value, max_time)

# 🔥 **AllRecipes Added Separately**
@st.cache_data
def scrape_allrecipes(meal_type_url):
    """Scrapes a random recipe from AllRecipes for the selected meal type."""
    response = requests.get(meal_type_url)
    soup = BeautifulSoup(response.text, "lxml")
    all_recipe_links = soup.select("a[href*='/recipe/']")
    recipe_url = random.choice(all_recipe_links)["href"]
    recipe_response = requests.get(recipe_url)
    recipe_soup = BeautifulSoup(recipe_response.text, "lxml")

    return {
        "title": recipe_soup.find("h1").text.strip(),
        "image": recipe_soup.select_one("img.card__img")["src"],
        "ingredients": [ing.get_text(strip=True) for ing in recipe_soup.select(".mm-recipes-structured-ingredients__list-item")],
        "instructions": [step.get_text(strip=True) for step in recipe_soup.select(".mntl-sc-block-html")]
    }

st.markdown("## 🍽 Get a Random Recipe from AllRecipes")
meal_types = {"Breakfast": "...", "Lunch": "...", "Dinner": "...", "Snacks": "..."}

selected_meal_type = st.selectbox("Choose a Meal Type", list(meal_types.keys()))
if st.button("Get AllRecipes Recipe"):
    allrecipes_recipe = scrape_allrecipes(meal_types[selected_meal_type])
    st.subheader(f"🍽 AllRecipes Recommended Recipe: {allrecipes_recipe.get('title')}")
    st.image(allrecipes_recipe["image"], width=400)
