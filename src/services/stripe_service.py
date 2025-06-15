from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

import stripe
from fastapi import HTTPException, status, Request

from config import get_settings
from database.models.payments import PaymentModel, PaymentStatus
from schemas.payments import PaymentCreateSchema

stripe_settings = get_settings()

class StripeService:
    @staticmethod
    async def create_payment_intent(payment_data: PaymentCreateSchema, request: Request) -> dict:
        try:
            amount_cents = int(payment_data.amount * 100)
            
            # Get base URL from request
            base_url = request.base_url
            success_url = f"{base_url}api/v1/payments/success/?session_id={{CHECKOUT_SESSION_ID}}"
            cancel_url = f"{base_url}api/v1/payments/cancel/?session_id={{CHECKOUT_SESSION_ID}}"

            session = stripe.checkout.Session.create(
                api_key=stripe_settings.STRIPE_SECRET_KEY,
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
                success_url=success_url,
                cancel_url=cancel_url,
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
                    api_key=stripe_settings.STRIPE_SECRET_KEY,
                    payment_intent=payment.external_payment_id
                )
                return refund.status == "succeeded"
            except stripe.error.StripeError:  # type: ignore[attr-defined]
                session = stripe.checkout.Session.retrieve(
                    payment.external_payment_id,
                    api_key=stripe_settings.STRIPE_SECRET_KEY
                )
                if not session.payment_intent:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="No payment intent found for this session"
                    )

                refund = stripe.Refund.create(
                    api_key=stripe_settings.STRIPE_SECRET_KEY,
                    payment_intent=session.payment_intent
                )
                return refund.status == "succeeded"

        except stripe.error.StripeError as e:  # type: ignore[attr-defined]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
