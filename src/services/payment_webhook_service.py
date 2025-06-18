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
    async def _get_payment_by_external_id(external_payment_id: str, db: AsyncSession) -> PaymentModel | None:
        """Get payment by external ID. Returns None if not found."""
        return await db.scalar(
            select(PaymentModel).where(PaymentModel.external_payment_id == external_payment_id)
        )

    @staticmethod
    async def _get_order(order_id: int, db: AsyncSession) -> OrderModel | None:
        """Get order by ID. Returns None if not found."""
        return await db.get(OrderModel, order_id)

    async def handle_successful_session(self, external_payment_id: str) -> None:
        """Handle successful session payment."""
        async with get_db_contextmanager() as db:
            try:
                payment = await self._get_payment_by_external_id(external_payment_id, db)
                if not payment:
                    return

                payment.status = PaymentStatus.SUCCESSFUL

                order = await self._get_order(payment.order_id, db)
                if order:
                    order.status = OrderStatus.PAID

                await db.commit()
            except Exception as e:
                logger.error(f"Error handling successful session: {e}")
                await db.rollback()

    async def handle_expired_session(self, external_payment_id: str) -> None:
        """Handle expired session payment."""
        async with get_db_contextmanager() as db:
            try:
                payment = await self._get_payment_by_external_id(external_payment_id, db)
                if not payment:
                    return

                payment.status = PaymentStatus.EXPIRED
                await db.commit()
            except Exception as e:
                logger.error(f"Error handling expired session: {e}")
                await db.rollback()

    async def handle_successful_payment(self, external_payment_id: str) -> None:
        """Handle successful payment."""
        async with get_db_contextmanager() as db:
            try:
                payment = await self._get_payment_by_external_id(external_payment_id, db)
                if not payment:
                    return

                payment.status = PaymentStatus.SUCCESSFUL

                order = await self._get_order(payment.order_id, db)
                if order:
                    order.status = OrderStatus.PAID

                await db.commit()
            except Exception as e:
                logger.error(f"Error handling successful payment: {e}")
                await db.rollback()

    async def handle_failed_payment(self, external_payment_id: str) -> None:
        """Handle failed payment."""
        async with get_db_contextmanager() as db:
            try:
                payment = await self._get_payment_by_external_id(external_payment_id, db)
                if not payment:
                    return

                payment.status = PaymentStatus.CANCELED

                order = await self._get_order(payment.order_id, db)
                if order:
                    order.status = OrderStatus.PENDING

                await db.commit()
            except Exception as e:
                logger.error(f"Error handling failed payment: {e}")
                await db.rollback()

    async def handle_refunded_payment(self, external_payment_id: str) -> None:
        """Handle refunded payment."""
        async with get_db_contextmanager() as db:
            try:
                payment = await self._get_payment_by_external_id(external_payment_id, db)
                if not payment:
                    return

                payment.status = PaymentStatus.REFUNDED

                order = await self._get_order(payment.order_id, db)
                if order:
                    order.status = OrderStatus.CANCELED

                await db.commit()
            except Exception as e:
                logger.error(f"Error handling refunded payment: {e}")
                await db.rollback()
