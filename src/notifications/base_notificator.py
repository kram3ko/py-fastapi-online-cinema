import logging
import smtplib
from abc import ABC
from dataclasses import field, dataclass
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from jinja2 import Environment, FileSystemLoader

from exceptions import BaseEmailError


@dataclass
class BaseEmailNotificator(ABC):
    _hostname: str
    _port: int
    _email: str
    _password: str
    _use_tls: bool
    _template_dir: str
    _env: Environment = field(init=False, repr=False)

    def __post_init__(self):
        self._env = Environment(loader=FileSystemLoader(self._template_dir))

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
