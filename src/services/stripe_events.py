from collections.abc import Coroutine
from typing import Any, Callable

import stripe

from services.payment_webhook_service import PaymentWebhookService


class StripeEventType:
    CHECKOUT_SESSION_COMPLETED = "checkout.session.completed"
    CHECKOUT_SESSION_EXPIRED = "checkout.session.expired"
    PAYMENT_INTENT_SUCCEEDED = "payment_intent.succeeded"
    PAYMENT_INTENT_FAILED = "payment_intent.payment_failed"
    REFUND_CREATED = "refund.created"
    CHARGE_REFUNDED = "charge.refunded"


async def handle_checkout_session_completed(event_data: dict, webhook_service: PaymentWebhookService) -> None:
    session_id = event_data["id"]
    payment_intent = event_data["payment_intent"]
    await webhook_service.handle_successful_session(session_id=session_id, payment_intent=payment_intent)


async def handle_checkout_session_expired(event_data: dict, webhook_service: PaymentWebhookService) -> None:
    session_id = event_data["id"]
    await webhook_service.handle_expired_session(session_id)


async def handle_payment_intent_succeeded(event_data: dict, webhook_service: PaymentWebhookService) -> None:
    external_payment_id = event_data["id"]
    await webhook_service.handle_successful_payment(external_payment_id)


async def handle_payment_intent_payment_failed(event_data: dict, webhook_service: PaymentWebhookService) -> None:
    external_payment_id = event_data["id"]
    await webhook_service.handle_failed_payment(external_payment_id)


async def handle_charge_refunded(event_data: dict, webhook_service: PaymentWebhookService) -> None:
    charge_id = event_data["id"]
    charge = stripe.Charge.retrieve(charge_id)
    external_payment_id = charge.payment_intent
    await webhook_service.handle_refunded_payment(external_payment_id)


async def handle_refund_created(event_data: dict, webhook_service: PaymentWebhookService) -> None:
    external_payment_id = event_data["payment_intent"]
    await webhook_service.handle_refunded_payment(external_payment_id)


STRIPE_EVENT_HANDLERS: dict[str, Callable[[dict, PaymentWebhookService], Coroutine[Any, Any, None]]] = {
    StripeEventType.CHECKOUT_SESSION_COMPLETED: handle_checkout_session_completed,
    StripeEventType.CHECKOUT_SESSION_EXPIRED: handle_checkout_session_expired,
    StripeEventType.PAYMENT_INTENT_SUCCEEDED: handle_payment_intent_succeeded,
    StripeEventType.PAYMENT_INTENT_FAILED: handle_payment_intent_payment_failed,
    StripeEventType.CHARGE_REFUNDED: handle_charge_refunded,
    StripeEventType.REFUND_CREATED: handle_refund_created,
}
