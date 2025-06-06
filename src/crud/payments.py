from fastapi import HTTPException, status
from fastapi.params import Depends
from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from database import get_db
from database.models.orders import OrderItemModel, OrderModel
from database.models.payments import PaymentItemModel, PaymentModel, PaymentStatus
from schemas.payments import PaymentCreateSchema, PaymentStatusSchema, AdminPaymentFilter


async def create_payment(
    payment_data: PaymentCreateSchema,
    user_id: int,
    db: AsyncSession = Depends(get_db)
) -> PaymentModel:
    result = await db.execute(select(OrderModel).where(OrderModel.id == payment_data.order_id))
    order = result.scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Order not found.")

    if order.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="It`s not your order.")

    result = await db.execute(select(OrderItemModel).where(OrderItemModel.order_id == order.id))
    order_items = result.scalars().all()
    total_amount = sum([item.price for item in order_items])

    if total_amount != payment_data.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Incorrect payment amount. Expected: {total_amount}, Got: {payment_data.amount}")

    payment = PaymentModel(
        user_id=user_id,
        order_id=order.id,
        amount=payment_data.amount,
        status=PaymentStatus.SUCCESSFUL,
    )

    db.add(payment)

    await db.flush()

    for item in order_items:
        payment_item = PaymentItemModel(
            payment_id=payment.id,
            order_item_id=item.id,
            price_at_payment=item.price,
        )
        db.add(payment_item)

    await db.commit()
    await db.refresh(payment)
    return payment


async def get_payment_by_id(payment_id: int, db: AsyncSession) -> PaymentModel | None:
    result = await db.execute(select(PaymentModel).where(PaymentModel.id == payment_id))
    return result.scalar_one_or_none()


async def get_user_payments(
    user_id: int,
    db: AsyncSession,
    skip: int = 0,
    limit: int = 10
) -> list[PaymentModel]:
    result = await db.execute(
        select(PaymentModel)
        .where(PaymentModel.user_id == user_id)
        .offset(skip)
        .limit(limit)
    )
    return result.scalars().all()


async def get_payments_with_filters(
    filters: AdminPaymentFilter,
    db: AsyncSession
) -> list[PaymentModel]:
    query = select(PaymentModel)
    
    if filters.user_id:
        query = query.where(PaymentModel.user_id == filters.user_id)
    if filters.status:
        query = query.where(PaymentModel.status == filters.status)
    if filters.start_date:
        query = query.where(PaymentModel.created_at >= filters.start_date)
    if filters.end_date:
        query = query.where(PaymentModel.created_at <= filters.end_date)
    
    query = query.offset(filters.skip).limit(filters.limit)
    result = await db.execute(query)
    return result.scalars().all()


async def update_payment_status(
    payment_id: int,
    new_status: PaymentStatus,
    db: AsyncSession
) -> PaymentModel:
    payment = await get_payment_by_id(payment_id, db)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    
    payment.status = new_status
    await db.commit()
    await db.refresh(payment)
    return payment
