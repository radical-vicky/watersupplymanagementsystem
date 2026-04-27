from allauth.account.adapter import DefaultAccountAdapter
from django.urls import reverse

class CustomAccountAdapter(DefaultAccountAdapter):
    def get_email_confirmation_url(self, request, emailconfirmation):
        """Override to fix URL encoding issues"""
        url = reverse(
            "account_confirm_email",
            args=[emailconfirmation.key],
        )
        return request.build_absolute_uri(url)
    
    def get_password_reset_url(self, request, user):
        """Override to fix password reset URL encoding"""
        from allauth.account.utils import url_str_to_user_pk
        
        temp_key = self.generate_temp_key(user)
        url = reverse(
            "account_reset_password_from_key",
            kwargs={"uidb36": url_str_to_user_pk(user), "key": temp_key},
        )
        return request.build_absolute_uri(url)