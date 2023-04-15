# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
from datetime import timedelta

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from passlib.context import CryptContext

from app import conf
from app.conf import config

ACCESS_TOKEN_EXPIRE_MINUTES = timedelta(minutes=int(config["TIMEDELTA"]))
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password):
    return pwd_context.hash(password)


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
