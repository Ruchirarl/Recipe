import streamlit as st
import requests
import os

# Set Streamlit page title
st.set_page_config(page_title="BiteByType - Meals that fit your personality")

# Load environment variables from Streamlit secrets
SPOONACULAR_API_KEY = st.secrets["SPOONACULAR_API_KEY"]

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
    data = response.json()
    return data.get("recipes", [None])[0] if response.status_code == 200 and "recipes" in data else None

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
    data = response.json()
    if response.status_code == 200 and "results" in data and data["results"]:
        return get_recipe_details_by_id(data["results"][0]["id"])
    return None

def get_recipe_by_nutrients(nutrient, min_value, max_value, max_time):
    url = "https://api.spoonacular.com/recipes/findByNutrients"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        f"min{nutrient}": min_value,
        f"max{nutrient}": max_value,
        "maxReadyTime": max_time,
        "number": 1
    }
    response = requests.get(url, params=params)
    data = response.json()
    if response.status_code == 200 and data:
        return get_recipe_details_by_id(data[0]["id"])
    return None

def get_recipe_details_by_id(recipe_id):
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    params = {"apiKey": SPOONACULAR_API_KEY, "includeNutrition": True}
    response = requests.get(url, params=params)
    return response.json() if response.status_code == 200 else None

def get_recipe_details(recipe):
    if not recipe or "extendedIngredients" not in recipe or "instructions" not in recipe:
        return None
    
    return {
        "title": recipe.get("title", "No title available"),
        "image": recipe.get("image", ""),
        "instructions": recipe.get("instructions", "No instructions available."),
        "ingredients": [ingredient["original"] for ingredient in recipe.get("extendedIngredients", [])],
        "calories": next((n["amount"] for n in recipe.get("nutrition", {}).get("nutrients", []) if n["name"] == "Calories"), "N/A"),
        "protein": next((n["amount"] for n in recipe.get("nutrition", {}).get("nutrients", []) if n["name"] == "Protein"), "N/A"),
        "fat": next((n["amount"] for n in recipe.get("nutrition", {}).get("nutrients", []) if n["name"] == "Fat"), "N/A"),
    }

# Streamlit App
st.title("🍽️ BiteByType - Meals that fit your personality")

search_type = st.radio("How would you like to find a recipe?", ["By Personality", "By Ingredient", "By Nutrients"])

recipe = None

if search_type == "By Personality":
    personality = st.selectbox("Select your dominant personality trait", list(PERSONALITY_TO_CUISINE.keys()))
    diet = st.selectbox("Choose your diet preference", diet_types)
    if st.button("Find Recipe"):
        recipe = get_recipe_by_personality(personality, diet)

elif search_type == "By Ingredient":
    ingredient = st.text_input("Enter an ingredient")
    max_time = st.number_input("Enter max preparation time in minutes", min_value=5, max_value=120, value=30)
    if st.button("Find Recipe"):
        recipe = get_recipe_by_ingredient(ingredient, max_time)

elif search_type == "By Nutrients":
    nutrient = st.selectbox("Choose a nutrient", ["Calories", "Protein", "Fat"])
    min_value = st.number_input(f"Enter minimum {nutrient}", min_value=0, max_value=5000, value=50)
    max_value = st.number_input(f"Enter maximum {nutrient}", min_value=0, max_value=5000, value=500)
    max_time = st.number_input("Enter max preparation time in minutes", min_value=5, max_value=120, value=30)
    if st.button("Find Recipe"):
        recipe = get_recipe_by_nutrients(nutrient, min_value, max_value, max_time)

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
