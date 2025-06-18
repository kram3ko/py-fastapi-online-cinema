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
    async def _get_payment_by_external_id(external_payment_id: str, db: AsyncSession) -> PaymentModel:
        """Get payment by external ID."""
        payment = await db.scalar(
            select(PaymentModel).where(PaymentModel.external_payment_id == external_payment_id)
        )
        if not payment:
            logger.error(f"Payment with external ID {external_payment_id} not found")
            raise Exception(f"Payment with external payment ID {external_payment_id} not found")
        return payment

    @staticmethod
    async def _get_order(order_id: int, db: AsyncSession) -> OrderModel:
        """Get order by ID."""
        order = await db.get(OrderModel, order_id)
        if not order:
            logger.error(f"Order with ID {order_id} not found")
            raise Exception(f"Order with ID {order_id} not found")
        return order

    @staticmethod
    async def update_payment_status(payment: PaymentModel, status: PaymentStatus) -> None:
        """Update payment status."""
        try:
            payment.status = status
        except Exception as e:
            logger.error(f"Error updating payment status: {e}")
            raise

    @staticmethod
    async def update_order_status(order: OrderModel, status: OrderStatus) -> None:
        """Update order status."""
        try:
            order.status = status
        except Exception as e:
            logger.error(f"Error updating order status: {e}")
            raise

    async def handle_successful_session(self, external_payment_id: str) -> None:
        """Handle successful session payment."""
        async with get_db_contextmanager() as db:
            try:
                payment = await self._get_payment_by_external_id(external_payment_id, db)
                await self.update_payment_status(payment, PaymentStatus.SUCCESSFUL)

                order = await self._get_order(payment.order_id, db)
                await self.update_order_status(order, OrderStatus.PAID)

                await db.commit()
            except Exception as e:
                logger.error(f"Error handling successful session: {e}")
                await db.rollback()
                raise

    async def handle_expired_session(self, external_payment_id: str) -> None:
        """Handle expired session payment."""
        async with get_db_contextmanager() as db:
            try:
                payment = await self._get_payment_by_external_id(external_payment_id, db)
                await self.update_payment_status(payment, PaymentStatus.EXPIRED)

                await db.commit()
            except Exception as e:
                logger.error(f"Error handling expired session: {e}")
                await db.rollback()
                raise

    async def handle_successful_payment(self, external_payment_id: str) -> None:
        """Handle successful payment."""
        async with get_db_contextmanager() as db:
            try:
                payment = await self._get_payment_by_external_id(external_payment_id, db)
                await self.update_payment_status(payment, PaymentStatus.SUCCESSFUL)

                order = await self._get_order(payment.order_id, db)
                await self.update_order_status(order, OrderStatus.PAID)

                await db.commit()
            except Exception as e:
                logger.error(f"Error handling successful payment: {e}")
                await db.rollback()
                raise

    async def handle_failed_payment(self, external_payment_id: str) -> None:
        """Handle failed payment."""
        async with get_db_contextmanager() as db:
            try:
                payment = await self._get_payment_by_external_id(external_payment_id, db)
                await self.update_payment_status(payment, PaymentStatus.CANCELED)

                order = await self._get_order(payment.order_id, db)
                await self.update_order_status(order, OrderStatus.PENDING)

                await db.commit()
            except Exception as e:
                logger.error(f"Error handling failed payment: {e}")
                await db.rollback()
                raise

    async def handle_refunded_payment(self, external_payment_id: str) -> None:
        """Handle refunded payment."""
        async with get_db_contextmanager() as db:
            try:
                payment = await self._get_payment_by_external_id(external_payment_id, db)
                await self.update_payment_status(payment, PaymentStatus.REFUNDED)

                order = await self._get_order(payment.order_id, db)
                await self.update_order_status(order, OrderStatus.CANCELED)

                await db.commit()
            except Exception as e:
                logger.error(f"Error handling refunded payment: {e}")
                await db.rollback()
                raise
