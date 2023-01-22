# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import logging
from datetime import timezone
from typing import Optional
from pymongo import MongoClient
from datetime import datetime, timedelta
from jwt import encode, decode
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend
from passlib.context import CryptContext

from app.conf import mongo_string, config
from app import conf


ACCESS_TOKEN_EXPIRE_MINUTES = timedelta(minutes=int(config["TIMEDELTA"]))
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


def authenticate_user(username, password):
    try:
        client = MongoClient(mongo_string)
        db = client["settings"]
        collection = db["users"]
        user = collection.find_one({"username": username}, projection={"_id": False})
        if user and verify_password(password, user["password"]):
            return user["username"], user["scopes"]
        else:
            return None, []
    except Exception as exception:
        log = logging.getLogger("uvicorn.access")
        log.warning(msg=" ".join(exception.args))
        return None, []

def create_access_token(data: dict,
                        expires_delta: Optional[timedelta] = ACCESS_TOKEN_EXPIRE_MINUTES):
    to_encode = data.copy()
    client = MongoClient(mongo_string)
    db = client["settings"]
    token = db["token"]
    if token.count_documents({}) == 0:
        generate_keys()
    token.update_one({"username": data["sub"]},
                     {"$set": {"token_date": datetime.now(timezone.utc)}},
                     upsert=True)

    return encode(to_encode, conf.SECRET_KEY, algorithm=conf.ALGORITHM)


def renew(user):
    client = MongoClient(mongo_string)
    db = client["settings"]
    token = db["token"]
    token.update_one({"username": user},
                     {"$set": {"token_date": datetime.now(timezone.utc)}},
                     upsert=True)


def revoke(username):
    client = MongoClient(mongo_string)
    db = client["settings"]
    token = db["token"]
    token.delete_one({"username": username})


def invalidate_token(token):
    payload = decode(token, conf.PUBLIC_KEY, algorithms=[conf.ALGORITHM])
    revoke(payload.get("sub"))


def generate_keys():
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    private_pem = private_key.private_bytes(encoding=serialization.Encoding.PEM,
                                            format=serialization.PrivateFormat.TraditionalOpenSSL,
                                            encryption_algorithm=serialization.NoEncryption())
    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    conf.SECRET_KEY = serialization.load_pem_private_key(private_pem,
                                                     password=None,
                                                     backend=default_backend())
    conf.PUBLIC_KEY = serialization.load_pem_public_key(public_pem,
                                                   backend=default_backend())
    conf.ALGORITHM = "RS256"


def init_user_token():
    client = MongoClient(mongo_string)
    db = client["settings"]
    token = db["token"]
    token.create_index("token_date", expireAfterSeconds=int(config["TIMEDELTA"]) * 60)
    generate_keys()
