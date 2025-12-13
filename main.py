# -*- Product under GNU GPL v3 -*-
# -*- Author: E.Aivayan -*-
import argparse
import atexit
import datetime
import ssl
import tempfile
from os import makedirs, unlink

import uvicorn

# cryptography is required to generate a self-signed certificate on the fly
try:
    from cryptography import x509
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.x509.oid import NameOID
except ImportError as e:
    raise ImportError("Please install the 'cryptography' package for dev HTTPS: pip install cryptography") from e


def generate_self_signed_cert(hostname: str = "localhost") -> tuple[str, str]:
    """
    Generate a self-signed certificate and private key, write them to temporary files,
    and return (cert_path, key_path). Caller is responsible for cleanup (files are
    registered for removal via atexit in this script).
    """
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name(
        [
            x509.NameAttribute(NameOID.COMMON_NAME, hostname),
        ]
    )
    now = datetime.datetime.utcnow()
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - datetime.timedelta(minutes=1))
        .not_valid_after(now + datetime.timedelta(days=365))
        .add_extension(
            x509.SubjectAlternativeName([x509.DNSName(hostname), x509.DNSName("127.0.0.1")]),
            critical=False,
        )
        .sign(key, hashes.SHA256())
    )

    cert_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pem")
    key_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pem")

    cert_file.write(cert.public_bytes(serialization.Encoding.PEM))
    cert_file.flush()
    cert_file.close()

    key_file.write(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    key_file.flush()
    key_file.close()

    return cert_file.name, key_file.name


def build_ssl_context(cert_path: str, key_path: str) -> ssl.SSLContext:
    """
    Create an SSLContext preferring/enforcing the latest TLS version available.
    """
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

    # Prefer TLSv1.3 if available; otherwise let negotiation use the highest supported.
    if hasattr(ssl, "TLSVersion"):
        try:
            context.minimum_version = ssl.TLSVersion.TLSv1_3
        except Exception:
            # Fallback: at least disable old insecure versions if TLSv1_3 not supported
            context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1
    else:
        # Older Python: disable TLS 1.0/1.1 explicitly
        context.options |= ssl.OP_NO_TLSv1 | ssl.OP_NO_TLSv1_1

    context.load_cert_chain(certfile=cert_path, keyfile=key_path)
    return context


if __name__ == "__main__":
    makedirs("app/static", exist_ok=True)

    parser = argparse.ArgumentParser()
    parser.add_argument("--dev-https", action="store_true", help="Run dev server with HTTPS using a self-signed cert")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind")
    parser.add_argument("--port", type=int, default=8081, help="Port to bind")
    args = parser.parse_args()

    ssl_context = None
    temp_files: list[str] = []
    ssl_param = {}
    if args.dev_https:
        cert_path, key_path = generate_self_signed_cert(hostname="localhost")
        temp_files.extend([cert_path, key_path])
        ssl_param = {"ssl_certfile": cert_path, "ssl_keyfile": key_path}
        # Ensure cleanup on exit
        def _cleanup_temp_files():
            for p in temp_files:
                try:
                    unlink(p)
                except Exception:
                    pass

        atexit.register(_cleanup_temp_files)

        ssl_context = build_ssl_context(cert_path, key_path)

    uvicorn.run(
        "app.api:app",
        host=args.host,
        port=args.port,
        reload=True,
        reload_dirs=["app"],
        log_config="log_config.yaml",
        **ssl_param,
    )
