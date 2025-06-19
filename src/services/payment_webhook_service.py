import asyncio
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.deps import get_db_contextmanager
from database.models.orders import OrderModel, OrderStatus
from database.models.payments import PaymentModel, PaymentStatus

logger = logging.getLogger(__name__)


class PaymentWebhookService:
    """Service for handling payment webhooks and updating payment/order statuses."""

    @staticmethod
    async def _get_payment_by_external_id(payment_id: str, db: AsyncSession, attempts: int = 3) -> PaymentModel:
        for attempt in range(attempts):
            payment = await db.scalar(
                select(PaymentModel).where(
                    (PaymentModel.session_id == payment_id) |
                    (PaymentModel.payment_intent_id == payment_id)
                )
            )
            if payment:
                return payment
            if attempt < 2:
                await asyncio.sleep(1)
        logger.error(f"Payment not found for session_id={payment_id}")
        raise ValueError("Payment not found")

    @staticmethod
    async def _get_order(order_id: int, db: AsyncSession) -> OrderModel:
        order = await db.get(OrderModel, order_id)
        if not order:
            logger.error(f"Order not found for order_id={order_id}")
            raise ValueError("Order not found")
        return order

    async def handle_successful_session(self, session_id: str, payment_intent_id: str) -> None:
        """Handle successful session payment."""
        async with get_db_contextmanager() as db:
            try:
                payment = await self._get_payment_by_external_id(session_id, db)
                if payment_intent_id.startswith("pi_") and payment.session_id.startswith("cs_"):
                    payment.payment_intent_id = payment_intent_id
                await db.commit()
            except Exception:
                await db.rollback()
                raise

    async def handle_expired_session(self, session_id: str) -> None:
        """Handle expired session payment."""
        async with get_db_contextmanager() as db:
            try:
                payment = await self._get_payment_by_external_id(session_id, db)
                payment.status = PaymentStatus.EXPIRED
                await db.commit()
            except Exception:
                await db.rollback()
                raise

    async def handle_successful_payment(self, payment_intent_id: str) -> None:
        """Handle successful payment."""
        async with get_db_contextmanager() as db:
            try:
                payment = await self._get_payment_by_external_id(payment_intent_id, db)

                payment.status = PaymentStatus.SUCCESSFUL
                order = await self._get_order(payment.order_id, db)
                order.status = OrderStatus.PAID
                await db.commit()
            except Exception:
                await db.rollback()
                raise

    async def handle_failed_payment(self, payment_intent_id: str) -> None:
        """Handle failed payment."""
        async with get_db_contextmanager() as db:
            try:
                payment = await self._get_payment_by_external_id(payment_intent_id, db)
                payment.status = PaymentStatus.CANCELED
                order = await self._get_order(payment.order_id, db)
                order.status = OrderStatus.PENDING
                await db.commit()
            except Exception:
                await db.rollback()
                raise

    async def handle_refunded_payment(self, payment_intent_id: str) -> None:
        """Handle refunded payment."""
        async with get_db_contextmanager() as db:
            try:
                payment = await self._get_payment_by_external_id(payment_intent_id, db)
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
