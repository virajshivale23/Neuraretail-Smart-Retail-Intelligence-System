import streamlit as st
import yaml
import bcrypt
from yaml.loader import SafeLoader

with open("config.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

users = config["credentials"]["usernames"]


def verify_password(password, hashed_password):
    return bcrypt.checkpw(
        password.encode(),
        hashed_password.encode()
    )


def login():

    if "authentication_status" not in st.session_state:
        st.session_state.authentication_status = False
        st.session_state.name = None
        st.session_state.username = None

    if not st.session_state.authentication_status:

        st.title("🔐 Login")

        with st.form("login"):

            username = st.text_input("Username")
            password = st.text_input("Password", type="password")

            submit = st.form_submit_button("Login")

            if submit:

                if username in users:

                    user = users[username]

                    if verify_password(password, user["password"]):

                        st.session_state.authentication_status = True
                        st.session_state.name = user["name"]
                        st.session_state.username = username

                        st.rerun()

                    else:
                        st.error("Invalid Password")

                else:
                    st.error("Invalid Username")

    return (
        st.session_state.name,
        st.session_state.authentication_status,
        st.session_state.username,
        None,
    )