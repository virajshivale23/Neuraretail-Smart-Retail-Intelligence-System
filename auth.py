import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader

# Load configuration
with open("config.yaml") as file:
    config = yaml.load(file, Loader=SafeLoader)

# Create authenticator
authenticator = stauth.Authenticate(
    config["credentials"],
    config["cookie"]["name"],
    config["cookie"]["key"],
    config["cookie"]["expiry_days"],
)

def login():
    name, authentication_status, username = authenticator.login(
        location="main",
        fields={
            "Form name": "Login",
            "Username": "Username",
            "Password": "Password",
            "Login": "Login",
        },
    )
    return name, authentication_status, username, authenticator