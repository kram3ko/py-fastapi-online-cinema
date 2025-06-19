from notifications.base_notificator import BaseEmailNotificator
from notifications.interfaces import EmailSenderInterface


class EmailSender(BaseEmailNotificator, EmailSenderInterface):
    def send_activation_email(self, email: str, activation_link: str) -> None:
        """
        Send an account activation email.

        Args:
            email (str): The recipient's email address.
            activation_link (str): The activation link to be included in the email.
        """
        template = self._env.get_template(self._activation_email_template_name)
        html_content = template.render(email=email, activation_link=activation_link)
        subject = "Account Activation"
        self._send_email(email, subject, html_content)

    def send_activation_complete_email(self, email: str, login_link: str) -> None:
        """
        Send an account activation completion email.

        Args:
            email (str): The recipient's email address.
            login_link (str): The login link to be included in the email.
        """
        template = self._env.get_template(self._activation_complete_email_template_name)
        html_content = template.render(email=email, login_link=login_link)
        subject = "Account Activated Successfully"
        self._send_email(email, subject, html_content)

    def send_password_reset_email(self, email: str, reset_link: str) -> None:
        """
        Send a password reset request email.

        Args:
            email (str): The recipient's email address.
            reset_link (str): The reset link to be included in the email.
        """
        template = self._env.get_template(self._password_email_template_name)
        html_content = template.render(email=email, reset_link=reset_link)
        subject = "Password Reset Request"
        self._send_email(email, subject, html_content)

    def send_password_reset_complete_email(self, email: str, login_link: str) -> None:
        """
        Send a password reset completion email.

        Args:
            email (str): The recipient's email address.
            login_link (str): The login link to be included in the email.
        """
        template = self._env.get_template(self._password_complete_email_template_name)
        html_content = template.render(email=email, login_link=login_link)
        subject = "Your Password Has Been Successfully Reset"
        self._send_email(email, subject, html_content)
