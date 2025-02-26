import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Set Streamlit page title and favicon
st.set_page_config(page_title="🍽 BiteByType - Meals that fit your personality")

# Load API keys from Streamlit Cloud secrets
SPOONACULAR_API_KEY = st.secrets["SPOONACULAR_API_KEY"]
YELP_API_KEY = st.secrets["YELP_API_KEY"]

# App Title
st.title("🍽 BiteByType - Meals that fit your personality")

st.markdown(
    """
    ## 🥗 Welcome to BiteByType!
    Discover personalized recipes based on your personality, diet, or nutrition needs! 🥦🍲

    🔍 **How It Works:**
    - Choose a recipe **By Personality 🎭, By Ingredient 🥑, or By Nutrients 🏋‍♂**.
    - Find **recipes that match your taste and lifestyle!**
    - Explore **nearby restaurants serving similar cuisines!**
    """
)

# Personality-to-cuisine mapping
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
    """Fetches data from an API and returns JSON response."""
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except requests.RequestException:
        return None

@st.cache_data
def scrape_allrecipes():
    """Scrape popular recipes from Allrecipes."""
    url = "https://www.allrecipes.com/recipes/"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    recipes = []
    for card in soup.find_all("a", class_="card__titleLink"):
        recipes.append({
            "title": card.text.strip(),
            "url": card["href"]
        })
    return recipes[:5]  # Return top 5 recipes

@st.cache_data
def scrape_nutrient_table():
    """Scrape nutritional information from Wikipedia."""
    url = "https://en.wikipedia.org/wiki/Table_of_food_nutrients"
    response = requests.get(url)
    soup = BeautifulSoup(response.text, "html.parser")

    table = soup.find("table", {"class": "wikitable"})
    rows = table.find_all("tr")

    headers = [th.text.strip() for th in rows[0].find_all("th")]
    data = []
    for row in rows[1:]:
        cols = row.find_all("td")
        data.append([col.text.strip() for col in cols])

    return pd.DataFrame(data, columns=headers)

st.write("### 🍴 Popular Recipes from Allrecipes")
popular_recipes = scrape_allrecipes()
for recipe in popular_recipes:
    st.write(f"- [{recipe['title']}]({recipe['url']})")

st.write("### 🥦 Nutritional Information (Per 100g)")
nutrient_table = scrape_nutrient_table()
st.dataframe(nutrient_table.head(10))

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
    """Fetch a recipe based on an ingredient and prep time."""
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
    """Fetch a recipe based on nutrient levels."""
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
    """Fetch full recipe details using recipe ID."""
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

## Streamlit UI
search_type = st.radio("## How would you like to find a recipe?", ["By Personality", "By Ingredient", "By Nutrients"], index=None)

recipe = None

if search_type:
    if search_type == "By Personality":
        personality = st.selectbox("Select your dominant personality trait", list(PERSONALITY_TO_CUISINE.keys()), index=None)
        diet = st.selectbox("Choose your diet preference", diet_types, index=None)
    
    elif search_type == "By Ingredient":
        ingredient = st.text_input("Enter an ingredient")
        max_time = st.slider("Max preparation time (minutes)", 5, 120, 30)

    elif search_type == "By Nutrients":
        nutrient = st.selectbox("Choose a nutrient", ["Calories", "Protein", "Fat"])
        min_value = st.number_input(f"Min {nutrient} (10)", min_value=10, value=100)
        max_value = st.number_input(f"Max {nutrient} (100)", min_value=10, value=100)
        max_time = st.slider("Max preparation time (minutes)", 5, 120, 30)

    if st.button("Find Recipe"):
        if search_type == "By Personality":
            recipe = get_recipe_by_personality(personality, diet)
        elif search_type == "By Ingredient":
            recipe = get_recipe_by_ingredient(ingredient, max_time)
        elif search_type == "By Nutrients":
            recipe = get_recipe_by_nutrients(nutrient, min_value, max_value, max_time)

if recipe:
    st.subheader(f"Recommended Recipe: {recipe.get('title', 'No title')}")
    st.image(recipe.get("image", ""), width=400)

else:
    st.write("Welcome! Choose a search method above to find a recipe that suits you.")