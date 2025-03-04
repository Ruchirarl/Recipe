import streamlit as st  # Importing Streamlit for building the web app
import requests  # Importing requests to make API calls
from bs4 import BeautifulSoup  # Importing BeautifulSoup for web scraping
import random  # Importing random to select recipes randomly

# Setting Streamlit page title
st.set_page_config(page_title="🍽 BiteByType - Meals that fit your personality")

# Loading API keys securely from Streamlit secrets
SPOONACULAR_API_KEY = st.secrets["SPOONACULAR_API_KEY"]  # API key for fetching recipes

# Displaying the app title
st.title("🍽 BiteByType - Meals that fit your personality")

st.markdown("""
## 🥗 Welcome to BiteByType!
BiteByType helps you discover recipes tailored to your **personality, ingredients, nutrition, or meal type**! 🍲✨
- **Choose a recipe**: By Personality 🎭, By Ingredient 🥑, By Nutrients 🏋‍♂, or By Meal Type 🍽.
- **Get personalized recipes** from **Spoonacular** or **AllRecipes**.
""")

# Meal type URLs for AllRecipes scraping
MEAL_TYPES = {
    "Breakfast": "https://www.allrecipes.com/recipes/78/breakfast-and-brunch/",
    "Lunch": "https://www.allrecipes.com/recipes/17561/lunch/",
    "Dinner": "https://www.allrecipes.com/recipes/17562/dinner/",
    "Snacks": "https://www.allrecipes.com/recipes/76/appetizers-and-snacks/"
}

diet_types = ["Vegetarian", "Vegan", "Keto", "Balanced", "Paleo", "Low-Carb", "Whole30"]

@st.cache_data  # Cache API responses
def fetch_api(url, params):
    """Fetches data from an API and returns JSON response."""
    try:
        response = requests.get(url, params=params)
        return response.json() if response.status_code == 200 else None
    except requests.RequestException:
        return None

def get_recipe_by_personality(personality, diet):
    """Fetch a recipe based on personality and diet preferences."""
    url = "https://api.spoonacular.com/recipes/random"
    params = {"apiKey": SPOONACULAR_API_KEY, "number": 1, "diet": diet, "instructionsRequired": True}
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

def scrape_allrecipes(meal_type_url):
    """Scrapes a random recipe from AllRecipes for the selected meal type."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(meal_type_url, headers=headers)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "lxml")
    all_recipe_links = soup.select("a[href*='/recipe/']")
    if not all_recipe_links:
        return None

    recipe_url = random.choice(all_recipe_links)["href"]
    recipe_response = requests.get(recipe_url, headers=headers)
    if recipe_response.status_code != 200:
        return None

    recipe_soup = BeautifulSoup(recipe_response.text, "lxml")
    title = recipe_soup.find("h1").text.strip() if recipe_soup.find("h1") else "Unknown Recipe"
    image_tag = recipe_soup.select_one("img.card__img")
    image_url = image_tag.get("data-src", image_tag.get("src", "")) if image_tag else ""
    ingredients = [ing.get_text(strip=True) for ing in recipe_soup.select(".mm-recipes-structured-ingredients__list-item")]
    instructions = [step.get_text(strip=True) for step in recipe_soup.select(".mntl-sc-block-html")]

    return {"title": title, "image": image_url, "ingredients": ingredients, "instructions": instructions}

# Streamlit UI: Choose search method
search_type = st.radio("## How would you like to find a recipe?", ["By Personality", "By Ingredient", "By Nutrients", "By Meal Type"])

recipe = None

if search_type == "By Personality":
    personality = st.selectbox("Select your dominant personality trait", ["Openness", "Conscientiousness", "Extraversion", "Agreeableness"])
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
    min_value = st.number_input(f"Min {nutrient} (10)", min_value=10, value=100)
    max_value = st.number_input(f"Max {nutrient} (100)", min_value=10, value=500)
    max_time = st.slider("Max preparation time (minutes)", 5, 120, 30)
    if st.button("Find Recipe"):
        recipe = get_recipe_by_nutrients(nutrient, min_value, max_value, max_time)

elif search_type == "By Meal Type":
    meal_type = st.selectbox("Choose a Meal Type", list(MEAL_TYPES.keys()))
    if st.button("Find Recipe"):
        recipe = scrape_allrecipes(MEAL_TYPES[meal_type])

# Display Recipe Details
if recipe:
    st.subheader(f"🍽 Recommended Recipe: {recipe.get('title')}")
    
    if recipe.get("image"):
        st.image(recipe["image"], width=400)

    if recipe.get("ingredients"):
        st.write("### 🛒 Ingredients:")
        for ing in recipe["ingredients"]:
            st.write(f"- {ing}")

    if recipe.get("instructions"):
        st.write("### 🍽 Instructions:")
        for idx, step in enumerate(recipe["instructions"], start=1):
            st.write(f"{idx}. {step}")

else:
    st.write("Select a search method and click 'Find Recipe' to get started.")
