import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup

# Setting Streamlit page title
st.set_page_config(page_title="🍽 BiteByType - Meals that fit your personality")

# Load API Keys
SPOONACULAR_API_KEY = st.secrets["SPOONACULAR_API_KEY"]
YELP_API_KEY = st.secrets["YELP_API_KEY"]

# Wikipedia URL for the nutrient table
WIKI_URL = "https://en.wikipedia.org/wiki/Table_of_food_nutrients"

# Function to scrape Wikipedia nutrient data
@st.cache_data
def scrape_wikipedia_nutrients():
    """Scrapes the food nutrient table from Wikipedia and returns it as a DataFrame."""
    response = requests.get(WIKI_URL)
    soup = BeautifulSoup(response.text, "html.parser")
    
    tables = soup.find_all("table", {"class": "wikitable"})
    if not tables:
        return None
    
    df = pd.read_html(str(tables[0]))[0]
    df.columns = ["Food", "Calories (kcal)", "Protein (g)", "Fat (g)", "Carbs (g)"]
    df = df.iloc[1:].reset_index(drop=True)
    
    return df

# Load Wikipedia nutrient data
nutrient_data = scrape_wikipedia_nutrients()

# Function to get food nutrition details
def get_nutrient_info(food_name):
    """Fetches nutrient details (Calories, Protein, Fat, Carbs) for a given food item."""
    if nutrient_data is None:
        return None
    
    matched_row = nutrient_data[nutrient_data["Food"].str.contains(food_name, case=False, na=False)]
    
    if matched_row.empty:
        return None
    
    return matched_row.iloc[0]

# Function to fetch API data
@st.cache_data
def fetch_api(url, params):
    """Fetches data from an API and returns JSON response."""
    try:
        response = requests.get(url, params=params)
        return response.json() if response.status_code == 200 else None
    except requests.RequestException:
        return None

# Function to fetch a recipe by personality
def get_recipe_by_personality(personality, diet):
    cuisine = {"Openness": "Japanese", "Conscientiousness": "Mediterranean", "Extraversion": "Mexican",
               "Agreeableness": "Vegetarian", "Neuroticism": "Comfort Food", "Adventurous": "Thai",
               "Analytical": "Greek", "Creative": "Fusion", "Traditional": "American"}[personality]
    
    url = "https://api.spoonacular.com/recipes/random"
    params = {"apiKey": SPOONACULAR_API_KEY, "number": 1, "diet": diet, "cuisine": cuisine, "instructionsRequired": True}
    
    data = fetch_api(url, params)
    return data.get("recipes", [None])[0] if data else None

# Function to fetch a recipe by ingredient
def get_recipe_by_ingredient(ingredient, max_time):
    url = "https://api.spoonacular.com/recipes/complexSearch"
    params = {"apiKey": SPOONACULAR_API_KEY, "includeIngredients": ingredient, "maxReadyTime": max_time, "number": 1, "instructionsRequired": True}
    
    data = fetch_api(url, params)
    return get_recipe_details_by_id(data["results"][0]["id"]) if data and data.get("results") else None

# Function to fetch a recipe by nutrients
def get_recipe_by_nutrients(nutrient, min_value, max_value):
    url = "https://api.spoonacular.com/recipes/findByNutrients"
    params = {"apiKey": SPOONACULAR_API_KEY, f"min{nutrient}": min_value, f"max{nutrient}": max_value, "number": 1}
    
    data = fetch_api(url, params)
    return get_recipe_details_by_id(data[0]["id"]) if data else None

# Function to fetch detailed recipe info
def get_recipe_details_by_id(recipe_id):
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    params = {"apiKey": SPOONACULAR_API_KEY, "includeNutrition": True}
    
    return fetch_api(url, params)

# Function to fetch nearby restaurants from Yelp
@st.cache_data
def get_restaurants(location, cuisine):
    url = "https://api.yelp.com/v3/businesses/search"
    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    params = {"term": cuisine, "location": location, "limit": 5}
    
    try:
        response = requests.get(url, headers=headers, params=params)
        return response.json().get("businesses", []) if response.status_code == 200 else []
    except requests.RequestException:
        return []

# --- Streamlit UI ---
st.markdown("""
## 🥗 Welcome to BiteByType!
Discover recipes tailored to your personality, dietary preferences, and nutrition needs! 🥦🍲
""")

# User selects feature
feature = st.radio("Select a feature:", 
                   ["Find a Recipe", "Compare Two Foods Nutritionally"], 
                   index=None)

if feature == "Find a Recipe":
    search_type = st.radio("How would you like to find a recipe?", 
                           ["By Personality", "By Ingredient", "By Nutrients"], index=None)
    
    if search_type == "By Personality":
        personality = st.selectbox("Select your dominant personality trait",
                                   ["Openness", "Conscientiousness", "Extraversion", "Agreeableness",
                                    "Neuroticism", "Adventurous", "Analytical", "Creative", "Traditional"])
        diet = st.selectbox("Choose your diet preference",
                            ["Gluten Free", "Ketogenic", "Vegetarian", "Vegan", "Pescetarian", "Paleo"])
        recipe = get_recipe_by_personality(personality, diet)

    elif search_type == "By Ingredient":
        ingredient = st.text_input("Enter an ingredient")
        max_time = st.slider("Max preparation time (minutes)", 5, 120, 30)
        recipe = get_recipe_by_ingredient(ingredient, max_time)

    elif search_type == "By Nutrients":
        nutrient = st.selectbox("Choose a nutrient", ["Calories", "Protein", "Fat"])
        min_value = st.number_input(f"Min {nutrient}", min_value=0, value=100)
        max_value = st.number_input(f"Max {nutrient}", min_value=0, value=200)
        recipe = get_recipe_by_nutrients(nutrient, min_value, max_value)

    if recipe:
        st.subheader(f"🍽 Recommended Recipe: {recipe.get('title', 'No title')}")
        st.image(recipe.get("image", ""), width=400)
        st.write(f"⏳ Preparation Time: {recipe.get('readyInMinutes', 'N/A')} minutes")
        st.write("📜 Ingredients:")
        st.write("\n".join(f"- {i['original']}" for i in recipe.get("extendedIngredients", [])))
        st.write("📝 Instructions:")
        st.write(recipe.get("instructions", "No instructions available."))

elif feature == "Compare Two Foods Nutritionally":
    st.header("🥑 Compare Two Foods Nutritionally")
    food1 = st.text_input("Enter First Food Item (e.g., Chicken, Tofu)")
    food2 = st.text_input("Enter Second Food Item (e.g., Salmon, Lentils)")
    
    if st.button("Compare Foods"):
        food1_data, food2_data = get_nutrient_info(food1), get_nutrient_info(food2)
        
        if food1_data is not None and food2_data is not None:
            st.table(pd.DataFrame({food1: food1_data[1:], food2: food2_data[1:]}, index=["Calories", "Protein", "Fat", "Carbs"]))
        else:
            st.error("One or both food items could not be found in Wikipedia’s nutrient table.")

st.write("Welcome! Choose a feature above to get started.")