from fastapi import HTTPException, status
from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_

from database import get_db
from database.models.accounts import UserModel
from database.models.orders import OrderItemModel, OrderModel
from database.models.payments import PaymentItemModel, PaymentModel
from schemas.payments import PaymentCreateSchema, PaymentStatusSchema
from schemas.payments_admin_filter import AdminPaymentFilterSchema


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
    order_items = result.scalar().all()
    total_amount = sum([item.price for item in order_items])

    if total_amount != payment_data.amount:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Incorrect payment ammount. Expected: {total_amount}, Got: {payment_data.amount}")

    payment = PaymentModel(
        user_id=user_id,
        order_id=order.id,
        amount=payment_data.amount,
        status=PaymentStatusSchema.successful,
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


async def get_user_payments(
    user_id: int,
    db: AsyncSession = Depends(get_db)
) -> any:
    result = await db.execute(select(PaymentModel).where(PaymentModel.user_id == user_id))

    return result.scalars().all()


async def get_all_payments(user_id: int,
                           db: AsyncSession = Depends(get_db),
                           payment_status: PaymentStatusSchema = None):
    user = select(UserModel).where(UserModel.user_id==user_id)
    if user.is_admin():
        query = select(PaymentModel)
        if payment_status:
            query.where(PaymentModel.status == payment_status)
        result = await db.execute(query)
        return result.scalars().all()
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You don`t have any rules for this action.")


async def get_filtered_payments_for_admin(
    db: AsyncSession,
    filters: AdminPaymentFilterSchema
) -> list[PaymentModel]:
    stmt = select(PaymentModel)
    filtered = []

    if filters.user_id:
        filtered.append(PaymentModel.user_id == filters.user_id)
    if filters.status:
        filtered.append(PaymentModel.status == filters.status)
    if filters.start_date:
        filtered.append(PaymentModel.created_at >= filters.start_date)
    if filters.end_date:
        filtered.append(PaymentModel.created_at <= filters.end_date)

    if filtered:
        stmt = stmt.where(and_(*filtered))

    stmt = stmt.order_by(PaymentModel.created_at.desc())
    result = await db.execute(stmt)
    return result.scalars().all()
