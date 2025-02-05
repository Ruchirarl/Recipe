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

def get_recipe_by_personality(personality, diet):
    cuisine = PERSONALITY_TO_CUISINE.get(personality, ["Italian"])[0]
    url = "https://api.spoonacular.com/recipes/random"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "number": 1,
        "addRecipeNutrition": True,
        "diet": diet,
        "cuisine": cuisine
    }
    response = requests.get(url, params=params)
    return response.json().get("recipes", [None])[0] if response.status_code == 200 else None

def get_recipe_by_ingredient(ingredient, max_time):
    url = "https://api.spoonacular.com/recipes/complexSearch"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "includeIngredients": ingredient,
        "maxReadyTime": max_time,
        "number": 1,
        "addRecipeNutrition": True
    }
    response = requests.get(url, params=params)
    return response.json().get("results", [None])[0] if response.status_code == 200 else None

def get_recipe_by_nutrients(calories, protein, fat, min_value, max_value, max_time, diet):
    url = "https://api.spoonacular.com/recipes/findByNutrients"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "minCalories": min_value,
        "maxCalories": max_value,
        "minProtein": protein,
        "minFat": fat,
        "maxReadyTime": max_time,
        "number": 1,
        "diet": diet
    }
    response = requests.get(url, params=params)
    return response.json()[0] if response.status_code == 200 and response.json() else None

def get_recipe_details(recipe):
    nutrition = recipe.get("nutrition", {}).get("nutrients", [])
    if not nutrition:
        return None  # Skip recipes without nutrition info
    
    return {
        "title": recipe.get("title", "No title available"),
        "image": recipe.get("image", ""),
        "instructions": recipe.get("instructions", "No instructions available."),
        "ingredients": [ingredient["name"] for ingredient in recipe.get("extendedIngredients", [])],
        "calories": next((n["amount"] for n in nutrition if n["name"] == "Calories"), "N/A"),
        "protein": next((n["amount"] for n in nutrition if n["name"] == "Protein"), "N/A"),
        "fat": next((n["amount"] for n in nutrition if n["name"] == "Fat"), "N/A"),
    }

# Streamlit App
st.title("🍽️ BiteByType - Meals that fit your personality")

search_type = st.radio("How would you like to find a recipe?", ["By Personality", "By Ingredient", "By Nutrients"])

recipe = None  # Initialize recipe variable

if search_type == "By Personality":
    personality = st.selectbox("Select your dominant personality trait", list(PERSONALITY_TO_CUISINE.keys()))
    diet = st.selectbox("Choose your diet preference", diet_types)
    location = st.text_input("Enter your city for restaurant recommendations")
    if st.button("Find Recipe"):
        recipe = get_recipe_by_personality(personality, diet)

elif search_type == "By Ingredient":
    ingredient = st.text_input("Enter an ingredient")
    max_time = st.number_input("Enter max preparation time in minutes", min_value=5, max_value=120, value=30)
    if st.button("Find Recipe"):
        recipe = get_recipe_by_ingredient(ingredient, max_time)

elif search_type == "By Nutrients":
    calories = st.number_input("Enter calorie intake", min_value=0, max_value=5000, value=500)
    protein = st.number_input("Enter protein intake", min_value=0, max_value=500, value=50)
    fat = st.number_input("Enter fat intake", min_value=0, max_value=500, value=50)
    min_value = st.number_input("Enter minimum calorie range", min_value=0, max_value=5000, value=50)
    max_value = st.number_input("Enter maximum calorie range", min_value=0, max_value=5000, value=500)
    max_time = st.number_input("Enter max preparation time in minutes", min_value=5, max_value=120, value=30)
    diet = st.selectbox("Choose your diet preference", diet_types)
    if st.button("Find Recipe"):
        recipe = get_recipe_by_nutrients(calories, protein, fat, min_value, max_value, max_time, diet)

if recipe:
    details = get_recipe_details(recipe)
    if details:
        st.subheader(f"🍽️ Recommended Recipe: {details['title']}")
        st.image(details['image'], width=400)
        st.write("### Ingredients:")
        st.write("\n".join([f"- {ingredient}" for ingredient in details["ingredients"]]))
        st.write("### Instructions:")
        st.write(details["instructions"])
        st.write("### 🔬 Nutrition Facts:")
        st.write(f"- **Calories:** {details['calories']} kcal")
        st.write(f"- **Protein:** {details['protein']} g")
        st.write(f"- **Fat:** {details['fat']} g")
else:
    st.write("❌ No recipe found, try again later!")
