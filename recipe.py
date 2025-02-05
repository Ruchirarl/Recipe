import requests
import streamlit as st
from dotenv import load_dotenv
import os
load_dotenv()

# Load API keys from environment variables
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
    "Neuroticism": ["Healthy", "Mediterranean", "Comfort Food"]
}

def get_recipe(personality_trait, max_calories, quick_meal, dish_type):
    """
    Fetch a recipe from Spoonacular based on personality trait, max calorie intake,
    quick meal preference, and dish type (vegetarian or non-vegetarian).
    """
    cuisine_list = PERSONALITY_TO_CUISINE.get(personality_trait, ["Italian"])
    max_ready_time = 30 if quick_meal else 60
    
    url = f"https://api.spoonacular.com/recipes/random?apiKey={SPOONACULAR_API_KEY}&number=1&maxCalories={max_calories}&maxReadyTime={max_ready_time}"
    if dish_type.lower() in ["v", "vegetarian"]:
        url += "&diet=vegetarian"
    
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        if "recipes" in data and data["recipes"]:
            recipe = data["recipes"][0]
            return {
                "title": recipe["title"],
                "image": recipe["image"],
                "instructions": recipe.get("instructions", "No instructions provided.").replace(". ", ".<br>"),
                "ingredients": [ingredient["name"] for ingredient in recipe.get("extendedIngredients", [])],
                "cuisine": cuisine_list[0],
                "readyInMinutes": recipe.get("readyInMinutes", "N/A"),
                "servings": recipe.get("servings", "N/A"),
            }
    return None

def get_nutrition_info(ingredients):
    """Fetch nutritional information using Edamam API."""
    url = "https://api.edamam.com/api/nutrition-details"
    params = {"app_id": EDAMAM_API_ID, "app_key": EDAMAM_API_KEY}
    payload = {"ingr": ingredients}
    
    response = requests.post(url, json=payload, params=params)
    if response.status_code == 200:
        return response.json()
    return None

def get_restaurant_suggestions(location, cuisine):
    """Fetch restaurant suggestions based on cuisine and location using Yelp API."""
    url = "https://api.yelp.com/v3/businesses/search"
    headers = {"Authorization": f"Bearer {YELP_API_KEY}"}
    params = {"term": cuisine, "location": location, "limit": 5}
    
    response = requests.get(url, headers=headers, params=params)
    if response.status_code == 200:
        return response.json().get("businesses", [])
    return []

# Streamlit UI
st.title("🍽️ Personalized Recipe and Restaurant Finder")

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
        
        nutrition = get_nutrition_info(recipe["ingredients"])
        if nutrition:
            st.subheader("🔬 Nutrition Analysis:")
            st.write(f"Calories: {nutrition.get('calories', 'N/A')}")
            if "totalNutrients" in nutrition:
                st.write(f"Protein: {nutrition['totalNutrients'].get('PROCNT', {}).get('quantity', 'N/A')}g")
                st.write(f"Carbs: {nutrition['totalNutrients'].get('CHOCDF', {}).get('quantity', 'N/A')}g")
                st.write(f"Fats: {nutrition['totalNutrients'].get('FAT', {}).get('quantity', 'N/A')}g")
        
        if location:
            restaurants = get_restaurant_suggestions(location, recipe["cuisine"])
            if restaurants:
                st.subheader("🍴 Nearby Restaurants:")
                for r in restaurants:
                    st.write(f"- **{r['name']}** ({r.get('rating', 'N/A')}⭐) - {r['location'].get('address1', 'No address provided')}")
            else:
                st.write("❌ No nearby restaurants found.")
    else:
        st.write("❌ No recipe found, please try again later!")
        