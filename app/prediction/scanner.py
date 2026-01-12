import streamlit as st
import re
import torch
from transformers import pipeline
# from app.chatbot.tools.ddg_search import get_news_search
from gdeltdoc import GdeltDoc, Filters

@st.cache_resource
def get_classifier():
    # Using a small, fast zero-shot classification model
    # This is locally instantiated and doesn't need an API key for classification
    return pipeline(
        "zero-shot-classification", 
        model="typeform/distilbert-base-uncased-mnli",
        device=0 if torch.cuda.is_available() else -1
    )

class DisasterScanner:
    def __init__(self):
        self.classifier = get_classifier()
        self.candidate_labels = ["Critical Disaster", "Moderate Warning", "General Information", "Not Disaster Related"]
        self.gd = GdeltDoc()
        
    def get_severity_score(self, text):
        """
        Calculates a severity score (0-10) based on zero-shot classification results.
        """
        result = self.classifier(text, candidate_labels=self.candidate_labels)
        label_to_score = {
            "Critical Disaster": 10,
            "Moderate Warning": 5,
            "General Information": 2,
            "Not Disaster Related": 0
        }
        
        # Weighted average or top label score
        top_label = result['labels'][0]
        top_score = result['scores'][0]
        
        base_score = label_to_score[top_label]
        # Adjust score by confidence
        final_score = base_score * top_score
        
        return round(min(10, final_score), 1)

    def scan_texts(self, texts):
        """
        Scans a list of texts and returns a list of results with severity and coordinates.
        """
        results = []
        for text in texts:
            severity = self.get_severity_score(text)
            
            if severity > 0:
                # We often don't have coordinates in the text, so we return severity and the text
                results.append({
                    "text": text[:200] + "...", 
                    "severity": severity,
                })
        return results

    def scan_bundle_news(self, bundle):
        state = bundle.get('state', "")
        cities = bundle.get('cities', [])[:2]

        city_queries = [f'{city} {state}' for city in cities if city]

        # fallback: if no cities, just search by state
        if not city_queries and state:
            keyword = f'"{state}"'
        else:
            keyword = " OR ".join(city_queries)
        
        keyword = keyword.replace("-", '"f-16"')

        # Build the GDELT Filters object
        filters = Filters(
            keyword =keyword,
            theme = "NATURAL_DISASTER",
            timespan = "3w",
            country = "US",
            num_records = 3
        )

        max_severity = 0
        top_text = "No disaster reports found."
        
        try:
            articles = self.gd.article_search(filters)
            
            if articles.empty:
                print("No articles found")
                return self._empty_response(bundle)

            # Process dataframe
            for _, row in articles.iterrows():
                # Perform your classification logic on row['title']
                result = self.classify_severity(row['title']) 
                
                if result['severity'] > max_severity:
                    max_severity = result['severity']
                    top_text = f"{row['title']} (Source: {row['domain']})"

        except Exception as e:
            print(f"DEBUG: GDELT query string: {filters.query_string}")
            print(f"DEBUG: GDELT scan error: {e}")
            return self._empty_response(bundle)
        
        output = {
            "severity": max_severity,
            "location": ", ".join(bundle.get('cities', ["Unknown"])),
            "text": top_text,
            "cell": bundle.get('h3')
        }
        print("Found output: ", output)
        return output

    def _empty_response(self, bundle):
        return {"severity": 0, "text": "No reports found.", "cell": bundle.get('h3')}

if __name__ == "__main__":
    scanner = DisasterScanner()
    test_texts = [
        "Major flooding reported in Nashville, TN. Severe property damage.",
        "Beautiful sunny day in California."
    ]
    print(scanner.scan_texts(test_texts))
