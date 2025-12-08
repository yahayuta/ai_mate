import streamlit as st

st.title('Simple Streamlit App')

st.write("This is a simple Streamlit app launched from the main Flask application.")

# add button
if st.button('Say hello'):
    st.write('Hello, Streamlit!')
else:
    st.write('Goodbye')
