# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import timezone
from typing import Optional
from pymongo import MongoClient
from datetime import datetime, timedelta
from jwt import encode, decode, PyJWTError
from cryptography.hazmat.primitives import serialization
from passlib.context import CryptContext

from app.conf import mongo_string, config


ALGORITHM = config["ALGORITHM"]
ACCESS_TOKEN_EXPIRE_MINUTES = timedelta(minutes=int(config["TIMEDELTA"]))

private_key = open(config["DASH_PRIVATE"], 'r').read()
SECRET_KEY = serialization.load_ssh_private_key(private_key.encode(), password=b'')

public_key = open(config["DASH_PUBLIC"], 'r').read()
PUBLIC_KEY = serialization.load_ssh_public_key(public_key.encode())

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(username, password):
    client = MongoClient(mongo_string)
    db = client["settings"]
    collection = db["users"]
    user = collection.find_one({"username": username}, projection={"_id": False})
    if user and verify_password(password, user["password"]):
        return user["username"], user["scopes"]
    else:
        return None, []


def create_access_token(data: dict,
                        expires_delta: Optional[timedelta] = ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode = data.copy()
    client = MongoClient(mongo_string)
    db = client["settings"]
    token = db["token"]
    token.update_one({"username": data["sub"]},
                     {"$set": {"token_date": datetime.now(timezone.utc)}},
                     upsert=True)

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode["exp"] = expire
    return encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def revoke(username):
    client = MongoClient(mongo_string)
    db = client["settings"]
    token = db["token"]
    token.delete_one({"username": username})


def invalidate_token(token):
    payload = decode(token, PUBLIC_KEY, algorithms=[ALGORITHM])
    revoke(payload.get("sub"))


def init_user_token():
    client = MongoClient(mongo_string)
    db = client["settings"]
    token = db["token"]
    token.create_index("token_date", expireAfterSeconds=int(config["TIMEDELTA"]) * 60)
