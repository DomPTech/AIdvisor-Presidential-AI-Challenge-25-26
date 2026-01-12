from altair.vegalite.v6.theme import theme
from gdeltdoc import GdeltDoc, Filters
import pandas as pd

def build_query_filter(bundle):
    state = bundle.get('state', "Unknown")
    cities = bundle.get('cities', [])
    
    # 1. Clean up Location Keywords
    # We remove commas and ensure terms are wrapped in quotes if they have spaces
    location_keywords = []
    if state != "Unknown":
        for city in cities[:2]:
            # Create a clean "City State" string (e.g., "Nashville Tennessee")
            # GDELT prefers spaces over commas for geographic proximity
            location_keywords.append(f'"{city} {state}"')
        
        # Add the state-level disaster declaration as a single phrase
        location_keywords.append(f'"{state} disaster declaration"')

    # 2. Use GDELT Themes
    # These must be the specific GGK Theme strings
    disaster_themes = [
        "NATURAL_DISASTER", 
        "SIT_WILDFIRE", 
        "SIT_FLOOD", 
        "SIT_EXTREMEWEATHER"
    ]

    # 3. Create Filter
    # keyword=[...] will result in (Keyword1 OR Keyword2 OR Keyword3)
    f = Filters(
        keyword = location_keywords,
        theme = disaster_themes,
        timespan = "24h",
        num_records = 75,
        country = "US"
    )
    return f

def test_bundles_lookup_real():
    # Example: Nashville, TN Bundle
    # bundle = {
    #     "h3_index": "86264d5b7ffffff",
    #     "cities": ["Nashville"],
    #     "counties": ["Davidson County"],
    #     "state": "Tennessee"
    # }
        
    # # Build
    # filters = build_query_filter(bundle)
    # print(f"Querying GDELT for: {bundle['cities'][0]}, {bundle['state']}")
    
    # Execute
    gd = GdeltDoc()

    # Search for articles matching the filters
    # results = gd.article_search(filters)
    
    # print(results)
    # if not results:
    #     print("No matches found in the last 24h.")
    # else:
    #     print(f"Found {len(results)} relevant articles.")
    #     for art in results[:3]: # Show top 3
    #         print(f"- {art['title']} ({art['sourcecountry']})")
    #         print(f"  URL: {art['url']}")

    f = Filters(
        keyword = 'Los Angeles natural disaster',
        # theme="NATURAL_DISASTER",
        timespan = "3w",
        country="US",
        num_records = 1,
    )

    gd = GdeltDoc()

    # Search for articles matching the filters
    articles = gd.article_search(f)
    if articles.empty:
        print("No articles found")
        return
    first_title = articles.iloc[0]['title']
    print(first_title)

if __name__ == "__main__":
    test_bundles_lookup_real()