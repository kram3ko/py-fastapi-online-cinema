from abc import ABC, abstractmethod


class EmailSenderInterface(ABC):
    @abstractmethod
    def send_activation_email(self, email: str, activation_link: str) -> None:
        """
        Synchronously send an account activation email.

        Args:
            email (str): The recipient's email address.
            activation_link (str): The activation link to include in the email.
        """
        pass

    @abstractmethod
    def send_activation_complete_email(self, email: str, login_link: str) -> None:
        """
        Synchronously send an email confirming that the account has been activated.

        Args:
            email (str): The recipient's email address.
            login_link (str): The login link to include in the email.
        """
        pass

    @abstractmethod
    def send_password_reset_email(self, email: str, reset_link: str) -> None:
        """
        Synchronously send a password reset request email.

        Args:
            email (str): The recipient's email address.
            reset_link (str): The password reset link to include in the email.
        """
        pass

    @abstractmethod
    def send_password_reset_complete_email(self, email: str, login_link: str) -> None:
        """
        Synchronously send an email confirming that the password has been reset.

        Args:
            email (str): The recipient's email address.
            login_link (str): The login link to include in the email.
        """
        pass


class StripeEmailSenderInterface(ABC):
    @abstractmethod
    def send_payment_success_email(self, email: str, payment_details: dict) -> None:
        """
        Send a payment success notification email.

        Args:
            email (str): The recipient's email address.
            payment_details (Dict[str, Any]): The payment details to include in the email.
        """
        pass
