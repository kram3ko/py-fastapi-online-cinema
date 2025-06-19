import stripe
from fastapi import HTTPException, Request, status

from config import get_settings
from database.models.orders import OrderModel
from database.models.payments import PaymentModel
from schemas.payments import CheckoutSessionResponse
from services.payment_webhook_service import PaymentWebhookService
from services.stripe_events import STRIPE_EVENT_HANDLERS

stripe_settings = get_settings()
stripe.api_key = stripe_settings.STRIPE_SECRET_KEY


class StripeService:
    @staticmethod
    async def create_checkout_session(
        request: Request,
        order: OrderModel
    ) -> CheckoutSessionResponse:
        try:
            line_items = [
                {
                    "price_data": {
                        "currency": stripe_settings.STRIPE_CURRENCY,
                        "product_data": {
                            "name": f"Order #{order.id} - {item.movie.name}",
                            "description": f"Year: {item.movie.year}, IMDB: {item.movie.imdb}",
                            "metadata": {
                                "movie_id": str(item.movie.id),
                                "order_item_id": str(item.id)
                            }
                        },
                        "unit_amount": int(item.price_at_order * 100),
                    },
                    "quantity": 1,
                }
                for item in order.order_items
            ]

            base_url = str(request.base_url)
            success_url = f"{base_url}api/v1/payments/history"
            cancel_url = f"{base_url}api/v1/payments/history"

            session = stripe.checkout.Session.create(
                api_key=stripe_settings.STRIPE_SECRET_KEY,
                payment_method_types=["card"],
                line_items=line_items,
                mode="payment",
                success_url=success_url,
                cancel_url=cancel_url,
                metadata={
                    "order_id": str(order.id),
                    "user_id": str(order.user_id)
                }
            )

            return CheckoutSessionResponse(
                payment_url=session.url,
                payment_id=order.id,
                session_id=session.id
            )
        except stripe.error.StripeError as e:  # type: ignore[attr-defined]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    @staticmethod
    async def get_checkout_session_url(session_id: str) -> str | None:
        session = stripe.checkout.Session.retrieve(session_id)
        return session.url

    @staticmethod
    async def handle_webhook(
        payload: bytes,
        sig_header: str,
        webhook_service: PaymentWebhookService
    ) -> tuple[str, dict]:
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

        handler = STRIPE_EVENT_HANDLERS.get(event.type)
        if not handler:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"No handler for event type: {event.type}"
            )

        await handler(event.data.object, webhook_service)

        event_data = event.data.object
        payment_details = {"payment_id": event_data.id}

        return event.type, payment_details

    @staticmethod
    async def refund_payment(payment: PaymentModel) -> bool:
        try:
            if not payment.session_id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="No external payment ID found"
                )

            payment_intent = payment.session_id
            try:
                session = stripe.checkout.Session.retrieve(payment.session_id)
                if session.payment_intent:
                    payment_intent = session.payment_intent
            except stripe.error.StripeError:  # type: ignore[attr-defined]
                pass

            refund = stripe.Refund.create(
                payment_intent=payment_intent
            )
            return refund.status == "succeeded"

        except stripe.error.StripeError as e:  # type: ignore[attr-defined]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
