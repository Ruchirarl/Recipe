import streamlit as st
import requests
from bs4 import BeautifulSoup

# Set page config
st.set_page_config(page_title="🍽 BiteByType - Personalized Meal Finder")

# Meal types mapped to AllRecipes URLs
meal_types = {
    "Breakfast": "https://www.allrecipes.com/recipes/78/breakfast-and-brunch/",
    "Lunch": "https://www.allrecipes.com/recipes/17561/lunch/",
    "Dinner": "https://www.allrecipes.com/recipes/17562/dinner/",
    "Snacks": "https://www.allrecipes.com/recipes/76/appetizers-and-snacks/"
}

### AllRecipes Web Scraper ###
@st.cache_data
def scrape_allrecipes(meal_type_url):
    """Scrapes a full recipe from AllRecipes for the selected meal type."""
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(meal_type_url, headers=headers)
    
    if response.status_code != 200:
        return None

    soup = BeautifulSoup(response.text, "lxml")
    
    # Find the first recipe link
    first_recipe_card = soup.find("article", class_="fixed-recipe-card")
    if not first_recipe_card:
        return None

    title_tag = first_recipe_card.find("span", class_="fixed-recipe-card__title-link")
    link_tag = first_recipe_card.find("a", class_="fixed-recipe-card__title-link")

    if not title_tag or not link_tag:
        return None

    recipe_title = title_tag.get_text(strip=True)
    recipe_url = link_tag.get("href")

    # Now fetch the detailed recipe page
    recipe_response = requests.get(recipe_url, headers=headers)
    if recipe_response.status_code != 200:
        return None

    recipe_soup = BeautifulSoup(recipe_response.text, "lxml")

    # Extract image
    image_tag = recipe_soup.find("img", class_="mntl-image")
    image_url = image_tag["src"] if image_tag else ""

    # Extract ingredients
    ingredients = []
    for ing in recipe_soup.select(".mm-recipes-structured-ingredients__list-item"):
        ingredients.append(ing.get_text(strip=True))

    # Extract instructions
    instructions = []
    for step in recipe_soup.select(".mntl-sc-block-html"):
        instructions.append(step.get_text(strip=True))

    # Extract Nutrition Facts
    nutrition_facts = []
    for row in recipe_soup.select(".mm-recipes-nutrition-facts-summary__table-row"):
        columns = row.find_all("td")
        if len(columns) == 2:
            nutrition_facts.append(f"{columns[1].get_text(strip=True)}: {columns[0].get_text(strip=True)}")

    return {
        "title": recipe_title,
        "image": image_url,
        "ingredients": ingredients,
        "instructions": instructions,
        "nutrition": nutrition_facts
    }

### Streamlit UI ###
st.title("🍽 BiteByType - Find Meals by Meal Type")

st.markdown("""
## How It Works:
1. Choose a **Meal Type** 🍽
2. Get a full **recipe** from **AllRecipes** (including ingredients, steps, and nutrition).
""")

# Select meal type
meal_type = st.selectbox("Choose a Meal Type", list(meal_types.keys()))

if st.button("Find Recipe"):
    recipe = scrape_allrecipes(meal_types[meal_type])

    if recipe:
        st.subheader(f"🍽 Recommended Recipe: {recipe['title']}")
        
        # Display recipe image
        if recipe["image"]:
            st.image(recipe["image"], width=400)

        # Display ingredients
        if recipe["ingredients"]:
            st.write("### Ingredients:")
            for ing in recipe["ingredients"]:
                st.write(f"- {ing}")

        # Display instructions
        if recipe["instructions"]:
            st.write("### Instructions:")
            for idx, step in enumerate(recipe["instructions"], start=1):
                st.write(f"{idx}. {step}")

        # Display nutrition facts
        if recipe["nutrition"]:
            st.write("### Nutrition Facts:")
            for fact in recipe["nutrition"]:
                st.write(f"- {fact}")

    else:
        st.warning("No recipe found. Please try again.")

