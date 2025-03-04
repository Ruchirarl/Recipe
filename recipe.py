import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Set page config
st.set_page_config(page_title="🍽 BiteByType - Personalized Meal Finder")

# Load API keys securely from Streamlit secrets
SPOONACULAR_API_KEY = st.secrets["SPOONACULAR_API_KEY"]
YELP_API_KEY = st.secrets["YELP_API_KEY"]

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

# Supported diets
diet_types = [
    "Gluten Free", "Ketogenic", "Vegetarian", "Lacto-Vegetarian",
    "Ovo-Vegetarian", "Vegan", "Pescetarian", "Paleo", "Primal",
    "Low FODMAP", "Whole30"
]

# Meal types for filtering
meal_types = {
    "Breakfast": "https://www.allrecipes.com/recipes/78/breakfast-and-brunch/",
    "Lunch": "https://www.allrecipes.com/recipes/17561/lunch/",
    "Dinner": "https://www.allrecipes.com/recipes/17562/dinner/",
    "Snacks": "https://www.allrecipes.com/recipes/76/appetizers-and-snacks/"
}

### Spoonacular API Fetch Function ###
@st.cache_data
def fetch_api(url, params):
    """Fetches data from Spoonacular API."""
    try:
        response = requests.get(url, params=params)
        return response.json() if response.status_code == 200 else None
    except requests.RequestException:
        return None

def get_recipe_by_personality(personality, diet, meal_type):
    """Fetch recipe by personality type and meal type from Spoonacular."""
    cuisine = PERSONALITY_TO_CUISINE.get(personality, ["Italian"])[0]
    url = "https://api.spoonacular.com/recipes/complexSearch"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "number": 3,  # Get multiple recipes
        "diet": diet,
        "cuisine": cuisine,
        "type": meal_type.lower(),  # Meal type filter (breakfast, lunch, dinner, etc.)
        "instructionsRequired": True
    }
    data = fetch_api(url, params)
    return data.get("results", []) if data else []

### AllRecipes Web Scraper ###
@st.cache_data
def scrape_allrecipes(meal_type_url):
    """Scrapes recipes from AllRecipes for the selected meal type."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(meal_type_url, headers=headers)
    
    if response.status_code != 200:
        return []

    soup = BeautifulSoup(response.text, "lxml")
    recipe_cards = soup.find_all("article", class_="fixed-recipe-card")

    recipes = []
    for card in recipe_cards:
        title_tag = card.find("span", class_="fixed-recipe-card__title-link")
        link_tag = card.find("a", class_="fixed-recipe-card__title-link")
        if title_tag and link_tag:
            recipes.append({"title": title_tag.get_text(strip=True), "url": link_tag.get("href")})
    
    return recipes

### Yelp API for Restaurant Recommendations ###
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

### Streamlit UI ###
st.title("🍽 BiteByType - Find Meals that Fit Your Personality")

st.markdown("""
## How It Works:
1. Choose your **Personality Trait** 🎭
2. Select a **Meal Type** 🍽
3. Pick a **Diet Preference** 🥗
4. Get **recipes from Spoonacular & AllRecipes**
5. Find nearby **restaurants** serving similar dishes! 🍽✨
""")

# Select personality trait
personality = st.selectbox("Select Your Personality Trait", list(PERSONALITY_TO_CUISINE.keys()), index=None)

# Select meal type
meal_type = st.selectbox("Choose a Meal Type", list(meal_types.keys()), index=None)

# Select diet preference
diet = st.selectbox("Choose Your Diet Preference", diet_types, index=None)

# Enter location for restaurant recommendations
location = st.text_input("Enter your location for restaurant recommendations (optional)")

if st.button("Find Recipes"):
    if personality and meal_type and diet:
        # Fetch Spoonacular Recipes
        spoonacular_recipes = get_recipe_by_personality(personality, diet, meal_type)

        # Scrape AllRecipes for additional recipes
        allrecipes_recipes = scrape_allrecipes(meal_types[meal_type])

        # Display Spoonacular Recipes
        if spoonacular_recipes:
            st.subheader("🍲 Recipes from Spoonacular")
            for recipe in spoonacular_recipes:
                st.write(f"**{recipe['title']}**")
                st.image(recipe.get("image", ""), width=300)
                st.write(f"[View Full Recipe](https://spoonacular.com/recipes/{recipe['title'].replace(' ', '-').lower()}-{recipe['id']})")

        # Display AllRecipes Recipes
        if allrecipes_recipes:
            st.subheader("🍽 Recipes from AllRecipes")
            for recipe in allrecipes_recipes:
                st.write(f"**[{recipe['title']}]({recipe['url']})**")

        # Fetch and display nearby restaurants if location is provided
        if location:
            restaurants = get_restaurants(location, PERSONALITY_TO_CUISINE.get(personality, ["Italian"])[0])
            if restaurants:
                st.subheader("🏢 Nearby Restaurants")
                for r in restaurants:
                    st.write(f"- {r['name']} ({r['rating']}⭐) - {r['location'].get('address1', 'Address not available')}")
            else:
                st.write("No nearby restaurants found.")
    else:
        st.warning("Please select Personality, Meal Type, and Diet to proceed!")
