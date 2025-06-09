from decimal import Decimal
from typing import Optional

import stripe
from fastapi import HTTPException, status

from config import get_settings
from database.models.payments import PaymentModel, PaymentStatus
from schemas.payments import PaymentCreateSchema

stripe_settings = get_settings()
stripe.api_key = stripe_settings.STRIPE_SECRET_KEY


class StripeService:
    @staticmethod
    async def create_payment_intent(payment_data: PaymentCreateSchema) -> dict:
        try:
            amount_cents = int(payment_data.amount * 100)

            intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=stripe_settings.STRIPE_CURRENCY,
                metadata={
                    "order_id": payment_data.order_id,
                }
            )

            return {
                "client_secret": intent.client_secret,
                "payment_intent_id": intent.id
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

        if event.type == "payment_intent.succeeded":
            payment_intent = event.data.object
            return {
                "external_payment_id": payment_intent.id,
                "status": PaymentStatus.SUCCESSFUL,
                "amount": Decimal(payment_intent.amount) / 100,
                "order_id": payment_intent.metadata.get("order_id")
            }
        elif event.type == "payment_intent.payment_failed":
            payment_intent = event.data.object
            return {
                "external_payment_id": payment_intent.id,
                "status": PaymentStatus.CANCELED,
                "amount": Decimal(payment_intent.amount) / 100,
                "order_id": payment_intent.metadata.get("order_id")
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

            refund = stripe.Refund.create(
                payment_intent=payment.external_payment_id
            )

            return refund.status == "succeeded"
        except stripe.error.StripeError as e:  # type: ignore[attr-defined]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
