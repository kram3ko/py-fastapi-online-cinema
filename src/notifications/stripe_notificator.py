from typing import Any

from notifications.base_notificator import BaseEmailNotificator
from notifications.stripe_interfaces import StripeEmailSenderInterface


class StripeEmailNotificator(BaseEmailNotificator, StripeEmailSenderInterface):
    def send_payment_success_email(self, email: str, payment_details: dict[str, Any]) -> None:
        """
        Send a payment success notification email.

        Args:
            email (str): The recipient's email address.
            payment_details (Dict[str, Any]): The payment details to include in the email.
        """
        subject = "Payment Successful"
        template = self._env.get_template("payment_success.html")
        html_content = template.render(payment_details=payment_details)
        self._send_email(email, subject, html_content)
