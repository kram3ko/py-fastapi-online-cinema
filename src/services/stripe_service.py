from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

import stripe
from fastapi import HTTPException, status

from config import get_settings
from database.models.payments import PaymentModel, PaymentStatus
from schemas.payments import PaymentCreateSchema

stripe_settings = get_settings()
stripe.api_key = stripe_settings.STRIPE_SECRET_KEY

SUCCESS_URL = f"{stripe_settings.FRONTEND_URL}:8000/api/v1/payments/success/?session_id={{CHECKOUT_SESSION_ID}}"
CANCEL_URL = f"{stripe_settings.FRONTEND_URL}:8000/api/v1/payments/cancel/?session_id={{CHECKOUT_SESSION_ID}}"


class StripeService:
    @staticmethod
    async def create_payment_intent(payment_data: PaymentCreateSchema) -> dict:
        try:
            amount_cents = int(payment_data.amount * 100)

            session = stripe.checkout.Session.create(
                payment_method_types=["card"],
                line_items=[{
                    "price_data": {
                        "currency": stripe_settings.STRIPE_CURRENCY,
                        "product_data": {
                            "name": f"Order #{payment_data.order_id}",
                        },
                        "unit_amount": amount_cents,
                    },
                    "quantity": 1,
                }],
                mode="payment",
                success_url=SUCCESS_URL,
                cancel_url=CANCEL_URL,
                metadata={
                    "order_id": payment_data.order_id,
                },
                expires_at=int((datetime.now() + timedelta(minutes=30)).timestamp())
            )

            return {
                "payment_url": session.url,
                "payment_intent_id": session.payment_intent if session.payment_intent else session.id
            }
        except stripe.error.StripeError as e:  # type: ignore[attr-defined]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    @staticmethod
    async def handle_webhook(payload: bytes, sig_header: str) -> Optional[dict]:
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, stripe_settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid payload"
            )
        except stripe.error.SignatureVerificationError:  # type: ignore[attr-defined]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid signature"
            )

        if event.type == "checkout.session.completed":
            session = event.data.object
            return {
                "external_payment_id": session.id,
                "status": PaymentStatus.SUCCESSFUL,
                "amount": Decimal(session.amount_total) / 100,
                "order_id": session.metadata.get("order_id")
            }
        elif event.type == "checkout.session.expired":
            session = event.data.object
            return {
                "external_payment_id": session.id,
                "status": PaymentStatus.CANCELED,
                "amount": Decimal(session.amount_total) / 100,
                "order_id": session.metadata.get("order_id")
            }

        return None

    @staticmethod
    async def refund_payment(payment: PaymentModel) -> bool:
        try:
            if not payment.external_payment_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No external payment ID found"
                )

            try:

                refund = stripe.Refund.create(
                    payment_intent=payment.external_payment_id
                )
                return refund.status == "succeeded"
            except stripe.error.StripeError:  # type: ignore[attr-defined]

                session = stripe.checkout.Session.retrieve(payment.external_payment_id)
                if not session.payment_intent:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No payment intent found for this session"
                    )

                refund = stripe.Refund.create(
                    payment_intent=session.payment_intent
                )
                return refund.status == "succeeded"

        except stripe.error.StripeError as e:  # type: ignore[attr-defined]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
