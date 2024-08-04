from app.auth.services import get_password_hash

password = "imtiazshawn"
hashed_password = get_password_hash(password)
print('Hashed Password: ', hashed_password);