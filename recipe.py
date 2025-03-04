import streamlit as st
import requests
from bs4 import BeautifulSoup

# Set page config
st.set_page_config(page_title="🍽 BiteByType - Personalized Meal Finder")

# Spoonacular API Key (stored securely in Streamlit secrets)
SPOONACULAR_API_KEY = st.secrets["SPOONACULAR_API_KEY"]

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

### AllRecipes Scraper ###
@st.cache_data
def scrape_allrecipes(meal_type_url):
    """Scrapes a full recipe from AllRecipes for the selected meal type."""
    headers = {"User-Agent": "Mozilla/5.0"}
    
    # Step 1: Get the meal category page (Breakfast, Lunch, etc.)
    response = requests.get(meal_type_url, headers=headers)
    if response.status_code != 200:
        st.error("Failed to fetch the meal type page.")
        return None

    soup = BeautifulSoup(response.text, "lxml")

    # Step 2: Find the first recipe card
    first_recipe = soup.select_one("div.card__content")
    if not first_recipe:
        st.error("No recipe card found. Check the HTML structure.")
        return None

    # Extract title
    title_tag = first_recipe.select_one(".card__title-text")
    title = title_tag.text.strip() if title_tag else "Unknown Recipe"

    # Extract image (Handling data-src and src fallback)
    image_tag = first_recipe.select_one("img.mntl-image")
    if image_tag:
        image_url = image_tag.get("data-src", image_tag.get("src", ""))
    else:
        image_url = ""  # If no image found, use an empty string

    # Extract recipe URL
    recipe_link = first_recipe.find_parent("a")
    recipe_url = recipe_link["href"] if recipe_link else None

    if not recipe_url:
        st.error("No recipe link found.")
        return None

    # Step 3: Fetch the detailed recipe page
    recipe_response = requests.get(recipe_url, headers=headers)
    if recipe_response.status_code != 200:
        st.error("Failed to fetch the recipe page.")
        return None

    recipe_soup = BeautifulSoup(recipe_response.text, "lxml")

    # Extract ingredients
    ingredients = [ing.get_text(strip=True) for ing in recipe_soup.select(".mm-recipes-structured-ingredients__list-item")]

    # Extract instructions
    instructions = [step.get_text(strip=True) for step in recipe_soup.select(".mntl-sc-block-html")]

    return {
        "title": title,
        "image": image_url,
        "ingredients": ingredients,
        "instructions": instructions
    }

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
    
    if st.button("Find Recipe"):
        recipe = get_recipe_by_personality(personality, diet)

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
    if recipe.get("ingredients"):
        st.write("### Ingredients:")
        for ing in recipe["ingredients"]:
            st.write(f"- {ing}")

    # Display instructions
    if recipe.get("instructions"):
        st.write("### Instructions:")
        for idx, step in enumerate(recipe["instructions"], start=1):
            st.write(f"{idx}. {step}")

else:
    st.write("Select a search method and click 'Find Recipe' to get started.")
