import streamlit as st
import requests
import os

# Set Streamlit page title
st.set_page_config(page_title="BiteByType - Meals that fit your personality")

# Load environment variables from Streamlit secrets
SPOONACULAR_API_KEY = st.secrets["SPOONACULAR_API_KEY"]
YELP_API_KEY = st.secrets["YELP_API_KEY"]

# Mapping personality traits to cuisines
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

# Supported diet types
diet_types = [
    "Gluten Free", "Ketogenic", "Vegetarian", "Lacto-Vegetarian", "Ovo-Vegetarian", "Vegan", 
    "Pescetarian", "Paleo", "Primal", "Low FODMAP", "Whole30"
]

def get_recipe_by_personality(personality_trait, max_calories, quick_meal, diet):
    cuisine = PERSONALITY_TO_CUISINE.get(personality_trait, ["Italian"])[0]
    max_ready_time = 30 if quick_meal else 60
    url = f"https://api.spoonacular.com/recipes/random?apiKey={SPOONACULAR_API_KEY}&number=1&maxCalories={max_calories}&maxReadyTime={max_ready_time}&addRecipeNutrition=true&diet={diet}&cuisine={cuisine}"
    response = requests.get(url)
    return response.json().get("recipes", [None])[0] if response.status_code == 200 else None

def get_recipe_by_ingredient(ingredient, meal_type, max_time):
    url = "https://api.spoonacular.com/recipes/complexSearch"
    params = {
        "includeIngredients": ingredient,
        "type": meal_type,
        "maxReadyTime": max_time,
        "number": 1,
        "addRecipeNutrition": True,
        "apiKey": SPOONACULAR_API_KEY
    }
    response = requests.get(url, params=params)
    return response.json().get("results", [None])[0] if response.status_code == 200 else None

def get_recipe_by_nutrients(nutrient, min_value, max_value):
    url = "https://api.spoonacular.com/recipes/findByNutrients"
    params = {
        f"min{nutrient}": min_value,
        f"max{nutrient}": max_value,
        "number": 1,
        "apiKey": SPOONACULAR_API_KEY
    }
    response = requests.get(url, params=params)
    return response.json()[0] if response.status_code == 200 else None

# Streamlit App
st.title("🍽️ BiteByType - Meals that fit your personality")

search_type = st.radio("How would you like to find a recipe?", ["By Personality", "By Ingredient", "By Nutrients"])

if search_type == "By Personality":
    personality = st.selectbox("Select your dominant personality trait", list(PERSONALITY_TO_CUISINE.keys()))
    calorie_intake = st.number_input("Enter your desired calorie intake per meal", min_value=100, max_value=2000, value=500)
    quick_meal = st.checkbox("Quick Meal (Under 30 minutes)")
    diet = st.selectbox("Choose your diet preference", diet_types)
    if st.button("Find Recipe"):
        recipe = get_recipe_by_personality(personality, calorie_intake, quick_meal, diet)
        if recipe:
            st.subheader(f"🍽️ Recommended Recipe: {recipe['title']}")
            st.image(recipe['image'], width=400)
            st.write("### Ingredients:")
            st.write("\n".join([f"- {ingredient['name']}" for ingredient in recipe.get("extendedIngredients", [])]))
            st.write("### Instructions:")
            st.write(recipe["instructions"])
        else:
            st.write("❌ No recipe found, try again later!")

elif search_type == "By Ingredient":
    ingredient = st.text_input("Enter an ingredient")
    meal_type = st.selectbox("Choose a meal type", ["main course", "dessert", "appetizer", "breakfast"])
    max_time = st.number_input("Enter max preparation time in minutes", min_value=5, max_value=120, value=30)
    if st.button("Find Recipe"):
        recipe = get_recipe_by_ingredient(ingredient, meal_type, max_time)
        if recipe:
            st.subheader(f"🍽️ Recommended Recipe: {recipe['title']}")
            st.image(recipe.get('image', ''), width=400)
        else:
            st.write("❌ No recipe found, try again later!")

elif search_type == "By Nutrients":
    nutrient = st.selectbox("Choose a nutrient", ["Calories", "Protein", "Carbs", "Fat"])
    min_value = st.number_input(f"Enter minimum {nutrient}", min_value=0, max_value=1000, value=50)
    max_value = st.number_input(f"Enter maximum {nutrient}", min_value=0, max_value=5000, value=500)
    if st.button("Find Recipe"):
        recipe = get_recipe_by_nutrients(nutrient, min_value, max_value)
        if recipe:
            st.subheader(f"🍽️ Recommended Recipe: {recipe['title']}")
            st.image(recipe.get('image', ''), width=400)
        else:
            st.write("❌ No recipe found, try again later!")
