import streamlit as st
import requests
from bs4 import BeautifulSoup
import pandas as pd

# Set page config
st.set_page_config(page_title="🍽 BiteByType - Personalized Meal Finder")

# Load API keys securely from Streamlit secrets
SPOONACULAR_API_KEY = st.secrets["SPOONACULAR_API_KEY"]
YELP_API_KEY = st.secrets["YELP_API_KEY"]

# Meal types mapped to AllRecipes URLs
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

def get_recipe_by_personality(personality, diet):
    """Fetch recipe by personality type from Spoonacular."""
    url = "https://api.spoonacular.com/recipes/random"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "number": 1,
        "diet": diet,
        "instructionsRequired": True
    }
    data = fetch_api(url, params)
    return data.get("recipes", [None])[0] if data else None

### AllRecipes Web Scraper ###
@st.cache_data
def scrape_allrecipes(meal_type_url):
    """Scrapes a full recipe from AllRecipes for the selected meal type."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(meal_type_url, headers=headers)
    
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "lxml")
    
    # Find the first recipe link
    first_recipe_card = soup.find("article", class_="fixed-recipe-card")
    if not first_recipe_card:
        return None

    title_tag = first_recipe_card.find("span", class_="fixed-recipe-card__title-link")
    link_tag = first_recipe_card.find("a", class_="fixed-recipe-card__title-link")

    if not title_tag or not link_tag:
        return None

    recipe_title = title_tag.get_text(strip=True)
    recipe_url = link_tag.get("href")

    # Now fetch the detailed recipe page
    recipe_response = requests.get(recipe_url, headers=headers)
    if recipe_response.status_code != 200:
        return None

    recipe_soup = BeautifulSoup(recipe_response.text, "lxml")

    # Extract ingredients
    ingredients = [ing.get_text(strip=True) for ing in recipe_soup.find_all("span", class_="ingredients-item-name")]

    # Extract instructions
    instructions = [step.get_text(strip=True) for step in recipe_soup.find_all("div", class_="paragraph")]

    # Extract image
    image_tag = recipe_soup.find("img", class_="ugc-photo")
    image_url = image_tag["src"] if image_tag else ""

    return {
        "title": recipe_title,
        "image": image_url,
        "ingredients": ingredients,
        "instructions": instructions
    }

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
1. **Choose a search method:** Personality, Ingredient, Nutrients, or Meal Type.
2. **Get recipes** from **Spoonacular** or **AllRecipes**.
3. **Find nearby restaurants** serving similar dishes!
""")

# Select search method
search_type = st.radio("## Choose a Search Method", ["By Personality", "By Ingredient", "By Nutrients", "By Meal Type"])

# Initialize recipe variable
recipe = None

# Handle search type selection
if search_type == "By Personality":
    personality = st.selectbox("Select Your Personality Trait", ["Openness", "Conscientiousness", "Extraversion", "Agreeableness"])
    diet = st.selectbox("Choose Your Diet Preference", ["Vegetarian", "Vegan", "Paleo", "Keto", "Balanced"])
    location = st.text_input("Enter your location for restaurant recommendations (optional)")

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

# Display Recipe Details
if recipe:
    st.subheader(f"🍽 Recommended Recipe: {recipe.get('title')}")
    
    # Display recipe image
    if recipe.get("image"):
        st.image(recipe["image"], width=400)

    # Display ingredients
    if "ingredients" in recipe:
        st.write("### Ingredients:")
        for ing in recipe["ingredients"]:
            st.write(f"- {ing}")

    # Display instructions
    if "instructions" in recipe:
        st.write("### Instructions:")
        for idx, step in enumerate(recipe["instructions"], start=1):
            st.write(f"{idx}. {step}")

else:
    st.write("Select a search method and click 'Find Recipe' to get started.")

