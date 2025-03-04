import streamlit as st  # Importing Streamlit for building the web app
import requests  # Importing requests to make API calls
from bs4 import BeautifulSoup
import random

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
    - Choose a recipe By Personality 🎭, By Ingredient 🥑, By Nutrients 🏋‍♂, or By Meal Type 🍽.
    - Find recipes that match your taste and lifestyle!
    - Explore restaurants nearby serving similar cuisines!
    
    Let's find your next favorite meal! 🍽✨
    """
)

# Your exact mapping for personality traits and cuisines
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

diet_types = [
    "Gluten Free", "Ketogenic", "Vegetarian", "Lacto-Vegetarian", "Ovo-Vegetarian", "Vegan",
    "Pescetarian", "Paleo", "Primal", "Low FODMAP", "Whole30"
]

@st.cache_data
def fetch_api(url, params):
    """Fetches data from Spoonacular API."""
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            return data if data else None
        else:
            return None
    except requests.RequestException:
        return None

def get_recipe_by_personality(personality, diet):
    """Fetch a recipe based on personality and diet preferences."""
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
    return data["recipes"][0] if data and "recipes" in data and data["recipes"] else None

def get_recipe_by_ingredient(ingredient, max_time):
    """Fetch a recipe based on an ingredient and preparation time."""
    url = "https://api.spoonacular.com/recipes/complexSearch"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "includeIngredients": ingredient,
        "maxReadyTime": max_time,
        "number": 1,
        "instructionsRequired": True
    }
    data = fetch_api(url, params)
    return get_recipe_details_by_id(data["results"][0]["id"]) if data and "results" in data and data["results"] else None

def get_recipe_by_nutrients(nutrient, min_value, max_value, max_time):
    """Fetch a recipe based on nutritional content."""
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
    return get_recipe_details_by_id(data[0]["id"]) if data else None

def get_recipe_details_by_id(recipe_id):
    """Fetch detailed recipe information by ID."""
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "includeNutrition": True
    }
    return fetch_api(url, params)

# ✅ Adding AllRecipes without changing anything else
meal_types = {
    "Breakfast": "https://www.allrecipes.com/recipes/78/breakfast-and-brunch/",
    "Lunch": "https://www.allrecipes.com/recipes/17561/lunch/",
    "Dinner": "https://www.allrecipes.com/recipes/17562/dinner/",
    "Snacks": "https://www.allrecipes.com/recipes/76/appetizers-and-snacks/"
}

def scrape_allrecipes(meal_type_url):
    """Scrapes a random recipe from AllRecipes for the selected meal type."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(meal_type_url, headers=headers, timeout=10)
    if response.status_code != 200:
        st.error("Failed to fetch meal type page.")
        return None

    soup = BeautifulSoup(response.text, "lxml")
    all_recipe_links = soup.select("a[href*='/recipe/']")
    if not all_recipe_links:
        st.warning("No recipes found in AllRecipes. Try another category.")
        return None

    recipe_url = random.choice(all_recipe_links)["href"]
    recipe_response = requests.get(recipe_url, headers=headers, timeout=10)
    if recipe_response.status_code != 200:
        st.error("Failed to fetch the recipe page.")
        return None

    recipe_soup = BeautifulSoup(recipe_response.text, "lxml")
    title = recipe_soup.find("h1").text.strip() if recipe_soup.find("h1") else "Unknown Recipe"
    image_tag = recipe_soup.select_one("img.card__img")
    image_url = image_tag.get("data-src", image_tag.get("src", "")) if image_tag else ""
    ingredients = [ing.get_text(strip=True) for ing in recipe_soup.select(".mm-recipes-structured-ingredients__list-item")]
    instructions = [step.get_text(strip=True) for step in recipe_soup.select(".mntl-sc-block-html")]

    return {"title": title, "image": image_url, "ingredients": ingredients, "instructions": instructions}

# ✅ Streamlit UI (Now with Meal Type option)
search_type = st.radio("## How would you like to find a recipe?", ["By Personality", "By Ingredient", "By Nutrients", "By Meal Type"])
recipe = None

if search_type == "By Personality":
    personality = st.selectbox("Select Your Personality Trait", list(PERSONALITY_TO_CUISINE.keys()))
    diet = st.selectbox("Choose Your Diet Preference", diet_types)
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

elif search_type == "By Meal Type":
    meal_type = st.selectbox("Choose a Meal Type", list(meal_types.keys()))
    if st.button("Find Recipe"):
        recipe = scrape_allrecipes(meal_types[meal_type])

st.write("🚀 Try selecting options to discover recipes!")
