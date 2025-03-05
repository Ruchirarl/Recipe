import streamlit as st  # Importing Streamlit for building the web app
import requests  # Importing requests to make API calls
import os  # Importing os to manage environment variables (not needed here since Streamlit secrets are used)
from bs4 import BeautifulSoup  # Importing BeautifulSoup for web scraping
import random  # Importing random to select recipes randomly

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

# Keep Your Original 3 Options (No Change)
search_type = st.radio("## How would you like to find a recipe?", ["By Personality", "By Ingredient", "By Nutrients", "By Meal Type"])

recipe = None

# Your existing options (By Personality, By Ingredient, By Nutrients) remain untouched
if search_type == "By Personality":
    personality = st.selectbox("Select your personality trait", ["Openness", "Conscientiousness", "Extraversion", "Agreeableness"])
    diet = st.selectbox("Choose your diet preference", ["Vegetarian", "Vegan", "Keto", "Balanced", "Paleo", "Low-Carb", "Whole30"])
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

# 🔥 **New Option: "By Meal Type" Using AllRecipes**
@st.cache_data
def scrape_allrecipes(meal_type_url):
    """Scrapes a random recipe from AllRecipes for the selected meal type."""
    headers = {"User-Agent": "Mozilla/5.0"}
    
    # Fetch the meal category page
    response = requests.get(meal_type_url, headers=headers)
    if response.status_code != 200:
        st.error("Failed to fetch recipes from AllRecipes.")
        return None

    soup = BeautifulSoup(response.text, "lxml")

    # Find all valid recipe links
    all_recipe_links = soup.select("a[href*='/recipe/']")
    if not all_recipe_links:
        st.error("No recipes found. The website structure might have changed.")
        return None

    # Pick a random recipe
    recipe_url = random.choice(all_recipe_links)["href"]

    # Fetch the recipe page
    recipe_response = requests.get(recipe_url, headers=headers)
    if recipe_response.status_code != 200:
        st.error("Failed to fetch the selected recipe.")
        return None

    recipe_soup = BeautifulSoup(recipe_response.text, "lxml")

    # Extract recipe details
    title = recipe_soup.find("h1").text.strip() if recipe_soup.find("h1") else "Unknown Recipe"
    image_tag = recipe_soup.select_one("img.card__img")
    image_url = image_tag.get("data-src", image_tag.get("src", "")) if image_tag else ""

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

# 🎯 If the user selects "By Meal Type"
if search_type == "By Meal Type":
    st.markdown("### 🍽 Select a Meal Type to Get a Recipe from AllRecipes")

    meal_types = {
        "Breakfast": "https://www.allrecipes.com/recipes/78/breakfast-and-brunch/",
        "Lunch": "https://www.allrecipes.com/recipes/17561/lunch/",
        "Dinner": "https://www.allrecipes.com/recipes/17562/dinner/",
        "Snacks": "https://www.allrecipes.com/recipes/76/appetizers-and-snacks/"
    }

    selected_meal_type = st.selectbox("Choose a Meal Type", list(meal_types.keys()))

    if st.button("Get AllRecipes Recipe"):
        allrecipes_recipe = scrape_allrecipes(meal_types[selected_meal_type])

        if allrecipes_recipe:
            st.subheader(f"🍽 AllRecipes Recommended Recipe: {allrecipes_recipe.get('title')}")

            # Display image if available
            if allrecipes_recipe.get("image"):
                st.image(allrecipes_recipe["image"], width=400)

            # Display ingredients
            st.write("### 🛒 Ingredients:")
            for ing in allrecipes_recipe["ingredients"]:
                st.write(f"- {ing}")

            # Display instructions
            st.write("### 🍽 Instructions:")
            for idx, step in enumerate(allrecipes_recipe["instructions"], start=1):
                st.write(f"{idx}. {step}")
