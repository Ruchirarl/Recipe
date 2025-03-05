import streamlit as st  # Importing Streamlit for building the web app
import requests  # Importing requests to make API calls
import os  # Importing os to manage environment variables (not needed here since Streamlit secrets are used)

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
    "Openness": ["Japanese", "Indian", "Mediterranean"],  # People who are open to experiences might enjoy diverse flavors.
    "Conscientiousness": ["Balanced", "Low-Carb", "Mediterranean"],  # Health-conscious and balanced meal choices.
    "Extraversion": ["BBQ", "Mexican", "Italian"],  # Social personalities may prefer bold, flavorful, and shared meals.
    "Agreeableness": ["Vegetarian", "Comfort Food", "Vegan"],  # Kind and empathetic personalities may favor plant-based and homey meals.
    "Neuroticism": ["Healthy", "Mediterranean", "Comfort Food"],  # People prone to stress might seek comfort food or healthy options.
    "Adventurous": ["Thai", "Korean", "Ethiopian"],  # Those who love new experiences might prefer bold, exotic cuisines.
    "Analytical": ["French", "Greek", "Fusion"],  # Logical thinkers may appreciate refined, well-balanced, and innovative meals.
    "Creative": ["Molecular Gastronomy", "Experimental", "Fusion"],  # Artistic individuals might enjoy innovative and avant-garde dishes.
    "Traditional": ["American", "British", "German"]  # Those who value tradition may prefer classic and hearty dishes.
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
        if response.status_code == 200:  # Checks if the API request was successful
            return response.json()  # Returns the parsed JSON response
        else:
            return None  # Returns None if the API call fails
    except requests.RequestException:  # Handles network errors or failed API requests
        return None  # Returns None if an exception occurs

def get_recipe_by_personality(personality, diet):
    """Fetch a recipe based on personality and diet preferences."""
    
    # Retrieve the primary cuisine based on the personality trait, defaulting to "Italian" if not found
    cuisine = PERSONALITY_TO_CUISINE.get(personality, ["Italian"])[0]
    
    # Define the API endpoint for fetching a random recipe
    url = "https://api.spoonacular.com/recipes/random"
    
    # Set the query parameters for the API request
    params = {
        "apiKey": SPOONACULAR_API_KEY,  # API key for authentication
        "number": 1,  # Request only one recipe
        "diet": diet,  # Apply diet preference filter
        "cuisine": cuisine,  # Apply cuisine filter based on personality
        "instructionsRequired": True  # Ensure that recipes include instructions
    }
    
    # Fetch data from the API
    data = fetch_api(url, params)
    
    # Return the first recipe if available, otherwise return None
    return data.get("recipes", [None])[0] if data else None

def get_recipe_by_ingredient(ingredient, max_time):
    """Fetch a recipe based on an ingredient and preparation time."""
    
    # Define the API endpoint for searching recipes by ingredient
    url = "https://api.spoonacular.com/recipes/complexSearch"
    
    # Set the query parameters for the API request
    params = {
        "apiKey": SPOONACULAR_API_KEY,  # API key for authentication
        "includeIngredients": ingredient,  # Filter recipes by the specified ingredient
        "maxReadyTime": max_time,  # Filter recipes by maximum preparation time
        "number": 1,  # Request only one recipe
        "instructionsRequired": True  # Ensure that recipes include instructions
    }
    
    # Fetch data from the API
    data = fetch_api(url, params)
    
    # If results exist, fetch full recipe details using the recipe ID, otherwise return None
    return get_recipe_details_by_id(data["results"][0]["id"]) if data and data.get("results") else None


def get_recipe_by_nutrients(nutrient, min_value, max_value, max_time):
    """Fetch a recipe based on nutritional content."""
    
    # Define the API endpoint for searching recipes by nutrient values
    url = "https://api.spoonacular.com/recipes/findByNutrients"
    
    # Set the query parameters for the API request
    params = {
        "apiKey": SPOONACULAR_API_KEY,  # API key for authentication
        "addRecipeNutrition": True,  # Include detailed nutritional information in the response
        f"min{nutrient}": min_value,  # Minimum threshold for the selected nutrient
        f"max{nutrient}": max_value,  # Maximum threshold for the selected nutrient 
        "maxReadyTime": max_time,  # Filter recipes by maximum preparation time
        "number": 1  # Request only one recipe
        
    }
    
    # Fetch data from the API
    data = fetch_api(url, params)
    
    # If data is available, retrieve detailed recipe information using its ID, otherwise return None
    return get_recipe_details_by_id(data[0]["id"]) if data else None

def get_recipe_details_by_id(recipe_id):
    """Fetch detailed recipe information by ID."""
    
    # Construct the API URL using the recipe ID
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    
    # Set the query parameters for the API request
    params = {
        "apiKey": SPOONACULAR_API_KEY,  # API key for authentication
        "includeNutrition": True  # Include nutritional information in the response
    }
    
    # Fetch and return detailed recipe data
    return fetch_api(url, params)
def scrape_allrecipes(meal_type_url):
    """Scrapes a random recipe from AllRecipes for the selected meal type."""
    headers = {"User-Agent": "Mozilla/5.0"}
    
    # Step 1: Fetch the meal category page
    response = requests.get(meal_type_url, headers=headers)
    if response.status_code != 200:
        st.error("Failed to fetch the meal type page.")
        return None

    soup = BeautifulSoup(response.text, "lxml")

    # Step 2: Find all valid recipe links (excluding articles)
    all_recipe_links = soup.select("a[href*='/recipe/']")  # Only valid recipes

    if not all_recipe_links:
        st.error("No recipes found. The HTML structure might have changed.")
        return None

    # ✅ Pick a random recipe instead of always selecting the first one
    recipe_url = random.choice(all_recipe_links)["href"]

    # Step 3: Fetch the detailed recipe page
    recipe_response = requests.get(recipe_url, headers=headers)
    if recipe_response.status_code != 200:
        st.error("Failed to fetch the recipe page.")
        return None

    recipe_soup = BeautifulSoup(recipe_response.text, "lxml")

    # Extract title
    title_tag = recipe_soup.find("h1")
    title = title_tag.text.strip() if title_tag else "Unknown Recipe"

    # Extract image (Fix missing images)
    image_tag = recipe_soup.select_one("img.card__img")
    if image_tag:
        image_url = image_tag.get("data-src", image_tag.get("src", ""))
    else:
        image_url = ""

    # Extract ingredients
    ingredients = [ing.get_text(strip=True) for ing in recipe_soup.select(".mm-recipes-structured-ingredients__list-item")]

    # Extract instructions
    instructions = [step.get_text(strip=True) for step in recipe_soup.select(".mntl-sc-block-html")]

    # Extract Nutrition Facts (Now Fixed)
    nutrition_facts = []
    nutrition_table = recipe_soup.select_one(".mm-recipes-nutrition-facts-label__table")
    
    if nutrition_table:
        for row in nutrition_table.find_all("tr"):
            columns = row.find_all("td")
            if len(columns) == 2:
                nutrient_name = columns[0].get_text(strip=True)
                nutrient_value = columns[1].get_text(strip=True)
                nutrition_facts.append(f"{nutrient_name}: {nutrient_value}")

    return {
        "title": title,
        "image": image_url,
        "ingredients": ingredients,
        "instructions": instructions,
        "nutrition": nutrition_facts
    }
@st.cache_data
def get_restaurants(location, cuisine):
    """Fetch nearby restaurants using Yelp API."""
    
    # Define the API endpoint for searching restaurants
    url = "https://api.yelp.com/v3/businesses/search"
    
    # Set the request headers with API key for authentication
    headers = {
        "Authorization": f"Bearer {YELP_API_KEY}"
    }
    
    # Set the query parameters for the API request
    params = {
        "term": cuisine,  # Search term based on cuisine type
        "location": location,  # User-provided location
        "limit": 5  # Limit the number of returned results to 5
    }
    
    try:
        # Send the API request
        response = requests.get(url, headers=headers, params=params)
        
        # If the request is successful, return the list of businesses, otherwise return an empty list
        return response.json().get("businesses", []) if response.status_code == 200 else []
    
    except requests.RequestException:
        # Handle any request errors and return an empty list
        return []

## Streamlit App UI

# Create a radio button to choose the recipe search type
search_type = st.radio(
    "## How would you like to find a recipe?", 
    ["By Personality", "By Ingredient", "By Nutrients"], 
    index=None
)

# Initialize recipe variable
recipe = None

# If a search type is selected, display corresponding input fields
if search_type:
    
    # Search by Personality
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

    # Search by Ingredient
    elif search_type == "By Ingredient":
        # Text input for entering the main ingredient
        ingredient = st.text_input("Enter an ingredient")
        
        # Slider for selecting maximum preparation time
        max_time = st.slider(
            "Max preparation time (minutes)", 
            5, 120, 30
        )

    # Search by Nutrients
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

    # Input field for entering the location to find nearby restaurants
    location = st.text_input("Enter your location for a restaurant recommendations")

    # Button to trigger the recipe search
    if st.button("Find Recipe"):
        if search_type == "By Personality":
            recipe = get_recipe_by_personality(personality, diet)
        elif search_type == "By Ingredient":
            recipe = get_recipe_by_ingredient(ingredient, max_time)
        elif search_type == "By Nutrients":
            recipe = get_recipe_by_nutrients(nutrient, min_value, max_value, max_time)
        elif search_type == "By Meal Type":
            meal_type = st.selectbox("Choose a Meal Type", list(meal_types.keys()))

    if st.button("Find Recipe"):
        recipe1 = scrape_allrecipes(meal_types[meal_type])

# Display Recipe Details
if recipe1:
    st.subheader(f"🍽 Recommended Recipe: {recipe.get('title')}")
    
    # ✅ Display recipe image (with caption)
    if recipe1.get("image"):
        st.image(recipe["image"], width=400, caption="Recipe Image")

    # ✅ Display ingredients
    if recipe1.get("ingredients"):
        st.write("### 🛒 Ingredients:")
        for ing in recipe1["ingredients"]:
            st.write(f"- {ing}")

    # ✅ Display instructions
    if recipe1.get("instructions"):
        st.write("### 🍽 Instructions:")
        for idx, step in enumerate(recipe["instructions"], start=1):
            st.write(f"{idx}. {step}")

    # ✅ Display Nutrition Facts
    if recipe1.get("nutrition"):
        st.write("### 🥗 Nutrition Facts:")
        for fact in recipe["nutrition"]:
            st.write(f"- {fact}")


# If a recipe is found, display the details
if recipe1:
    st.subheader(f"Recommended Recipe: {recipe1.get('title', 'No title')}")
    
    # Display recipe image if available
    st.image(recipe1.get("image", ""), width=400)
    
    # Display preparation time for all recipe types
    st.write(f"### **Total Preparation Time:** {recipe1.get('readyInMinutes', 'N/A')} minutes")

    # Display ingredients list
    st.write("### Ingredients:")
    st.write("\n".join(f"- {i['original']}" for i in recipe1.get("extendedIngredients", [])))
    
    # Display cooking instructions
    st.write("### Instructions:")
    st.write(recipe1.get("instructions", "No instructions available."))

    # Display nutrition details if available
    if 'nutrition' in recipe1 and 'nutrients' in recipe1['nutrition']:
        st.write("### Nutrition Information:")
        for nutrient in recipe1['nutrition']['nutrients']:
            st.write(f"- {nutrient['name']}: {nutrient['amount']} {nutrient['unit']}")


    # If location is provided, fetch nearby restaurants
    if location:
        restaurants = get_restaurants(location, recipe.get("cuisine", ""))
        
        # Display nearby restaurants if found
        if restaurants:
            st.write("### Nearby Restaurants:")
            for r in restaurants:
                st.write(f"- {r['name']} ({r['rating']}⭐) - {r['location'].get('address1', 'Address not available')}")
        else:
            st.write("No nearby restaurants found.")

# If no recipe is found, show a welcome message
else:
    st.write("Welcome! Choose a search method above to find a recipe that suits you.")