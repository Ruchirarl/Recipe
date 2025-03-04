import streamlit as st  # Importing Streamlit for building the web app
import requests  # Importing requests to make API calls
import os  # Importing os to manage environment variables
import pandas as pd  # Importing pandas for data manipulation
from bs4 import BeautifulSoup  # Importing BeautifulSoup for scraping Wikipedia

# Setting Streamlit page title and favicon
st.set_page_config(page_title="🍽 BiteByType - Meals that fit your personality")

# Loading API keys securely from Streamlit secrets
SPOONACULAR_API_KEY = st.secrets["SPOONACULAR_API_KEY"]
YELP_API_KEY = st.secrets["YELP_API_KEY"]

# Displaying the app title on the web page
st.title("🍽 BiteByType - Meals that fit your personality")

# Wikipedia URL for nutrient data
WIKIPEDIA_URL = "https://en.wikipedia.org/wiki/Table_of_food_nutrients"

# Function to scrape Wikipedia for nutrient information
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

    full_nutrient_data = pd.concat(all_data, ignore_index=True)
    full_nutrient_data.columns = ["Food", "Measure", "Weight (g)", "Calories", "Protein (g)", "Carbs (g)", "Fat (g)"]
    return full_nutrient_data

# Function to suggest ingredient replacements based on nutrient similarity
def suggest_replacement(main_ingredient, is_veg=True):
    """Suggests a replacement ingredient based on nutrient similarity."""
    nutrient_data = scrape_wikipedia_nutrients()
    ingredient_data = nutrient_data[nutrient_data["Food"].str.contains(main_ingredient, case=False, na=False)]

    if ingredient_data.empty:
        return f"No data found for {main_ingredient}."

    # Extract nutrient values
    target_nutrients = ingredient_data[["Protein (g)", "Carbs (g)", "Fat (g)"]].values[0]

    # Define replacement category
    category_filter = ["Meat", "Seafood", "Poultry"] if is_veg else ["Vegetables", "Legumes", "Plant-Based Proteins"]

    # Find the best match based on nutrient similarity
    nutrient_data["Similarity"] = nutrient_data.apply(
        lambda row: sum(abs(row[["Protein (g)", "Carbs (g)", "Fat (g)"]] - target_nutrients)),
        axis=1
    )

    alternative = nutrient_data.sort_values("Similarity").head(3)
    return alternative[["Food", "Protein (g)", "Carbs (g)", "Fat (g)"]].to_dict(orient="records")

# Recipe search functionality remains unchanged
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

def get_recipe_by_nutrients(nutrient, min_value, max_value, max_time):
    """Fetch a recipe based on nutritional content."""
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
    """Fetch detailed recipe information by ID."""
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    params = {"apiKey": SPOONACULAR_API_KEY, "includeNutrition": True}
    return fetch_api(url, params)

# Streamlit UI: User selects recipe by Nutrients
search_type = st.radio(
    "## How would you like to find a recipe?", 
    ["By Personality", "By Ingredient", "By Nutrients"], 
    index=None
)

recipe = None

if search_type:
    if search_type == "By Nutrients":
        nutrient = st.selectbox("Choose a nutrient", ["Calories", "Protein", "Fat"])
        min_value = st.number_input(f"Min {nutrient} (10)", min_value=10, value=100)
        max_value = st.number_input(f"Max {nutrient} (100)", min_value=10, value=100)
        max_time = st.slider("Max preparation time (minutes)", 5, 120, 30)

    if st.button("Find Recipe"):
        recipe = get_recipe_by_nutrients(nutrient, min_value, max_value, max_time)

if recipe:
    st.subheader(f"Recommended Recipe: {recipe.get('title', 'No title')}")
    st.image(recipe.get("image", ""), width=400)
    st.write(f"### Total Preparation Time: {recipe.get('readyInMinutes', 'N/A')} minutes")
    
    # Display ingredients list
    st.write("### Ingredients:")
    ingredients = [i['original'] for i in recipe.get("extendedIngredients", [])]
    st.write("\n".join(f"- {ingredient}" for ingredient in ingredients))

    # Ingredient Substitution Suggestion
    if ingredients:
        main_ingredient = ingredients[0]  # Assume first ingredient is the main one
        is_veg = True if "Vegetarian" in recipe.get("diets", []) else False
        suggestions = suggest_replacement(main_ingredient, is_veg)

        st.write("### Suggested Ingredient Substitutes:")
        for item in suggestions:
            st.write(f"- {item['Food']} (Protein: {item['Protein (g)']}g, Carbs: {item['Carbs (g)']}g, Fat: {item['Fat (g)']}g)")

    # Display cooking instructions
    st.write("### Instructions:")
    st.write(recipe.get("instructions", "No instructions available."))

else:
    st.write("Welcome! Choose a search method above to find a recipe that suits you.")