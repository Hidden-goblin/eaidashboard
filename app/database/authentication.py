# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from typing import Optional
from dotenv import dotenv_values
from pymongo import MongoClient
from datetime import datetime, timedelta
from jwt import encode, decode, PyJWTError
from cryptography.hazmat.primitives import serialization
from passlib.context import CryptContext

from app.conf import mongo_string

config = dotenv_values(".env")

ALGORITHM = config["ALGORITHM"]
ACCESS_TOKEN_EXPIRE_MINUTES = timedelta(minutes=int(config["TIMEDELTA"]))

private_key = open(config["PRIVATE"], 'r').read()
SECRET_KEY = serialization.load_ssh_private_key(private_key.encode(), password=b'')

public_key = open(config["PUBLIC"], 'r').read()
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
    if not user:
        return None, []
    if not verify_password(password, user["password"]):
        return None, []
    return user["username"], user["scopes"]


def create_access_token(data: dict,
                        expires_delta: Optional[timedelta] = ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode["exp"] = expire
    return encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

