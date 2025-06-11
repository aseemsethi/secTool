import streamlit as st

@st.fragment(run_every=None)
def webui_func(qa_chain):
    st.write("This is inside of a fragment!")
    st.title("CVE Check")
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    st.caption("A Streamlit powered chatbot powered by Ollama")
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]
    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])
    if prompt := st.chat_input("What is the code written in"):
        print("..............")
        answer = qa_chain.invoke(prompt)
        #print(f"Answer: {answer}")
        st.chat_message("assistant").write(answer)