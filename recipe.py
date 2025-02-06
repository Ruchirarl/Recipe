import streamlit as st  # Importing Streamlit for building the web app
import requests  # Importing requests to make API calls
import os  # Importing os to manage environment variables (not needed here since Streamlit secrets are used)

# Setting Streamlit page title and favicon
st.set_page_config(page_title="🍽 BiteByType - Meals that fit your personality")

# Loading API keys securely from Streamlit secrets
SPOONACULAR_API_KEY = st.secrets["SPOONACULAR_API_KEY"]  # API key for fetching recipes
YELP_API_KEY = st.secrets["YELP_API_KEY"]  # API key for fetching restaurant recommendations

# Displaying the app title on the web page
st.title("🍽 BiteByType - Meals that fit your personality")

# Displaying markdown text on the page
st.markdown(
    """
    ## 🥗 Welcome to BiteByType!
    BiteByType is your personalized meal finder 🍜🍕🍣, helping you discover recipes tailored to your personality, dietary preferences, and nutritional needs! 🥦🍲
    
    🔍 How It Works:
    - Choose a recipe By Personality 🎭, By Ingredient 🥑, or By Nutrients 🏋‍♂.
    - Find recipes that match your taste and lifestyle! 🍳🥘
    - Explore restaurants nearby serving similar cuisines! 🍽🏙
    
    Let's find your next favorite meal! 🍽✨
    """
)

# Mapping personality traits to specific cuisines (Beyond Big Five Personality Traits)
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

# List of supported diet types for filtering recipes
diet_types = [
    "Gluten Free", "Ketogenic", "Vegetarian", "Lacto-Vegetarian", "Ovo-Vegetarian", "Vegan",
    "Pescetarian", "Paleo", "Primal", "Low FODMAP", "Whole30"
]

def get_recipe_by_personality(personality, diet):
    cuisine = PERSONALITY_TO_CUISINE.get(personality, ["Italian"])[0]
    url = "https://api.spoonacular.com/recipes/random"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "number": 1,
        "diet": diet,
        "cuisine": cuisine,
        "instructionsRequired": True,
        "addRecipeInformation": True
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data.get("recipes", [None])[0] if data else None

def get_recipe_by_ingredient(ingredient, max_time):
    url = "https://api.spoonacular.com/recipes/complexSearch"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "includeIngredients": ingredient,
        "maxReadyTime": max_time,
        "number": 1,
        "instructionsRequired": True,
        "addRecipeInformation": True
    }
    response = requests.get(url, params=params)
    data = response.json()
    return get_recipe_details_by_id(data["results"][0]["id"]) if data and "results" in data and data["results"] else None

def get_recipe_by_nutrients(nutrient, min_value, max_value, max_time):
    url = "https://api.spoonacular.com/recipes/findByNutrients"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        f"min{nutrient}": min_value,
        f"max{nutrient}": max_value,
        "maxReadyTime": max_time,
        "number": 1,
        "addRecipeInformation": True
    }
    response = requests.get(url, params=params)
    data = response.json()
    return get_recipe_details_by_id(data[0]["id"]) if data else None

# Create a radio button to choose the recipe search type
search_type = st.radio(
    "How would you like to find a recipe?", 
    ["By Personality", "By Ingredient", "By Nutrients"], 
    index=None
)

# Initialize recipe variable
recipe = None

# If a search type is selected, display corresponding input fields
if search_type:
    
    # Search by Personality
    if search_type == "By Personality":
        personality = st.selectbox("Select your dominant personality trait", list(PERSONALITY_TO_CUISINE.keys()), index=None)
        diet = st.selectbox("Choose your diet preference", diet_types, index=None)
    
    # Search by Ingredient
    elif search_type == "By Ingredient":
        ingredient = st.text_input("Enter an ingredient")
    
    # Search by Nutrients
    elif search_type == "By Nutrients":
        nutrient = st.selectbox("Choose a nutrient", ["Calories", "Protein", "Fat"])
        min_value = st.number_input(f"Min {nutrient}", min_value=0, value=50)
        max_value = st.number_input(f"Max {nutrient}", min_value=0, value=500)
    
    location = st.text_input("Enter your city/state for restaurant recommendations")

    if st.button("Find Recipe"):
        if search_type == "By Personality":
            recipe = get_recipe_by_personality(personality, diet)
        elif search_type == "By Ingredient":
            recipe = get_recipe_by_ingredient(ingredient, 120)
        elif search_type == "By Nutrients":
            recipe = get_recipe_by_nutrients(nutrient, min_value, max_value, 120)

if recipe:
    st.subheader(f"Recommended Recipe: {recipe.get('title', 'No title')}")
    st.image(recipe.get("image", ""), width=400)
    st.write(f"⏱ **Preparation Time:** {recipe.get('readyInMinutes', 'N/A')} minutes")
    st.write("### Ingredients:")
    st.write("\n".join(f"- {i['original']}" for i in recipe.get("extendedIngredients", [])))
    st.write("### Instructions:")
    st.write(recipe.get("instructions", "No instructions available."))
else:
    st.write("Welcome! Choose a search method above to find a recipe that suits you.")
