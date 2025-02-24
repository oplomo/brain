# paystack.py
import requests
from django.conf import settings

PAYSTACK_SECRET_KEY = settings.PAYSTACK_SECRET_KEY
PAYSTACK_BASE_URL = 'https://api.paystack.co'


def initiate_payment(email, amount, reference):
    """Initialize a Paystack payment"""
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "email": email,
        "amount": int(amount) * 100,  # Paystack works in kobo, multiply by 100
        "reference": reference,
        "callback_url": settings.PAYSTACK_CALLBACK_URL,
    }
    response = requests.post(f"{PAYSTACK_BASE_URL}/transaction/initialize", json=data, headers=headers)
    return response.json()


def verify_payment(reference):
    """Verify a Paystack payment using the reference"""
    headers = {
        "Authorization": f"Bearer {PAYSTACK_SECRET_KEY}",
    }
    url = f"{PAYSTACK_BASE_URL}/transaction/verify/{reference}"
    response = requests.get(url, headers=headers)
    return response.json()
