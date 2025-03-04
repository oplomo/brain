from django import forms


class PaymentForm(forms.Form):
    email = forms.EmailField(label="Email Address", required=True)
    amount = forms.DecimalField(
        label="Amount (₦)", min_value=100, max_value=1000000, required=True
    )
    # Add other fields if needed (e.g., name, phone number)
