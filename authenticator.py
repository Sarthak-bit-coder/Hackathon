import pyotp
import qrcode

# Dictionary of admins with their TOTP secrets
admins = {
    "Sarthak": "JBSWY3DPEHPK3PXP",
    "Ayesha": "KZXW6YTBMFWWKZLU",
    "Shubham": "MFRGGZDFMZTWQ2LK",
    "Anav": "ONSWG4TFOQYTEMY=",
}

# Generate and save QR codes for each admin
for email, secret in admins.items():
    totp = pyotp.TOTP(secret)
    uri = totp.provisioning_uri(name=email, issuer_name="Neighborhood Watch")

    # Create QR code image
    img = qrcode.make(uri)

    # Save to a file
    filename = f"{email.replace('@', '_at_')}.png"
    img.save(filename)
    print(f"Saved QR code for {email} as {filename}")

    # Optional: Show the QR code
    img.show()