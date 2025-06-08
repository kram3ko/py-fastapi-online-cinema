from abc import ABC, abstractmethod
from typing import Dict, Any


class StripeEmailSenderInterface(ABC):
    @abstractmethod
    def send_payment_success_email(self, email: str, payment_details: Dict[str, Any]) -> None:
        """
        Send a payment success notification email.

        Args:
            email (str): The recipient's email address.
            payment_details (Dict[str, Any]): The payment details to include in the email.
        """
        pass 