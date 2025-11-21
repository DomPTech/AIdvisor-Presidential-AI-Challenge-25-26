import os
import streamlit as st

st.title("Flooding Prevention")
api_key = st.text_input("API key", type="password")
if not api_key:
    st.stop()
os.environ["OPENAI_API_KEY"] = api_key

if "history" not in st.session_state:
    st.session_state.history = []

#agent_runnable = get_agent()
#agent = PymatgenAgentExecutor(agent_runnable)

query = st.text_area("Ask a question or request flooding data/needs")

if st.button("Submit") and query.strip():
    with st.spinner("Working…"):
       # result = agent.invoke(query)
       # answer = result["output"]
        #st.write(answer)
        st.session_state.history += [
            {"role": "user", "content": query},
           # {"role": "assistant", "content": answer}
        ]