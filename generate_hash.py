from streamlit_authenticator.utilities.hasher import Hasher

passwords = ["admin123", "analyst123", "viewer123"]

hashed_passwords = Hasher(passwords).generate()

print(hashed_passwords)