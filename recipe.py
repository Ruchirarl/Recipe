import os
import requests
import streamlit as st
from dotenv import load_dotenv

# Load API keys from .env file
load_dotenv()

SPOONACULAR_API_KEY = os.getenv("SPOONACULAR_API_KEY")
EDAMAM_API_ID = os.getenv("EDAMAM_API_ID")
EDAMAM_API_KEY = os.getenv("EDAMAM_API_KEY")
YELP_API_KEY = os.getenv("YELP_API_KEY")

# Mapping personality traits to cuisines
PERSONALITY_TO_CUISINE = {
    "Openness": ["Japanese", "Indian", "Mediterranean"],
    "Conscientiousness": ["Balanced", "Low-Carb", "Mediterranean"],
    "Extraversion": ["BBQ", "Mexican", "Italian"],
    "Agreeableness": ["Vegetarian", "Comfort Food", "Vegan"],
    "Neuroticism": ["Healthy", "Mediterranean", "Comfort Food"],
    "Adventurous": ["Thai", "Ethiopian", "Korean"],
    "Romantic": ["French", "Italian", "Greek"],
    "Practical": ["American", "Mediterranean", "Farm-to-Table"],
    "Energetic": ["Smoothies", "Mexican", "Fusion"],
    "Relaxed": ["Comfort Food", "Soup & Stews", "Tea-based Dishes"]
}

def get_recipe(personality_trait, max_calories, quick_meal, dish_type, retries=3):
    """ Fetches a recipe from Spoonacular API with proper debugging. """

    cuisine_list = PERSONALITY_TO_CUISINE.get(personality_trait, ["Italian"])
    max_ready_time = 30 if quick_meal else 60

    url = f"https://api.spoonacular.com/recipes/random?apiKey={SPOONACULAR_API_KEY}&number=1"

    # Apply filters if they make sense
    if max_calories > 100:  # Avoid extreme restrictions
        url += f"&nutritionFilter=calories<{max_calories}"
    if max_ready_time:
        url += f"&maxReadyTime={max_ready_time}"
    if dish_type.lower() in ["v", "vegetarian"]:
        url += "&diet=vegetarian"

    # Debugging: Print API request URL
    print(f"🔗 API Request URL: {url}")

    for attempt in range(retries):
        response = requests.get(url)

        # Debugging: Print API response status
        print(f"📡 API Response Attempt {attempt+1}: Status {response.status_code}")

        try:
            data = response.json()
            print(f"📜 API Response Data: {data}")  # Debugging print
        except Exception as e:
            print(f"❌ Error parsing JSON response: {e}")
            continue

        if response.status_code == 200 and "recipes" in data and data["recipes"]:
            recipe = data["recipes"][0]
            return {
                "title": recipe["title"],
                "image": recipe["image"],
                "instructions": recipe.get("instructions", "No instructions provided."),
                "ingredients": [ingredient["name"] for ingredient in recipe.get("extendedIngredients", [])],
                "cuisine": cuisine_list[0],
                "readyInMinutes": recipe.get("readyInMinutes", "N/A"),
                "servings": recipe.get("servings", "N/A"),
            }
    
    # Backup request without filters if no recipe is found
    print("⚠️ No recipe found with filters. Retrying without filters...")
    backup_url = f"https://api.spoonacular.com/recipes/random?apiKey={SPOONACULAR_API_KEY}&number=1"
    response = requests.get(backup_url)
    if response.status_code == 200:
        data = response.json()
        if "recipes" in data and data["recipes"]:
            recipe = data["recipes"][0]
            return {
                "title": recipe["title"],
                "image": recipe["image"],
                "instructions": recipe.get("instructions", "No instructions provided."),
                "ingredients": [ingredient["name"] for ingredient in recipe.get("extendedIngredients", [])],
                "cuisine": "General",
                "readyInMinutes": recipe.get("readyInMinutes", "N/A"),
                "servings": recipe.get("servings", "N/A"),
            }
    
    return None

# Streamlit UI
st.set_page_config(page_title="BiteByType - Meals that Fit Your Personality")
st.title("🍽️ BiteByType - Meals that Fit Your Personality")

personality = st.selectbox("Select your dominant personality trait:", list(PERSONALITY_TO_CUISINE.keys()))
location = st.text_input("Enter your city or location:")
calorie_intake = st.number_input("Enter your desired calorie intake per meal (in calories):", min_value=100, max_value=2000, value=500)
quick_meal = st.checkbox("Do you want a quick meal (under 30 minutes)?")
dish_type = st.radio("Choose your preference:", ["Vegetarian (v)", "Non-Vegetarian (nv)"])
dish_type = "v" if "Vegetarian" in dish_type else "nv"

if st.button("Find Recipe"):
    recipe = get_recipe(personality, calorie_intake, quick_meal, dish_type)
    if recipe:
        st.subheader(f"🍽️ Recommended Recipe: {recipe['title']}")
        st.image(recipe['image'], use_column_width=True)
        st.write(f"⏳ Ready in: {recipe['readyInMinutes']} minutes")
        st.write(f"🍽️ Servings: {recipe['servings']}")
        
        st.write("📌 **Ingredients:**")
        st.write("\n".join([f"- {ingredient}" for ingredient in recipe["ingredients"]]))
        st.write("📖 **Instructions:**")
        st.markdown(recipe["instructions"], unsafe_allow_html=True)
    else:
        st.write("❌ No recipe found. Please try again later!")
