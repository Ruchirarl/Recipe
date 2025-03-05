import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Setting Streamlit page title
st.set_page_config(page_title="🍽 BiteByType - Meals that fit your personality")

# Loading API keys from Streamlit secrets
SPOONACULAR_API_KEY = st.secrets["SPOONACULAR_API_KEY"]  # API key for recipes
YELP_API_KEY = st.secrets["YELP_API_KEY"]  # API key for restaurant search

# Displaying the app title
st.title("🍽 BiteByType - Meals that fit your personality")

# Displaying markdown text
st.markdown(
    """
    ## 🥗 Welcome to BiteByType!
    Discover recipes tailored to your personality, dietary preferences, and nutrition needs! 🥦🍲

    🔍 How It Works  
    - Choose a recipe By Personality 🎭, By Ingredient 🥑, or By Nutrients 🏋‍♂  
    - Get recipes that match your taste and lifestyle!  
    - Find restaurants nearby serving similar cuisines!  
    """
)

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

# Wikipedia Beverage Categories (Dynamically Scraped!)
@st.cache_data
def get_wikipedia_beverages():
    """Scrapes Wikipedia to get beverage data dynamically."""
    url = "https://en.wikipedia.org/wiki/Table_of_food_nutrients"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    # Find all tables in the Wikipedia page
    tables = soup.find_all("table", {"class": "wikitable"})
    
    # Extracting beverages table (this may change if Wikipedia updates structure)
    beverages_table = tables[15]  # Assuming the first table is Beverages

    df = pd.read_html(str(beverages_table))[0]  # Convert HTML table to DataFrame
    return df

# Fetch Wikipedia beverages
beverages_df = get_wikipedia_beverages()

# Suggest beverage based on personality from Wikipedia data
def suggest_beverage(personality):
    """Finds a Wikipedia beverage related to a personality."""
    if personality in PERSONALITY_TO_CUISINE:
        beverage_options = beverages_df["Food"].sample(n=1).values[0]  # Random drink
        return beverage_options
    return "Water"  # Default

# Diet Types
diet_types = [
    "Gluten Free", "Ketogenic", "Vegetarian", "Lacto-Vegetarian", "Ovo-Vegetarian", "Vegan",
    "Pescetarian", "Paleo", "Primal", "Low FODMAP", "Whole30"
]

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
    return get_recipe_details_by_id(data["results"][0]["id"]) if data and data.get("results") else None

def get_recipe_by_nutrients(nutrient, min_value, max_value, max_time):
    """Fetch a recipe based on nutrient range."""
    url = "https://api.spoonacular.com/recipes/findByNutrients"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        f"min{nutrient}": min_value,
        f"max{nutrient}": max_value,
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

## Streamlit UI

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

    elif search_type == "By Ingredient":
        ingredient = st.text_input("Enter an ingredient")
        max_time = st.slider("Max preparation time (minutes)", 5, 120, 30)
        if st.button("Find Recipe"):
            recipe = get_recipe_by_ingredient(ingredient, max_time)

    elif search_type == "By Nutrients":
        nutrient = st.selectbox("Choose a nutrient", ["Calories", "Protein", "Fat"])
        min_value = st.number_input(f"Min {nutrient}", min_value=0, value=100)
        max_value = st.number_input(f"Max {nutrient}", min_value=0, value=200)
        max_time = st.slider("Max preparation time (minutes)", 5, 120, 30)
        if st.button("Find Recipe"):
            recipe = get_recipe_by_nutrients(nutrient, min_value, max_value, max_time)

if recipe:
    st.subheader(f"Recommended Recipe: {recipe.get('title', 'No title')}")
    st.image(recipe.get("image", ""), width=400)
    st.write(f"### Total Preparation Time: {recipe.get('readyInMinutes', 'N/A')} minutes")

    if suggested_beverage:
        st.write(f"### Suggested Beverage: *{suggested_beverage}* 🍹 (From Wikipedia)")

else:
    st.write("Welcome! Choose a search method above to find a recipe that suits you.")