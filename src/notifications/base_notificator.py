import logging
import smtplib
from abc import ABC
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Environment, FileSystemLoader

from exceptions import BaseEmailError


class BaseEmailNotificator(ABC):
    def __init__(
        self,
        hostname: str,
        port: int,
        email: str,
        password: str,
        use_tls: bool,
        template_dir: str,
        activation_email_template_name: str,
        activation_complete_email_template_name: str,
        password_email_template_name: str,
        password_complete_email_template_name: str,
    ):
        self._hostname = hostname
        self._port = port
        self._email = email
        self._password = password
        self._use_tls = use_tls
        self._activation_email_template_name = activation_email_template_name
        self._activation_complete_email_template_name = activation_complete_email_template_name
        self._password_email_template_name = password_email_template_name
        self._password_complete_email_template_name = password_complete_email_template_name

        self._env = Environment(loader=FileSystemLoader(template_dir))

    def _send_email(self, recipient: str, subject: str, html_content: str) -> None:
        """
        Send an email with the given subject and HTML content.

        Args:
            recipient (str): The recipient's email address.
            subject (str): The subject of the email.
            html_content (str): The HTML content of the email.

        Raises:
            BaseEmailError: If sending the email fails.
        """
        message = MIMEMultipart()
        message["From"] = self._email
        message["To"] = recipient
        message["Subject"] = subject
        message.attach(MIMEText(html_content, "html"))

        try:
            with smtplib.SMTP(self._hostname, self._port) as smtp:
                if self._use_tls:
                    smtp.starttls()
                smtp.login(self._email, self._password)
                smtp.sendmail(self._email, [recipient], message.as_string())
        except smtplib.SMTPException as error:
            logging.error(f"Failed to send email to {recipient}: {error}")
            raise BaseEmailError(f"Failed to send email to {recipient}: {error}")
