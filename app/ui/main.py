import streamlit as st

def main():
    st.set_page_config(page_title="Disaster Prediction & Coordination", layout="wide")
    st.title("Disaster Prediction & Volunteering Coordination Portal")
    
    st.sidebar.title("Navigation")
    app_mode = st.sidebar.selectbox("Choose the app mode",
        ["Home", "Chatbot", "Prediction", "Volunteering"])

    if app_mode == "Home":
        st.write("Welcome to the portal.")
    elif app_mode == "Chatbot":
        st.write("Chatbot interface will go here.")
    elif app_mode == "Prediction":
        st.write("Prediction tools will go here.")
    elif app_mode == "Volunteering":
        st.write("Volunteering coordination will go here.")

if __name__ == "__main__":
    main()
