import requests
import json
from datetime import datetime
import base64
from decouple import config

class MpesaClient:
    def __init__(self):
        self.consumer_key = config('MPESA_CONSUMER_KEY', default='')
        self.consumer_secret = config('MPESA_CONSUMER_SECRET', default='')
        self.passkey = config('MPESA_PASSKEY', default='')
        self.shortcode = config('MPESA_SHORTCODE', default='174379')
        self.environment = config('MPESA_ENVIRONMENT', default='sandbox')
        
        if self.environment == 'sandbox':
            self.auth_url = 'https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
            self.stk_push_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
            self.query_url = 'https://sandbox.safaricom.co.ke/mpesa/stkpushquery/v1/query'
            self.callback_url = config('MPESA_CALLBACK_URL', default='https://your-domain.com/payments/mpesa-callback/')
        else:
            self.auth_url = 'https://api.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials'
            self.stk_push_url = 'https://api.safaricom.co.ke/mpesa/stkpush/v1/processrequest'
            self.query_url = 'https://api.safaricom.co.ke/mpesa/stkpushquery/v1/query'
            self.callback_url = config('MPESA_CALLBACK_URL', default='')
    
    def get_access_token(self):
        """Get M-Pesa API access token"""
        try:
            auth = base64.b64encode(f"{self.consumer_key}:{self.consumer_secret}".encode()).decode()
            headers = {'Authorization': f'Basic {auth}'}
            response = requests.get(self.auth_url, headers=headers)
            response.raise_for_status()
            return response.json()['access_token']
        except Exception as e:
            print(f"Error getting access token: {e}")
            return None
    
    def stk_push(self, phone_number, amount, account_reference, transaction_desc):
        """Send STK push to customer's phone"""
        access_token = self.get_access_token()
        if not access_token:
            return {'error': 'Failed to get access token'}
        
        # Format phone number
        phone_number = str(phone_number).strip()
        if phone_number.startswith('0'):
            phone_number = '254' + phone_number[1:]
        elif phone_number.startswith('+'):
            phone_number = phone_number[1:]
        if not phone_number.startswith('254'):
            phone_number = '254' + phone_number
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_str = f"{self.shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode()
        
        payload = {
            'BusinessShortCode': self.shortcode,
            'Password': password,
            'Timestamp': timestamp,
            'TransactionType': 'CustomerPayBillOnline',
            'Amount': int(amount),
            'PartyA': phone_number,
            'PartyB': self.shortcode,
            'PhoneNumber': phone_number,
            'CallBackURL': self.callback_url,
            'AccountReference': account_reference[:12],
            'TransactionDesc': transaction_desc[:13] if transaction_desc else 'Payment'
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(self.stk_push_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error sending STK push: {e}")
            return {'error': str(e)}
    
    def query_status(self, checkout_request_id):
        """Query the status of an STK push transaction"""
        access_token = self.get_access_token()
        if not access_token:
            return {'error': 'Failed to get access token'}
        
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password_str = f"{self.shortcode}{self.passkey}{timestamp}"
        password = base64.b64encode(password_str.encode()).decode()
        
        payload = {
            'BusinessShortCode': self.shortcode,
            'Password': password,
            'Timestamp': timestamp,
            'CheckoutRequestID': checkout_request_id
        }
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            response = requests.post(self.query_url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error querying status: {e}")
            return {'error': str(e)}