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

def get_recipe_details(recipe):
    return {
        "title": recipe.get("title", "No title available"),
        "image": recipe.get("image", ""),
        "instructions": recipe.get("instructions", "No instructions available."),
        "ingredients": [ingredient["name"] for ingredient in recipe.get("extendedIngredients", [])],
        "calories": next((n["amount"] for n in recipe.get("nutrition", {}).get("nutrients", []) if n["name"] == "Calories"), "N/A"),
        "protein": next((n["amount"] for n in recipe.get("nutrition", {}).get("nutrients", []) if n["name"] == "Protein"), "N/A"),
        "fat": next((n["amount"] for n in recipe.get("nutrition", {}).get("nutrients", []) if n["name"] == "Fat"), "N/A"),
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
    
    if location:
        restaurants = get_restaurants(location, recipe.get("cuisine", ""))
        if restaurants:
            st.write("### 🍴 Nearby Restaurants:")
            for restaurant in restaurants:
                st.write(f"- **{restaurant['name']}** ({restaurant['rating']}⭐) - {restaurant['location'].get('address1', 'Address not available')}")
        else:
            st.write("❌ No nearby restaurants found.")
else:
    st.write("❌ No recipe found, try again later!")
