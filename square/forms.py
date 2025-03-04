from django import forms


class PaymentForm(forms.Form):
    email = forms.EmailField(label="Email Address", required=True)
