import streamlit as st
import requests
import wikipedia
import pandas as pd
from bs4 import BeautifulSoup

# API Keys (Load from Streamlit secrets)
SPOONACULAR_API_KEY = st.secrets["SPOONACULAR_API_KEY"]
YELP_API_KEY = st.secrets["YELP_API_KEY"]

# Streamlit App Configuration
st.set_page_config(page_title="🍽 BiteByType - Personalized Recipes")
st.title("🍽 BiteByType - Personalized Recipes")

st.markdown("""
    ## 🥗 Welcome to BiteByType!
    Discover personalized recipes tailored to your taste, diet, and nutritional needs. 🍲

    🔍 *How It Works:*
    - Search By Personality 🎭, By Ingredient 🥑, or By Nutrients 🏋‍♂.
    - Get recipes that match your lifestyle!
    - Find restaurants serving similar cuisines!

    Let's cook something amazing! 🍽✨
""")

# --- API Utility Function ---
@st.cache_data
def fetch_api(url, params):
    """Fetch data from an API and return JSON response."""
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: Status code {response.status_code}")
            return None
    except requests.RequestException as e:
        st.error(f"Request Exception: {e}")
        return None

# --- Wikipedia Data Function ---
@st.cache_data
def get_wiki_food_nutrients():
    """Fetch and parse the Wikipedia table of food nutrients."""
    try:
        url = "https://en.wikipedia.org/wiki/Table_of_food_nutrients"
        response = requests.get(url)
        if response.status_code != 200:
            return {"status": "error", "message": f"Failed to fetch page. Status code: {response.status_code}"}

        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table', {'class': 'wikitable'})

        if not tables:
            return {"status": "error", "message": "No tables found on the Wikipedia page"}

        df = pd.read_html(str(tables[0]))[0]  # Convert first table to DataFrame

        return {"status": "success", "data": df}

    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- Recipe Search Functions ---
def get_recipe_by_nutrients(nutrient, min_value, max_value, max_time):
    """Fetch recipes based on nutrient range."""
    wiki_data = get_wiki_food_nutrients()

    if wiki_data["status"] == "success":
        df = wiki_data["data"]
        df[nutrient] = pd.to_numeric(df[nutrient], errors='coerce')
        filtered_ingredients = df[(df[nutrient] >= min_value) & (df[nutrient] <= max_value)]["Food"].tolist()

        if not filtered_ingredients:
            st.write("No matching foods found.")
            return None

        ingredients = ", ".join(filtered_ingredients)

        # Fetch recipe
        url = "https://api.spoonacular.com/recipes/complexSearch"
        params = {
            "apiKey": SPOONACULAR_API_KEY,
            "includeIngredients": ingredients,
            "maxReadyTime": max_time,
            "number": 1,
            "instructionsRequired": True
        }

        data = fetch_api(url, params)

        if data and "results" in data and data["results"]:
            return get_recipe_details_by_id(data["results"][0]["id"])
        else:
            st.write("No recipes found with those ingredients.")
            return None
    else:
        st.write(f"Error fetching Wikipedia data: {wiki_data['message']}")
        return None

def get_recipe_details_by_id(recipe_id):
    """Fetch detailed recipe information by ID."""
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    params = {"apiKey": SPOONACULAR_API_KEY, "includeNutrition": True}
    return fetch_api(url, params)

def get_recipe_by_ingredient(ingredient):
    """Fetch a recipe based on a single ingredient."""
    url = "https://api.spoonacular.com/recipes/findByIngredients"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "ingredients": ingredient,
        "number": 1
    }
    data = fetch_api(url, params)

    if data:
        return get_recipe_details_by_id(data[0]["id"]) if data else None
    else:
        return None

def get_personality_recipe(personality):
    """Return a recipe based on personality type."""
    personality_recipes = {
        "Adventurous": "Mexican",
        "Health Conscious": "Salad",
        "Comfort Seeker": "Mac and Cheese",
        "Minimalist": "Stir Fry"
    }

    cuisine = personality_recipes.get(personality, "Vegetarian")
    url = "https://api.spoonacular.com/recipes/complexSearch"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "cuisine": cuisine,
        "number": 1
    }

    data = fetch_api(url, params)
    return get_recipe_details_by_id(data["results"][0]["id"]) if data and "results" in data else None

# --- Yelp Restaurant Search ---
def find_restaurants(location, cuisine):
    """Fetch nearby restaurants serving the selected cuisine."""
    url = "https://api.yelp.com/v3/businesses/search"
    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    params = {"term": cuisine, "location": location, "limit": 5}

    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get("businesses", [])
    else:
        return []

# --- Streamlit UI ---
search_type = st.radio(
    "## How would you like to find a recipe?",
    ["By Nutrients", "By Ingredient", "By Personality", "Find Restaurants"],
    index=0
)

if search_type == "By Nutrients":
    nutrient = st.selectbox("Select Nutrient", ["calories", "protein", "fat"])
    min_value = st.number_input("Min Value", 10, 500, 100)
    max_value = st.number_input("Max Value", 10, 500, 200)
    max_time = st.slider("Max Time (minutes)", 5, 120, 30)

    if st.button("Find Recipe"):
        recipe = get_recipe_by_nutrients(nutrient, min_value, max_value, max_time)
        if recipe:
            st.write(recipe)

elif search_type == "By Ingredient":
    ingredient = st.text_input("Enter an ingredient (e.g., chicken, broccoli)")
    if st.button("Find Recipe"):
        recipe = get_recipe_by_ingredient(ingredient)
        if recipe:
            st.write(recipe)

elif search_type == "By Personality":
    personality = st.selectbox("Select Personality Type", ["Adventurous", "Health Conscious", "Comfort Seeker", "Minimalist"])
    if st.button("Find Recipe"):
        recipe = get_personality_recipe(personality)
        if recipe:
            st.write(recipe)

elif search_type == "Find Restaurants":
    location = st.text_input("Enter your city or ZIP code")
    cuisine = st.text_input("Enter cuisine type (e.g., Italian, Mexican)")
    if st.button("Find Restaurants"):
        restaurants = find_restaurants(location, cuisine)
        for r in restaurants:
            st.write(f"### {r['name']}")
            st.write(f"📍 {r['location']['address1']}")
            st.write(f"⭐ Rating: {r['rating']} ({r['review_count']} reviews)")