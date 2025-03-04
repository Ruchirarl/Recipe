
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

# If a recipe is found, display the details
if recipe:
    st.subheader(f"Recommended Recipe: {recipe.get('title', 'No title')}")
    
    # Display recipe image if available
    st.image(recipe.get("image", ""), width=400)
    
    # Display preparation time for all recipe types
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
        for nutrient in recipe['nutrition']['nutrients']:
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