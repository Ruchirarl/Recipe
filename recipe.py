import streamlit as st
import requests
import wikipedia
from bs4 import BeautifulSoup

# Load API Keys from Streamlit secrets
SPOONACULAR_API_KEY = st.secrets["SPOONACULAR_API_KEY"]
YELP_API_KEY = st.secrets["YELP_API_KEY"]

# Streamlit App Configuration
st.set_page_config(page_title="🍽 BiteByType - Personalized Recipes")
st.title("🍽 BiteByType - Personalized Recipes")

# --- Welcome Message ---
st.markdown("""
    ## 🥗 Welcome to BiteByType!
    Discover recipes tailored to your *personality, dietary preferences, and nutrition needs*! 🥦🍲

    🔍 *How It Works*  
    - Choose a recipe By Personality 🎭, By Ingredient 🥑, By Nutrients 🏋‍♂, or Wikipedia Search 📖  
    - Get recipes that match your taste and lifestyle!  
    - Find nearby restaurants serving similar cuisines!  
""")

# --- Personality to Cuisine Mapping ---
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

# --- Wikipedia Recipe Search ---
def get_wikipedia_recipe(query):
    """Fetch a recipe summary from Wikipedia."""
    try:
        page = wikipedia.page(query)
        return page.summary[:1000] + "..."  # Limit text length
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Multiple results found: {e.options}"
    except wikipedia.exceptions.PageError:
        return "Recipe not found on Wikipedia."
    except Exception as e:
        return f"Error fetching Wikipedia: {e}"

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

# --- Restaurant Search ---
@st.cache_data
def get_restaurants(location, cuisine):
    """Fetch nearby restaurants using Yelp API."""
    url = "https://api.yelp.com/v3/businesses/search"
    headers = {
        "Authorization": f"Bearer {YELP_API_KEY}"
    }
    params = {
        "term": cuisine,
        "location": location,
        "limit": 5
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        return response.json().get("businesses", []) if response.status_code == 200 else []
    except requests.RequestException:
        return []

# --- Streamlit UI ---
search_type = st.radio(
    "## How would you like to find a recipe?",
    ["By Personality", "By Ingredient", "By Nutrients", "Wikipedia Search"],
    index=None
)

recipe = None

if search_type:
    if search_type == "By Personality":
        personality = st.selectbox(
            "Select your dominant personality trait",
            list(PERSONALITY_TO_CUISINE.keys()),
            index=None
        )
        diet = st.selectbox(
            "Choose your diet preference",
            diet_types,
            index=None
        )
        if st.button("Find Recipe"):
            recipe = get_recipe_by_personality(personality, diet)

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

    elif search_type == "Wikipedia Search":
        wiki_query = st.text_input("Enter the recipe name to search on Wikipedia")
        if st.button("Search Wikipedia"):
            summary = get_wikipedia_recipe(wiki_query)
            st.write(summary)

if recipe:
    st.subheader(f"Recommended Recipe: {recipe.get('title', 'No title')}")
    st.image(recipe.get("image", ""), width=400)
    st.write(f"### *Total Preparation Time:* {recipe.get('readyInMinutes', 'N/A')} minutes")
    st.write("### Ingredients:")
    st.write("\n".join(f"- {i['original']}" for i in recipe.get("extendedIngredients", [])))
    st.write("### Instructions:")
    st.write(recipe.get("instructions", "No instructions available."))

else:
    st.write("Welcome! Choose a search method above to find a recipe that suits you.")