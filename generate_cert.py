from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import datetime
import os

# Create the certs directory if it doesn't exist
if not os.path.exists("certs"):
    os.makedirs("certs")

# 1. Generate the Private Key (privkey.pem)
key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)

# 2. Generate the Public Certificate (fullchain.pem)
subject = issuer = x509.Name([
    x509.NameAttribute(NameOID.COUNTRY_NAME, u"VN"),
    x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, u"HoChiMinh"),
    x509.NameAttribute(NameOID.ORGANIZATION_NAME, u"MedicalASR"),
    x509.NameAttribute(NameOID.COMMON_NAME, u"localhost"),
])

cert = x509.CertificateBuilder().subject_name(
    subject
).issuer_name(
    issuer
).public_key(
    key.public_key()
).serial_number(
    x509.random_serial_number()
).not_valid_before(
    datetime.datetime.utcnow()
).not_valid_after(
    # Valid for 1 year
    datetime.datetime.utcnow() + datetime.timedelta(days=365)
).add_extension(
    x509.BasicConstraints(ca=True, path_length=None), critical=True,
).sign(key, hashes.SHA256())

# 3. Write files to disk
with open("certs/privkey.pem", "wb") as f:
    f.write(key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ))

with open("certs/fullchain.pem", "wb") as f:
    f.write(cert.public_bytes(encoding=serialization.Encoding.PEM))

print("✅ SUCCESS! Created certs/privkey.pem and certs/fullchain.pem")