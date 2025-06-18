import logging
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.deps import get_db_contextmanager
from database.models.orders import OrderModel, OrderStatus
from database.models.payments import PaymentModel, PaymentStatus

logger = logging.getLogger(__name__)


class PaymentWebhookService:
    """Service for handling payment webhooks and updating payment/order statuses."""

    async def get_payment(self, external_payment_id: str) -> Optional[PaymentModel]:
        """Get payment by external payment ID."""
        async with get_db_contextmanager() as db:
            try:
                return await self._get_payment_by_external_id(external_payment_id, db)
            except Exception as e:
                logger.error(f"Error getting payment: {e}")
                await db.rollback()
                return None

    @staticmethod
    async def get_order(order_id: int, db: AsyncSession) -> Optional[OrderModel]:
        """Get order by ID."""
        try:
            return await db.get(OrderModel, order_id)
        except Exception as e:
            logger.error(f"Error getting order: {e}")
            await db.rollback()
            return None

    @staticmethod
    async def update_payment_status(payment: PaymentModel, status: PaymentStatus, db: AsyncSession) -> None:
        """Update payment status."""
        try:
            payment.status = status
            await db.commit()
        except Exception as e:
            logger.error(f"Error updating payment status: {e}")
            await db.rollback()
            raise

    @staticmethod
    async def update_order_status(order: OrderModel, status: OrderStatus, db: AsyncSession) -> None:
        """Update order status."""
        try:
            order.status = status
            await db.commit()
        except Exception as e:
            logger.error(f"Error updating order status: {e}")
            await db.rollback()
            raise

    async def handle_successful_payment(self, external_payment_id: str) -> None:
        """Handle successful payment."""
        async with get_db_contextmanager() as db:
            try:
                payment = await self._get_payment_by_external_id(external_payment_id, db)
                if not payment:
                    return

                payment.status = PaymentStatus.SUCCESSFUL
                await db.commit()

                order = await self.get_order(payment.order_id, db)
                if order:
                    await self.update_order_status(order, OrderStatus.PAID, db)
            except Exception as e:
                logger.error(f"Error handling successful payment: {e}")
                await db.rollback()
                raise

    async def handle_failed_payment(self, external_payment_id: str) -> None:
        """Handle failed payment."""
        async with get_db_contextmanager() as db:
            try:
                payment = await self._get_payment_by_external_id(external_payment_id, db)
                if not payment:
                    return

                payment.status = PaymentStatus.CANCELED
                await db.commit()

                order = await self.get_order(payment.order_id, db)
                if order:
                    await self.update_order_status(order, OrderStatus.PENDING, db)
            except Exception as e:
                logger.error(f"Error handling failed payment: {e}")
                await db.rollback()
                raise

    async def handle_refunded_payment(self, external_payment_id: str) -> None:
        """Handle refunded payment."""
        async with get_db_contextmanager() as db:
            try:
                payment = await self._get_payment_by_external_id(external_payment_id, db)
                if not payment:
                    return

                payment.status = PaymentStatus.REFUNDED
                await db.commit()

                order = await self.get_order(payment.order_id, db)
                if order:
                    await self.update_order_status(order, OrderStatus.CANCELED, db)
            except Exception as e:
                logger.error(f"Error handling refunded payment: {e}")
                await db.rollback()
                raise

    async def handle_expired_payment(self, external_payment_id: str) -> None:
        """Handle expired payment."""
        async with get_db_contextmanager() as db:
            try:
                payment = await self._get_payment_by_external_id(external_payment_id, db)
                if not payment:
                    return

                payment.status = PaymentStatus.EXPIRED
                await db.commit()

                order = await self.get_order(payment.order_id, db)
                if order:
                    await self.update_order_status(order, OrderStatus.PENDING, db)
            except Exception as e:
                logger.error(f"Error handling expired payment: {e}")
                await db.rollback()
                raise

    @staticmethod
    async def _get_payment_by_external_id(external_payment_id: str, db: AsyncSession) -> Optional[PaymentModel]:
        try:
            result = await db.execute(
                select(PaymentModel).where(PaymentModel.external_payment_id == external_payment_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"Error getting payment by external ID: {e}")
            await db.rollback()
            return None
