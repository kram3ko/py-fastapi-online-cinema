import logging

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.models.orders import OrderModel, OrderStatus
from database.models.payments import PaymentModel, PaymentStatus

logger = logging.getLogger(__name__)


class PaymentWebhookService:
    @staticmethod
    async def process_webhook_data(webhook_data: dict, db: AsyncSession) -> None:
        """
        Process webhook data and update payment and order status.

        Args:
            webhook_data: Dictionary containing webhook event data
            db: Database session

        Raises:
            HTTPException: If payment or order not found, or if there are processing errors
        """
        if not webhook_data:
            logger.info("Skipping webhook processing: No webhook data received")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No webhook data received"
            )

        result = await db.execute(
            select(PaymentModel).where(
                PaymentModel.external_payment_id == webhook_data["external_payment_id"]
            )
        )
        payment = result.scalar_one_or_none()

        if not payment:
            logger.warning(
                "Payment not found for external ID: %s",
                webhook_data["external_payment_id"]
            )
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Payment not found for external ID: {webhook_data['external_payment_id']}"
            )

        try:
            payment.status = webhook_data["status"]
            logger.info(
                "Updated payment status to %s for payment ID: %s",
                payment.status,
                payment.id
            )

            order = await db.get(OrderModel, payment.order_id)
            if not order:
                await db.commit()
                logger.warning(
                    "Order not found for payment ID: %s, order ID: %s",
                    payment.id,
                    payment.order_id
                )
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Order not found for payment ID: {payment.id}"
                )

            status_map = {
                PaymentStatus.SUCCESSFUL: OrderStatus.PAID,
                PaymentStatus.CANCELED: OrderStatus.CANCELED,
                PaymentStatus.REFUNDED: OrderStatus.CANCELED,
            }

            order.status = status_map.get(webhook_data["status"], order.status)

            await db.commit()
            logger.info(
                "Successfully processed webhook. Payment ID: %s, Status: %s, Order ID: %s, Order Status: %s",
                payment.id,
                payment.status,
                order.id,
                order.status
            )
        except Exception as e:
            await db.rollback()
            logger.error(
                "Error processing webhook: %s",
                str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Error processing webhook: {str(e)}"
            )
