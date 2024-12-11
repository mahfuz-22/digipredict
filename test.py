from firebase_admin import credentials, auth
import firebase_admin

cred = credentials.Certificate("asthma-adminsdk.json")
d = firebase_admin.initialize_app(cred)

auth.create_user(email="test@test.com", password="test123")