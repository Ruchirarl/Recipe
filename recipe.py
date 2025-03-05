import streamlit as st
import requests
import pandas as pd
from bs4 import BeautifulSoup

# API Keys (Load from Streamlit secrets)
SPOONACULAR_API_KEY = st.secrets["SPOONACULAR_API_KEY"]

# Streamlit App Configuration
st.set_page_config(page_title="🍽 BiteByType - Personalized Recipes")
st.title("🍽 BiteByType - Personalized Recipes")

st.markdown("""
    ## 🥗 Welcome to BiteByType!
    BiteByType is your personalized meal finder, helping you discover recipes tailored to your dietary preferences! 🥦🍲

    🔍 How It Works:
    - Choose a recipe *By Nutrients 🏋‍♂*.
    - Find recipes that match your taste and lifestyle!
    - Let's find your next favorite meal! 🍽✨
""")

# --- API Utility Function ---
@st.cache_data
def fetch_api(url, params):
    """Fetches data from an API and returns JSON response."""
    try:
        response = requests.get(url, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: Status code {response.status_code}")
            return None
    except requests.RequestException as e:
        st.error(f"Request Exception: {e}")
        return None

# --- Wikipedia Data Function ---
@st.cache_data
def get_wiki_food_nutrients():
    """Fetch and parse the Wikipedia table of food nutrients."""
    try:
        url = "https://en.wikipedia.org/wiki/Table_of_food_nutrients"
        response = requests.get(url)
        if response.status_code != 200:
            return {"status": "error", "message": f"Failed to fetch page. Status code: {response.status_code}"}

        soup = BeautifulSoup(response.text, 'html.parser')
        tables = soup.find_all('table', {'class': 'wikitable'})

        if not tables:
            return {"status": "error", "message": "No tables found on the Wikipedia page"}

        nutrient_table = tables[0]  # Assuming first table contains the required data
        data = []
        rows = nutrient_table.find_all('tr')

        # Extract headers
        headers = [th.text.strip() for th in rows[0].find_all('th')]

        # Extract data
        for row in rows[1:]:
            cols = row.find_all('td')
            cols = [ele.text.strip() for ele in cols]
            if cols:
                data.append(dict(zip(headers, cols)))

        return {"status": "success", "data": data}

    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- Recipe Search by Nutrients ---
def get_recipe_by_nutrients(nutrient, min_value, max_value, max_time):
    """Fetch recipes based on nutrient range, using Wikipedia data to identify vegetables."""
    wiki_data = get_wiki_food_nutrients()

    if wiki_data["status"] == "success":
        df = pd.DataFrame(wiki_data["data"])  # Convert to DataFrame for filtering

        # Standardize column names
        df.columns = df.columns.str.lower().str.strip()

        # Convert nutrient values to numeric (handling potential issues)
        df[nutrient.lower()] = pd.to_numeric(df[nutrient.lower()], errors='coerce')

        # Filter vegetables based on user input
        filtered_df = df[(df[nutrient.lower()] >= min_value) & (df[nutrient.lower()] <= max_value)]

        if not filtered_df.empty:
            selected_vegetable = filtered_df.iloc[0]["food"]  # Pick the first match
            st.write(f"### Selected Vegetable: {selected_vegetable}")

            # Fetch recipe from Spoonacular
            url = "https://api.spoonacular.com/recipes/findByIngredients"
            params = {
                "apiKey": SPOONACULAR_API_KEY,
                "ingredients": selected_vegetable,
                "number": 1,
                "ranking": 1
            }

            recipe_data = fetch_api(url, params)
            
            if recipe_data and recipe_data[0]:
                return get_recipe_details_by_id(recipe_data[0]["id"])
            else:
                st.write("No recipes found for this vegetable.")
                return None
        else:
            st.write("No vegetables match your selected nutrient range.")
            return None
    else:
        st.write(f"Error fetching Wikipedia data: {wiki_data['message']}")
        return None

def get_recipe_details_by_id(recipe_id):
    """Fetch detailed recipe information by ID."""
    url = f"https://api.spoonacular.com/recipes/{recipe_id}/information"
    params = {"apiKey": SPOONACULAR_API_KEY, "includeNutrition": True}
    return fetch_api(url, params)

# --- Streamlit UI ---
st.subheader("Find Recipes by Nutrient Content")

# Create UI Elements
nutrient = st.selectbox("Select Nutrient", ["Calories", "Protein", "Fat"])
min_value = st.number_input("Min Value", 10, 500, 100)
max_value = st.number_input("Max Value", 10, 500, 200)
max_time = st.slider("Max Time (minutes)", 5, 120, 30)

if st.button("Find Recipe"):
    recipe = get_recipe_by_nutrients(nutrient, min_value, max_value, max_time)

    if recipe:
        st.subheader(f"Recommended Recipe: {recipe.get('title', 'No title')}")
        
        # Display recipe image if available
        st.image(recipe.get("image", ""), width=400)

        # Display preparation time
        st.write(f"### *Total Preparation Time:* {recipe.get('readyInMinutes', 'N/A')} minutes")

        # Display ingredients list
        st.write("### Ingredients:")
        st.write("\n".join(f"- {i['original']}" for i in recipe.get("extendedIngredients", [])))

        # Display cooking instructions
        st.write("### Instructions:")
        st.write(recipe.get("instructions", "No instructions available."))

        # Display nutrition details if available
        if 'nutrition' in recipe and 'nutrients' in recipe['nutrition']:
            st.write("### Nutrition Information:")
            for nutrient in recipe['nutrition']['nutrients']:
                st.write(f"- {nutrient['name']}: {nutrient['amount']} {nutrient['unit']}")

    else:
        st.write("No suitable recipe found.")