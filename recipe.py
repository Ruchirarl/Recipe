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

def get_recipe_by_personality(personality, max_calories, quick_meal, diet):
    cuisine = PERSONALITY_TO_CUISINE.get(personality, ["Italian"])[0]
    max_ready_time = 30 if quick_meal else 60
    url = "https://api.spoonacular.com/recipes/random"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "number": 1,
        "maxCalories": max_calories,
        "maxReadyTime": max_ready_time,
        "addRecipeNutrition": True,
        "diet": diet,
        "cuisine": cuisine
    }
    response = requests.get(url, params=params)
    return response.json().get("recipes", [None])[0] if response.status_code == 200 else None

def get_recipe_by_ingredient(ingredient):
    url = "https://api.spoonacular.com/recipes/complexSearch"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "includeIngredients": ingredient,
        "number": 1,
        "addRecipeNutrition": True
    }
    response = requests.get(url, params=params)
    return response.json().get("results", [None])[0] if response.status_code == 200 else None

def get_recipe_by_nutrients(nutrient, min_value, max_value):
    url = "https://api.spoonacular.com/recipes/findByNutrients"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        f"min{nutrient}": min_value,
        f"max{nutrient}": max_value,
        "number": 1
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

def get_restaurants(location, cuisine):
    url = "https://api.yelp.com/v3/businesses/search"
    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    params = {"term": cuisine, "location": location, "limit": 5}
    response = requests.get(url, headers=headers, params=params)
    return response.json().get("businesses", []) if response.status_code == 200 else []

# Streamlit App
st.title("🍽️ BiteByType - Meals that fit your personality")

search_type = st.radio("How would you like to find a recipe?", ["By Personality", "By Ingredient", "By Nutrients"])

recipe = None  # Initialize recipe variable

if search_type == "By Personality":
    personality = st.selectbox("Select your dominant personality trait", list(PERSONALITY_TO_CUISINE.keys()))
    calorie_intake = st.number_input("Enter your desired calorie intake per meal", min_value=100, max_value=2000, value=500)
    quick_meal = st.checkbox("Quick Meal (Under 30 minutes)")
    diet = st.selectbox("Choose your diet preference", diet_types)
    location = st.text_input("Enter your city for restaurant recommendations")
    if st.button("Find Recipe"):
        recipe = get_recipe_by_personality(personality, calorie_intake, quick_meal, diet)

elif search_type == "By Ingredient":
    ingredient = st.text_input("Enter an ingredient")
    if st.button("Find Recipe"):
        recipe = get_recipe_by_ingredient(ingredient)

elif search_type == "By Nutrients":
    nutrient = st.selectbox("Choose a nutrient", ["Calories", "Protein", "Carbs", "Fat"])
    min_value = st.number_input(f"Enter minimum {nutrient}", min_value=0, max_value=1000, value=50)
    max_value = st.number_input(f"Enter maximum {nutrient}", min_value=0, max_value=5000, value=500)
    if st.button("Find Recipe"):
        recipe = get_recipe_by_nutrients(nutrient, min_value, max_value)

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
