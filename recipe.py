import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup

# Load API Key for Spoonacular
SPOONACULAR_API_KEY = st.secrets["SPOONACULAR_API_KEY"]

# Wikipedia Table URL for Food Nutrients
WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/Table_of_food_nutrients"

# Function to Scrape Wikipedia for Nutrient Data
@st.cache_data
def scrape_wikipedia_nutrients():
    """Scrapes Wikipedia's Table of Food Nutrients and returns structured data."""
    response = requests.get(WIKIPEDIA_URL)
    soup = BeautifulSoup(response.text, "html.parser")

    tables = soup.find_all("table", {"class": "wikitable"})
    all_data = []

    for table in tables:
        df = pd.read_html(str(table))[0]  # Convert each table to Pandas DataFrame
        all_data.append(df)

    # Combine all tables into one DataFrame
    full_nutrient_data = pd.concat(all_data, ignore_index=True)
    full_nutrient_data.columns = ["Food", "Measure", "Weight (g)", "Calories", "Protein (g)", "Carbs (g)", "Fat (g)"]
    return full_nutrient_data

# Function to Find Matching Foods from Wikipedia Nutrient Table
def get_matching_foods(nutrient, min_value, max_value):
    """Finds foods from Wikipedia table that match the given nutrient range."""
    nutrient_data = scrape_wikipedia_nutrients()

    # Select relevant column based on nutrient choice
    nutrient_column = {
        "Calories": "Calories",
        "Protein": "Protein (g)",
        "Carbs": "Carbs (g)",
        "Fat": "Fat (g)"
    }[nutrient]

    # Filter foods within the nutrient range
    matching_foods = nutrient_data[
        (nutrient_data[nutrient_column] >= min_value) & 
        (nutrient_data[nutrient_column] <= max_value)
    ]

    return matching_foods["Food"].tolist()

# Function to Suggest Ingredient Swaps
def suggest_ingredient_swaps(recipe_ingredients, user_diet):
    """Suggests vegetarian/non-veg alternatives based on Wikipedia nutrient data."""
    nutrient_data = scrape_wikipedia_nutrients()
    
    # Define animal-based and plant-based food categories
    animal_foods = ["Chicken", "Beef", "Pork", "Fish", "Shrimp", "Lamb", "Turkey"]
    plant_foods = ["Tofu", "Lentils", "Chickpeas", "Mushrooms", "Seitan", "Beans", "Jackfruit"]

    swapped_ingredients = []
    for ingredient in recipe_ingredients:
        if user_diet == "Vegetarian" and ingredient in animal_foods:
            # Find a plant-based alternative with similar nutrients
            replacement = nutrient_data[nutrient_data["Protein (g)"] >= 5]["Food"].sample(1).values[0]
            swapped_ingredients.append(replacement)
        elif user_diet != "Vegetarian" and ingredient in plant_foods:
            # Find an animal-based alternative with similar nutrients
            replacement = nutrient_data[nutrient_data["Protein (g)"] >= 10]["Food"].sample(1).values[0]
            swapped_ingredients.append(replacement)
        else:
            swapped_ingredients.append(ingredient)
    
    return swapped_ingredients

# Function to Fetch Recipe Using Spoonacular API
def get_recipe_by_ingredients(ingredients_list):
    """Fetches a recipe using ingredients from Spoonacular API."""
    url = "https://api.spoonacular.com/recipes/complexSearch"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "includeIngredients": ",".join(ingredients_list[:5]),  # Limit to 5 key ingredients
        "number": 1,
        "instructionsRequired": True
    }

    data = requests.get(url, params=params).json()
    if data and "results" in data and data["results"]:
        return get_recipe_details_by_id(data["results"][0]["id"])
    return None

# Function to Fetch Recipe Details
def get_recipe_details_by_id(recipe_id):
    """Fetches full recipe details by ID from Spoonacular API."""
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    params = {"apiKey": SPOONACULAR_API_KEY, "includeNutrition": True}
    return requests.get(url, params=params).json()

# Streamlit UI
st.set_page_config(page_title="🍽 BiteByType - Nutrient-Powered Recipe Search")
st.title("🍽 Nutrient-Based Recipe Finder with Smart Swaps")

st.markdown("""
    ### 🔍 Search for a Recipe Based on Nutrients  
    - Enter a *nutrient range, and the system will find **matching foods* from Wikipedia.  
    - A *recipe will be suggested* based on those ingredients.  
    - If you have dietary restrictions, the system will *suggest ingredient swaps*!  
""")

# User Input for Nutrient-Based Search
nutrient = st.selectbox("Choose a nutrient", ["Calories", "Protein", "Carbs", "Fat"])
min_value = st.number_input(f"Min {nutrient} Value", min_value=0, value=100)
max_value = st.number_input(f"Max {nutrient} Value", min_value=0, value=200)

# User Dietary Preference (For Ingredient Swaps)
user_diet = st.selectbox("Do you follow a Vegetarian diet?", ["No", "Vegetarian"])

recipe = None  # Initialize recipe variable

if st.button("Find Recipe"):
    matching_foods = get_matching_foods(nutrient, min_value, max_value)

    if matching_foods:
        # Fetch initial recipe
        recipe = get_recipe_by_ingredients(matching_foods)

        if recipe:
            # Get the original ingredients
            original_ingredients = [i["name"] for i in recipe.get("extendedIngredients", [])]

            # Suggest ingredient swaps if needed
            modified_ingredients = suggest_ingredient_swaps(original_ingredients, user_diet)

            if original_ingredients != modified_ingredients:
                st.subheader("🔄 Suggested Ingredient Swaps")
                for orig, mod in zip(original_ingredients, modified_ingredients):
                    if orig != mod:
                        st.write(f"🔄 *{orig} → {mod}*")

                # Fetch new recipe with modified ingredients
                recipe = get_recipe_by_ingredients(modified_ingredients)
    else:
        st.error("❌ No matching foods found in Wikipedia's table.")

# If a recipe is found, display the details
if recipe:
    st.subheader(f"🍽 Recommended Recipe: {recipe.get('title', 'No title')}")
    st.image(recipe.get("image", ""), width=400)
    st.write(f"### Total Preparation Time: {recipe.get('readyInMinutes', 'N/A')} minutes")

    st.write("### Ingredients:")
    st.write("\n".join(f"- {i['original']}" for i in recipe.get("extendedIngredients", [])))

    st.write("### Instructions:")
    st.write(recipe.get("instructions", "No instructions available."))

else:
    st.write("Welcome! Choose a search method above to find a recipe that suits you.")
    