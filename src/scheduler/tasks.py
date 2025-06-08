import logging
from datetime import datetime, timezone

from sqlalchemy import delete
from sqlalchemy.exc import SQLAlchemyError

from config import get_settings
from config.dependencies import get_accounts_email_notificator, get_stripe_email_notificator
from database.deps import get_sync_db_contextmanager
from database.models.accounts import ActivationTokenModel
from scheduler.celery_app import celery_app

logger = logging.getLogger(__name__)

settings = get_settings()


@celery_app.task
def delete_expired_activation_tokens() -> int | None:
    with get_sync_db_contextmanager() as db:
        try:
            stmt = delete(ActivationTokenModel).where(ActivationTokenModel.expires_at < datetime.now(timezone.utc))
            result = db.execute(stmt)
            db.commit()
            logger.info(f"Deleted tokens: {result.rowcount}")
            return result.rowcount
        except SQLAlchemyError as e:
            db.rollback()
            logger.error(f"Error deleting tokens: {e}")
    return None


@celery_app.task(name="send_activation_email")
def send_activation_email_task(email: str, activation_link: str) -> None:
    """Send activation email."""
    try:
        email_sender = get_accounts_email_notificator(settings)
        email_sender.send_activation_email(email, activation_link)
        logger.info(f"Activation email sent to {email}")
    except Exception as e:
        logger.error(f"Error sending activation email to {email}: {e}")


@celery_app.task(name="send_activation_complete_email")
def send_activation_complete_email_task(email: str, login_link: str) -> None:
    """Send activation complete email."""
    try:
        email_sender = get_accounts_email_notificator(settings)
        email_sender.send_activation_complete_email(email, login_link)
        logger.info(f"Activation complete email sent to {email}")
    except Exception as e:
        logger.error(f"Error sending activation complete email to {email}: {e}")


@celery_app.task(name="send_password_reset_email")
def send_password_reset_email_task(email: str, reset_link: str) -> None:
    """Send password reset email."""
    try:
        email_sender = get_accounts_email_notificator(settings)
        email_sender.send_password_reset_email(email, reset_link)
        logger.info(f"Password reset email sent to {email}")
    except Exception as e:
        logger.error(f"Error sending password reset email to {email}: {e}")


@celery_app.task(name="send_password_reset_complete_email")
def send_password_reset_complete_email_task(email: str, login_link: str) -> None:
    """Send password reset complete email."""
    try:
        email_sender = get_accounts_email_notificator(settings)
        email_sender.send_password_reset_complete_email(email, login_link)
        logger.info(f"Password reset complete email sent to {email}")
    except Exception as e:
        logger.error(f"Error sending password reset complete email to {email}: {e}")

@celery_app.task(name="send_stripe_payment_success_email")
def send_stripe_payment_success_email_task(email: str, payment_details: dict) -> None:
    """Send Stripe payment success email."""
    try:
        email_sender = get_stripe_email_notificator(settings)
        email_sender.send_payment_success_email(email, payment_details)
        logger.info(f"Stripe payment success email sent to {email}")
    except Exception as e:
        logger.error(f"Error sending Stripe payment success email to {email}: {e}")