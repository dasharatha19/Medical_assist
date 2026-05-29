from supabase import create_client
import os

supabase = create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_ANON_KEY"))

def login(email, password):
    response = supabase.auth.sign_in_with_password({"email": email, "password": password})
    return response.user, response.session.access_token

def signup(email, password):
    response = supabase.auth.sign_up({"email": email, "password": password})
    return response.user