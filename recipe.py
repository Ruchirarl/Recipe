import streamlit as st
import requests
import os

# Set Streamlit page title
st.set_page_config(page_title="BiteByType - Meals that fit your personality")

# Load environment variables from Streamlit secrets
SPOONACULAR_API_KEY = st.secrets["SPOONACULAR_API_KEY"]
EDAMAM_API_ID = st.secrets["EDAMAM_API_ID"]
EDAMAM_API_KEY = st.secrets["EDAMAM_API_KEY"]
YELP_API_KEY = st.secrets["YELP_API_KEY"]

# Mapping personality traits to cuisines
PERSONALITY_TO_CUISINE = {
    "Openness": ["Japanese", "Indian", "Mediterranean"],
    "Conscientiousness": ["Balanced", "Low-Carb", "Mediterranean"],
    "Extraversion": ["BBQ", "Mexican", "Italian"],
    "Agreeableness": ["Vegetarian", "Comfort Food", "Vegan"],
    "Neuroticism": ["Healthy", "Mediterranean", "Comfort Food"]
}

def get_recipe(personality_trait, max_calories, quick_meal, dish_type):
    cuisine_list = PERSONALITY_TO_CUISINE.get(personality_trait, ["Italian"])
    selected_cuisine = cuisine_list[0]
    max_ready_time = 30 if quick_meal else 60
    url = f"https://api.spoonacular.com/recipes/random?apiKey={SPOONACULAR_API_KEY}&number=1&maxCalories={max_calories}&maxReadyTime={max_ready_time}"
    
    if dish_type.lower() == "vegetarian":
        url += "&diet=vegetarian"
    
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data.get("recipes"):
            recipe = data["recipes"][0]
            return {
                "title": recipe["title"],
                "image": recipe["image"],
                "instructions": recipe["instructions"],
                "ingredients": [ingredient["name"] for ingredient in recipe["extendedIngredients"]],
                "cuisine": selected_cuisine,
                "calories": recipe["nutrition"]["nutrients"][0]["amount"],
                "protein": recipe["nutrition"]["nutrients"][8]["amount"],
                "fat": recipe["nutrition"]["nutrients"][1]["amount"]
            }
    return None

def get_nutrition_info(ingredients):
    url = "https://api.edamam.com/api/nutrition-details"
    params = {"app_id": EDAMAM_API_ID, "app_key": EDAMAM_API_KEY}
    payload = {"ingr": ingredients}
    response = requests.post(url, json=payload, params=params)
    if response.status_code == 200:
        return response.json()
    return None

def get_restaurant_suggestions(location, cuisine):
    url = "https://api.yelp.com/v3/businesses/search"
    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    params = {"term": cuisine, "location": location, "limit": 5}
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get("businesses", [])
    return []

# Streamlit App
st.title("🍽️ BiteByType - Meals that fit your personality")

personality = st.selectbox("Select your dominant personality trait", list(PERSONALITY_TO_CUISINE.keys()))
location = st.text_input("Enter your city or location (for restaurant suggestions)")
calorie_intake = st.number_input("Enter your desired calorie intake per meal", min_value=100, max_value=2000, value=500)
quick_meal = st.checkbox("Quick Meal (Under 30 minutes)")
dish_type = st.radio("Choose dish type", ["Vegetarian", "Non-Vegetarian"], index=0)

if st.button("Find Recipe"):
    recipe = get_recipe(personality, calorie_intake, quick_meal, dish_type)
    if recipe:
        st.subheader(f"🍽️ Recommended Recipe: {recipe['title']}")
        st.image(recipe['image'], width=400)
        st.write("### Ingredients:")
        st.write("\n".join([f"- {ingredient}" for ingredient in recipe["ingredients"]]))
        st.write("### Instructions:")
        st.write(recipe["instructions"])
        
        st.write("### 🔬 Nutrition Facts (from Spoonacular):")
        st.write(f"- **Calories:** {recipe['calories']} kcal")
        st.write(f"- **Protein:** {recipe['protein']} g")
        st.write(f"- **Fat:** {recipe['fat']} g")
        
        if location:
            restaurants = get_restaurant_suggestions(location, recipe["cuisine"])
            if restaurants:
                st.write("### 🍴 Nearby Restaurants:")
                for restaurant in restaurants:
                    st.write(f"- **{restaurant['name']}** ({restaurant['rating']}⭐) - {restaurant['location'].get('address1', 'Address not available')}")
            else:
                st.write("❌ No nearby restaurants found.")
    else:
        st.write("❌ No recipe found, try again later!")
