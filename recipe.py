import streamlit as st  # Importing Streamlit for building the web app
import requests  # Importing requests to make API calls
import os  # Importing os to manage environment variables (not needed here since Streamlit secrets are used)
from bs4 import BeautifulSoup  # For scraping AllRecipes
import random  # For picking a random recipe from AllRecipes

# ──────────────────────────────────────────────────────────
#               1) YOUR ORIGINAL CODE
# ──────────────────────────────────────────────────────────

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
    BiteByType is your personalized meal finder, helping you discover recipes tailored to your personality, dietary preferences, and nutritional needs! 🥦🍲
    
    🔍 How It Works:
    - Choose a recipe By Personality 🎭, By Ingredient 🥑, or By Nutrients 🏋‍♂.
    - Find recipes that match your taste and lifestyle!
    - Explore restaurants nearby serving similar cuisines!
    
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

@st.cache_data  # Caches API responses to optimize performance and reduce redundant API calls
def fetch_api(url, params):
    """Fetches data from an API and returns JSON response."""
    try:
        response = requests.get(url, params=params)  # Makes a GET request to the API with given parameters
        if response.status_code == 200:  
            return response.json()  
        else:
            return None  
    except requests.RequestException: 
        return None  

def get_recipe_by_personality(personality, diet):
    """Fetch a recipe based on personality and diet preferences."""
    cuisine = PERSONALITY_TO_CUISINE.get(personality, ["Italian"])[0]
    url = "https://api.spoonacular.com/recipes/random"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "number": 1,
        "diet": diet,
        "cuisine": cuisine,
        "instructionsRequired": True
    }
    data = fetch_api(url, params)
    return data.get("recipes", [None])[0] if data else None

def get_recipe_by_ingredient(ingredient, max_time):
    """Fetch a recipe based on an ingredient and preparation time."""
    url = "https://api.spoonacular.com/recipes/complexSearch"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "includeIngredients": ingredient,
        "maxReadyTime": max_time,
        "number": 1,
        "instructionsRequired": True
    }
    data = fetch_api(url, params)
    return get_recipe_details_by_id(data["results"][0]["id"]) if data and data.get("results") else None

def get_recipe_by_nutrients(nutrient, min_value, max_value, max_time):
    """Fetch a recipe based on nutritional content."""
    url = "https://api.spoonacular.com/recipes/findByNutrients"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "addRecipeNutrition": True,
        f"min{nutrient}": min_value,
        f"max{nutrient}": max_value,
        "maxReadyTime": max_time,
        "number": 1
    }
    data = fetch_api(url, params)
    return get_recipe_details_by_id(data[0]["id"]) if data else None

def get_recipe_details_by_id(recipe_id):
    """Fetch detailed recipe information by ID."""
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    params = {
        "apiKey": SPOONACULAR_API_KEY,
        "includeNutrition": True
    }
    return fetch_api(url, params)

@st.cache_data
def get_restaurants(location, cuisine):
    """Fetch nearby restaurants using Yelp API."""
    url = "https://api.yelp.com/v3/businesses/search"
    headers = {
        "Authorization": f"Bearer {YELP_API_KEY}"
    }
    params = {
        "term": cuisine,
        "location": location,
        "limit": 5
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        return response.json().get("businesses", []) if response.status_code == 200 else []
    except requests.RequestException:
        return []

# ──────────────────────────────────────────────────────────
#         2) ADD A "By Meal Type" OPTION (AllRecipes)
# ──────────────────────────────────────────────────────────

# This function will scrape AllRecipes, but return a dict
# shaped like the Spoonacular response so it displays
# *without* altering your existing display code.
def get_recipe_by_meal_type(meal_type_url):
    """Scrapes a random recipe from AllRecipes for the selected meal type."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(meal_type_url, headers=headers)
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "lxml")
    all_recipe_links = soup.select("a[href*='/recipe/']")
    if not all_recipe_links:
        return None

    recipe_url = random.choice(all_recipe_links)["href"]
    recipe_response = requests.get(recipe_url, headers=headers)
    if recipe_response.status_code != 200:
        return None

    recipe_soup = BeautifulSoup(recipe_response.text, "lxml")

    # Extract title
    title_tag = recipe_soup.find("h1")
    title = title_tag.text.strip() if title_tag else "Unknown Recipe"

    # Extract image
    image_tag = recipe_soup.select_one("img.card__img")
    if image_tag:
        image_url = image_tag.get("data-src", image_tag.get("src", ""))
    else:
        image_url = ""

    # Ingredients -> We'll store them as 'extendedIngredients' with 'original' for each line
    raw_ingredients = [ing.get_text(strip=True) for ing in recipe_soup.select(".mm-recipes-structured-ingredients__list-item")]
    extended_ingredients = [{"original": ing} for ing in raw_ingredients]

    # Instructions -> We'll combine all steps into a single string
    raw_instructions = [step.get_text(strip=True) for step in recipe_soup.select(".mntl-sc-block-html")]
    instructions = "\n".join(raw_instructions) if raw_instructions else "No instructions available."

    # Attempt to find a nutrition table (some recipes might not have it)
    raw_nutrition = []
    nutrition_table = recipe_soup.select_one(".mm-recipes-nutrition-facts-label__table")
    if nutrition_table:
        for row in nutrition_table.find_all("tr"):
            columns = row.find_all("td")
            if len(columns) == 2:
                nutrient_name = columns[0].get_text(strip=True)
                nutrient_value = columns[1].get_text(strip=True)
                raw_nutrition.append(f"{nutrient_name}: {nutrient_value}")

    # We'll fit this into the same structure Spoonacular returns:
    # recipe["nutrition"]["nutrients"] is expected to be a list of dicts with name, amount, unit
    # We'll parse the lines "Calories: 200" for example
    parsed_nutrients = []
    for fact in raw_nutrition:
        # e.g. "Calories: 200"
        parts = fact.split(":")
        if len(parts) == 2:
            n_name = parts[0].strip()
            n_value = parts[1].strip()
            # We'll treat everything after the name as 'amount' + 'unit'
            # e.g. "200 cals" → "200", "cals"
            # This is a bit improvised since AllRecipes data can vary
            # We'll just put the entire 'n_value' in 'amount'
            # and leave 'unit' blank
            parsed_nutrients.append({
                "name": n_name,
                "amount": n_value,
                "unit": ""
            })

    # Return a dictionary that mirrors Spoonacular's structure
    return {
        "title": title,
        "image": image_url,
        "readyInMinutes": "N/A",  # AllRecipes doesn't provide
        "extendedIngredients": extended_ingredients,
        "instructions": instructions,
        "nutrition": {
            "nutrients": parsed_nutrients
        }
    }

# ──────────────────────────────────────────────────────────
#        3) UPDATE THE RADIO FOR THE 4th OPTION
# ──────────────────────────────────────────────────────────

# Create a radio button to choose the recipe search type
search_type = st.radio(
    "## How would you like to find a recipe?", 
    ["By Personality", "By Ingredient", "By Nutrients", "By Meal Type"], 
    index=None
)

# Initialize recipe variable
recipe = None

# If a search type is selected, display corresponding input fields
if search_type:
    if search_type == "By Personality":
        # Dropdown for selecting dominant personality trait
        personality = st.selectbox(
            "Select your dominant personality trait", 
            list(PERSONALITY_TO_CUISINE.keys()), 
            index=None
        )
        # Dropdown for selecting diet preference
        diet = st.selectbox(
            "Choose your diet preference", 
            diet_types, 
            index=None
        )

    elif search_type == "By Ingredient":
        # Text input for entering the main ingredient
        ingredient = st.text_input("Enter an ingredient")
        # Slider for selecting maximum preparation time
        max_time = st.slider(
            "Max preparation time (minutes)", 
            5, 120, 30
        )

    elif search_type == "By Nutrients":
        # Dropdown for selecting a nutrient type
        nutrient = st.selectbox(
            "Choose a nutrient", 
            ["Calories", "Protein", "Fat"]
        )
        
        # Input fields for specifying min and max values of the nutrient
        min_value = st.number_input(
            f"Min {nutrient} (10)", 
            min_value=10, 
            value=100
        )
        
        max_value = st.number_input(
            f"Max {nutrient} (100)", 
            min_value=10, 
            value=100
        )
        
        # Slider for selecting maximum preparation time
        max_time = st.slider(
            "Max preparation time (minutes)", 
            5, 120, 30
        )

    elif search_type == "By Meal Type":
        # NEW: "By Meal Type" (AllRecipes)
        st.markdown("### Choose a Meal Type to Fetch a Random Recipe from AllRecipes")
        meal_types = {
            "Breakfast": "https://www.allrecipes.com/recipes/78/breakfast-and-brunch/",
            "Lunch": "https://www.allrecipes.com/recipes/17561/lunch/",
            "Dinner": "https://www.allrecipes.com/recipes/17562/dinner/",
            "Snacks": "https://www.allrecipes.com/recipes/76/appetizers-and-snacks/"
        }
        selected_meal_type = st.selectbox("Select a Meal Type", list(meal_types.keys()))

    # Input field for entering the location to find nearby restaurants (applies to all, if user wants)
    location = st.text_input("Enter your location for restaurant recommendations")

    # Button to trigger the recipe search
    if st.button("Find Recipe"):
        if search_type == "By Personality":
            recipe = get_recipe_by_personality(personality, diet)
        elif search_type == "By Ingredient":
            recipe = get_recipe_by_ingredient(ingredient, max_time)
        elif search_type == "By Nutrients":
            recipe = get_recipe_by_nutrients(nutrient, min_value, max_value, max_time)
        elif search_type == "By Meal Type":
            recipe = get_recipe_by_meal_type(meal_types[selected_meal_type])

# If a recipe is found, display the details
if recipe:
    st.subheader(f"Recommended Recipe: {recipe.get('title', 'No title')}")
    
    # Display recipe image if available
    st.image(recipe.get("image", ""), width=400)
    
    # Display preparation time
    st.write(f"### **Total Preparation Time:** {recipe.get('readyInMinutes', 'N/A')} minutes")

    # Display ingredients list
    st.write("### Ingredients:")
    st.write("\n".join(f"- {i['original']}" for i in recipe.get("extendedIngredients", [])))
    
    # Display cooking instructions
    st.write("### Instructions:")
    st.write(recipe.get("instructions", "No instructions available."))

    # Display nutrition details if available
    if 'nutrition' in recipe and 'nutrients' in recipe['nutrition']:
        st.write("### Nutrition Information:")
        for n in recipe['nutrition']['nutrients']:
            # We'll just print the name + amount + unit
            st.write(f"- {n['name']}: {n['amount']} {n['unit']}")

    # If location is provided, fetch nearby restaurants
    if location:
        restaurants = get_restaurants(location, recipe.get("cuisine", "")) or []
        
        if restaurants:
            st.write("### Nearby Restaurants:")
            for r in restaurants:
                st.write(f"- {r['name']} ({r['rating']}⭐) - {r['location'].get('address1', 'Address not available')}")
        else:
            st.write("No nearby restaurants found.")

# If no recipe is found yet, show a welcome message
else:
    st.write("Welcome! Choose a search method above to find a recipe that suits you.")
