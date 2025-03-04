import streamlit as st
import requests
import wikipedia
from bs4 import BeautifulSoup

# API Keys (Load from Streamlit secrets)
SPOONACULAR_API_KEY = st.secrets["SPOONACULAR_API_KEY"]
YELP_API_KEY = st.secrets["YELP_API_KEY"]

# Streamlit App Configuration
st.set_page_config(page_title="🍽 BiteByType - Personalized Recipes")
st.title("🍽 BiteByType - Personalized Recipes")

st.markdown("""
    ## 🥗 Welcome to BiteByType!
    BiteByType is your personalized meal finder, helping you discover recipes tailored to your personality, dietary preferences, and nutritional needs! 🥦🍲

    🔍 How It Works:
    - Choose a recipe By Personality 🎭, By Ingredient 🥑, or By Nutrients 🏋‍♂.
    - Find recipes that match your taste and lifestyle!
    - Explore restaurants nearby serving similar cuisines!

    Let's find your next favorite meal! 🍽✨
""")

# Personality-Cuisine Mapping
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

# --- API Utility Function ---
@st.cache_data
def fetch_api(url, params):
    """Fetches data from an API and returns JSON response."""
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
        page = wikipedia.page("List of food nutrients")
        soup = BeautifulSoup(page.html(), 'html.parser')
        tables = soup.find_all('table', {'class': 'wikitable'})

        if tables:
            nutrient_table = tables[0]
            data = []
            rows = nutrient_table.find_all('tr')
            headers = [th.text.strip() for th in rows[0].find_all('th')]
            for row in rows[1:]:
                cols = row.find_all('td')
                cols = [ele.text.strip() for ele in cols]
                data.append(dict(zip(headers, cols)))
            return {"status": "success", "data": data}
        else:
            return {"status": "error", "message": "No tables found on the Wikipedia page"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- Recipe Search Functions ---
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
    return data.get("recipes", [None])[0] if data else None

def get_recipe_by_ingredient(ingredient, max_time):
    """Fetch a recipe based on ingredients and time preference."""
    url = "https://api.spoonacular.com/recipes/complexSearch"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "includeIngredients": ingredient,
        "maxReadyTime": max_time,
        "number": 1
    }
    data = fetch_api(url, params)
    if data and "results" in data and data["results"]:
        return get_recipe_details_by_id(data["results"][0]["id"])
    return None

def get_recipe_by_nutrients(nutrient, min_value, max_value, max_time):
    """Fetch recipes based on nutrient range."""
    url = "https://api.spoonacular.com/recipes/findByNutrients"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        nutrient.lower(): min_value,
        f"max{nutrient}": max_value,
        "number": 1
    }
    data = fetch_api(url, params)
    if data:
        return get_recipe_details_by_id(data[0]["id"])
    return None

def get_recipe_details_by_id(recipe_id):
    """Fetch detailed recipe information by ID."""
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    params = {"apiKey": SPOONACULAR_API_KEY, "includeNutrition": True}
    return fetch_api(url, params)

def get_restaurants(location, cuisine):
    """Fetch nearby restaurants using Yelp API."""
    url = "https://api.yelp.com/v3/businesses/search"
    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    params = {"term": cuisine, "location": location, "limit": 5}
    return fetch_api(url, params)

# --- Streamlit UI ---
search_type = st.radio("## How would you like to find a recipe?", ["By Personality", "By Ingredient", "By Nutrients"])

if search_type == "By Personality":
    personality = st.selectbox("Select Personality", list(PERSONALITY_TO_CUISINE.keys()))
    diet = st.selectbox("Select Diet", diet_types)
elif search_type == "By Ingredient":
    ingredient = st.text_input("Enter Ingredient")
    max_time = st.slider("Max Time (minutes)", 5, 120, 30)
elif search_type == "By Nutrients":
    nutrient = st.selectbox("Select Nutrient", ["Calories", "Protein", "Fat"])
    min_value = st.number_input("Min Value", 10, 500, 100)
    max_value = st.number_input("Max Value", 10, 500, 200)

location = st.text_input("Enter your location for restaurant recommendations")

if st.button("Find Recipe"):
    # Call appropriate function based on selection