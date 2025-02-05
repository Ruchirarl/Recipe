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

def get_recipe_by_nutrients(nutrient, min_value, max_value, max_time):
    url = "https://api.spoonacular.com/recipes/findByNutrients"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        f"min{nutrient}": min_value,
        f"max{nutrient}": max_value,
        "maxReadyTime": max_time,
        "number": 1,
        "addRecipeNutrition": True
    }
    response = requests.get(url, params=params)
    data = response.json()
    return data[0] if response.status_code == 200 and data else None

def get_restaurants(location, cuisine):
    url = "https://api.yelp.com/v3/businesses/search"
    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    params = {"term": cuisine, "location": location, "limit": 5}
    response = requests.get(url, headers=headers, params=params)
    return response.json().get("businesses", []) if response.status_code == 200 else []

def get_recipe_details(recipe):
    if not recipe or "extendedIngredients" not in recipe or "instructions" not in recipe:
        return None
    
    return {
        "title": recipe.get("title", "No title available"),
        "image": recipe.get("image", ""),
        "instructions": recipe.get("instructions", "No instructions available."),
        "ingredients": [ingredient["original"] for ingredient in recipe.get("extendedIngredients", [])],
        "nutrition": recipe.get("nutrition", {}).get("nutrients", [])
    }

# Streamlit App
st.title("🍽️ BiteByType - Meals that fit your personality")

search_type = st.radio("How would you like to find a recipe?", ["By Personality", "By Ingredient", "By Nutrients"], index=None)

recipe = None

if search_type:
    if search_type == "By Personality":
        personality = st.selectbox("Select your dominant personality trait", list(PERSONALITY_TO_CUISINE.keys()), index=None)
        diet = st.selectbox("Choose your diet preference", diet_types, index=None)
    elif search_type == "By Ingredient":
        ingredient = st.text_input("Enter an ingredient", "")
        max_time = st.number_input("Enter max preparation time in minutes", min_value=5, max_value=120, value=30)
    elif search_type == "By Nutrients":
        nutrient = st.selectbox("Choose a nutrient", ["Calories", "Protein", "Fat"], index=None)
        min_value = st.number_input(f"Enter minimum {nutrient}", min_value=0, max_value=5000, value=50)
        max_value = st.number_input(f"Enter maximum {nutrient}", min_value=0, max_value=5000, value=500)
        max_time = st.number_input("Enter max preparation time in minutes", min_value=5, max_value=120, value=30)

    location = st.text_input("Enter your city for restaurant recommendations", "")

    if st.button("Find Recipe"):
        if search_type == "By Nutrients":
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
        
        if search_type == "By Nutrients" and details["nutrition"]:
            st.write("### 🔬 Nutrition Facts:")
            for nutrient in details["nutrition"]:
                st.write(f"- {nutrient['name']}: {nutrient['amount']} {nutrient['unit']}")

        if location:
            restaurants = get_restaurants(location, details.get("cuisine", ""))
            if restaurants:
                st.write("### 🍴 Nearby Restaurants:")
                for restaurant in restaurants:
                    st.write(f"- **{restaurant['name']}** ({restaurant['rating']}⭐) - {restaurant['location'].get('address1', 'Address not available')}")
            else:
                st.write("❌ No nearby restaurants found.")
else:
    st.write("👋 Welcome! Choose a search method above to find a recipe that suits you.")
