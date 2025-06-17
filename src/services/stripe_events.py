from decimal import Decimal
from typing import Any, Callable

import stripe

from database.models.payments import PaymentStatus


class StripeEventType:
    CHECKOUT_SESSION_COMPLETED = "checkout.session.completed"
    CHECKOUT_SESSION_EXPIRED = "checkout.session.expired"
    PAYMENT_INTENT_SUCCEEDED = "payment_intent.succeeded"
    PAYMENT_INTENT_FAILED = "payment_intent.payment_failed"
    REFUND_CREATED = "refund.created"
    CHARGE_REFUNDED = "charge.refunded"


def handle_checkout_session_completed(event_data: dict[str, Any]) -> dict[str, Any]:
    session = event_data["object"]
    return {
        "external_payment_id": session.id,
        "status": PaymentStatus.SUCCESSFUL,
        "amount": Decimal(session.amount_total) / 100,
        "order_id": session.metadata.get("order_id"),
        "session_id": session.id,
        "payment_id": session.payment_intent,
        "event_type": event_data.get("type")
    }


def handle_checkout_session_expired(event_data: dict[str, Any]) -> dict[str, Any]:
    session = event_data["object"]
    return {
        "external_payment_id": session.id,
        "status": PaymentStatus.CANCELED,
        "amount": Decimal(session.amount_total) / 100,
        "order_id": session.metadata.get("order_id"),
        "session_id": session.id,
        "payment_id": session.payment_intent,
        "event_type": event_data.get("type")
    }


def handle_payment_intent_succeeded(event_data: dict[str, Any]) -> dict[str, Any]:
    payment_intent = event_data["object"]
    session = stripe.checkout.Session.list(
        payment_intent=payment_intent.id,
        limit=1
    ).data[0]
    return {
        "external_payment_id": session.id,
        "status": PaymentStatus.SUCCESSFUL,
        "amount": Decimal(payment_intent.amount) / 100,
        "order_id": payment_intent.metadata.get("order_id"),
        "payment_id": payment_intent.id,
        "session_id": session.id,
        "event_type": event_data.get("type")
    }


def handle_payment_intent_failed(event_data: dict[str, Any]) -> dict[str, Any]:
    payment_intent = event_data["object"]
    session = stripe.checkout.Session.list(
        payment_intent=payment_intent.id,
        limit=1
    ).data[0]
    return {
        "external_payment_id": session.id,
        "status": PaymentStatus.CANCELED,
        "amount": Decimal(payment_intent.amount) / 100,
        "order_id": payment_intent.metadata.get("order_id"),
        "payment_id": payment_intent.id,
        "session_id": session.id,
        "event_type": event_data.get("type")
    }


def handle_charge_refunded(event_data: dict[str, Any]) -> dict[str, Any]:
    charge = event_data["object"]
    session = stripe.checkout.Session.list(
        payment_intent=charge.payment_intent,
        limit=1
    ).data[0]
    return {
        "external_payment_id": session.id,
        "status": PaymentStatus.REFUNDED,
        "amount": Decimal(charge.amount) / 100,
        "order_id": charge.metadata.get("order_id"),
        "payment_id": charge.payment_intent,
        "session_id": session.id,
        "event_type": event_data.get("type")
    }


def handle_refund_created(event_data: dict[str, Any]) -> dict[str, Any]:
    refund = event_data["object"]
    charge = stripe.Charge.retrieve(refund.charge)
    session = stripe.checkout.Session.list(
        payment_intent=charge.payment_intent,
        limit=1
    ).data[0]
    return {
        "external_payment_id": session.id,
        "status": PaymentStatus.REFUNDED,
        "amount": Decimal(refund.amount) / 100,
        "order_id": charge.metadata.get("order_id"),
        "payment_id": charge.payment_intent,
        "session_id": session.id,
        "event_type": event_data.get("type")
    }


STRIPE_EVENT_HANDLERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    StripeEventType.CHECKOUT_SESSION_COMPLETED: handle_checkout_session_completed,
    StripeEventType.CHECKOUT_SESSION_EXPIRED: handle_checkout_session_expired,
    StripeEventType.PAYMENT_INTENT_SUCCEEDED: handle_payment_intent_succeeded,
    StripeEventType.PAYMENT_INTENT_FAILED: handle_payment_intent_failed,
    StripeEventType.CHARGE_REFUNDED: handle_charge_refunded,
    StripeEventType.REFUND_CREATED: handle_refund_created,
}
