import logging

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.deps import get_db_contextmanager
from database.models.orders import OrderModel, OrderStatus
from database.models.payments import PaymentModel, PaymentStatus
from scheduler.tasks import send_stripe_payment_success_email_task

logger = logging.getLogger(__name__)


class PaymentWebhookService:
    """Service for handling payment webhooks and updating payment/order statuses."""

    @staticmethod
    async def _get_payment_by_session_id_payment_id(payment_id: str, db: AsyncSession) -> PaymentModel:
        payment = await db.scalar(
            select(PaymentModel).where(
                (PaymentModel.session_id == payment_id) |
                (PaymentModel.payment_intent_id == payment_id)
            )
        )
        if not payment:
            logger.error(f"Payment not found for session_id={payment_id}")
            raise ValueError("Payment not found")
        return payment

    @staticmethod
    async def _get_order(order_id: int, db: AsyncSession) -> OrderModel | type[OrderModel]:
        order = await db.get(OrderModel, order_id)
        if not order:
            logger.error(f"Order not found for order_id={order_id}")
            raise ValueError("Order not found")
        return order

    async def handle_successful_session(self, session_id: str, payment_intent_id: str) -> None:
        """Handle successful session payment."""
        async with get_db_contextmanager() as db:
            try:
                payment = await self._get_payment_by_session_id_payment_id(session_id, db)
                payment.payment_intent_id = payment_intent_id
                payment.status = PaymentStatus.SUCCESSFUL
                order = await self._get_order(payment.order_id, db)
                order.status = OrderStatus.PAID
                await db.commit()
            except Exception:
                await db.rollback()
                raise

    async def handle_expired_session(self, session_id: str) -> None:
        """Handle expired session payment."""
        async with get_db_contextmanager() as db:
            try:
                payment = await self._get_payment_by_session_id_payment_id(session_id, db)
                payment.status = PaymentStatus.EXPIRED
                await db.commit()
            except Exception:
                await db.rollback()
                raise

    @staticmethod
    async def handle_payment_intent_successful(payment_intent_id: str) -> None:
        """Handle successful payment."""
        try:
            charge_intent = stripe.PaymentIntent.retrieve(payment_intent_id, expand=["charges"])
            charges = charge_intent.charges.data[0]
            receipt_url = charges.receipt_url if charges else None
            payment_details_name = charges.name if charges else None
            payment_details_email = charges.email if charges else None

            payment_details = {
                "payment_details_name": payment_details_name,
                "payment_details_email": payment_details_email,
                "payment_id": payment_intent_id,
                "receipt_url": receipt_url,
            }

            send_stripe_payment_success_email_task.delay(payment_details_email, payment_details)

        except Exception as e:
            logger.error(f"Error sending email: {e}")
            raise

    async def handle_payment_intent_failed(self, payment_intent_id: str) -> None:
        """Handle failed payment."""
        pass

    async def handle_refunded_payment(self, payment_intent_id: str) -> None:
        """Handle refunded payment."""
        async with get_db_contextmanager() as db:
            try:
                payment = await self._get_payment_by_session_id_payment_id(payment_intent_id, db)
                payment.status = PaymentStatus.REFUNDED
                try:
                    order = await self._get_order(payment.order_id, db)
                    order.status = OrderStatus.CANCELED
                except ValueError:
                    logger.error(f"Order {payment.order_id} not found for payment {payment.id}")
                await db.commit()
            except Exception:
                await db.rollback()
                raise
