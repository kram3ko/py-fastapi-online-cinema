from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.orders import OrderItemModel, OrderModel, OrderStatus
from database.models.payments import PaymentItemModel, PaymentModel, PaymentStatus
from schemas.payments import PaymentCreateSchema, PaymentStatusSchema, PaymentUpdateSchema


async def update_payment_and_order_status(
    db: AsyncSession, payment_intent: str, new_status: PaymentStatus, order_status: OrderStatus
) -> None:
    result = await db.execute(
        select(PaymentModel).where(PaymentModel.external_payment_id == payment_intent)
    )
    payment = result.scalar_one_or_none()

    if payment:
        payment.status = new_status
        order = await db.get(OrderModel, payment.order_id)
        if order:
            order.status = order_status
        await db.commit()


async def create_payment(
    payment: PaymentCreateSchema,
    user_id: int,
    db: AsyncSession
) -> PaymentModel:
    try:
        result = await db.execute(
            select(OrderModel)
            .where(
                OrderModel.id == payment.order_id,
                OrderModel.user_id == user_id,
                OrderModel.status == OrderStatus.PENDING
            )
            .options(
                selectinload(OrderModel.order_items).selectinload(OrderItemModel.movie),
                selectinload(OrderModel.user)
            )
        )
        order = result.scalar_one_or_none()
        if not order:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Order not found or not available for payment"
            )

        # Calculate total amount from order items
        total_amount = sum(float(item.price_at_order) for item in order.order_items)

        # Create payment
        payment_data = payment.model_dump()
        payment_data["user_id"] = user_id
        payment_data["amount"] = total_amount
        db_payment = PaymentModel(**payment_data)
        db.add(db_payment)
        await db.flush()

        payment_items = []
        for item in order.order_items:
            payment_item = PaymentItemModel(
                payment_id=db_payment.id,
                order_item_id=item.id,
                price_at_payment=item.price_at_order
            )
            payment_items.append(payment_item)
        db.add_all(payment_items)

        await db.commit()
        await db.refresh(db_payment)

        # Load the order relationship
        result = await db.execute(
            select(PaymentModel)
            .where(PaymentModel.id == db_payment.id)
            .options(
                selectinload(PaymentModel.order).selectinload(OrderModel.order_items).selectinload(OrderItemModel.movie),
                selectinload(PaymentModel.payment_items)
            )
        )
        return result.scalar_one()
    except HTTPException:
        await db.rollback()
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


async def get_payment(
    payment_id: int,
    db: AsyncSession
) -> Optional[PaymentModel]:
    result = await db.execute(select(PaymentModel).filter(PaymentModel.id == payment_id))
    return result.scalar_one_or_none()


async def get_payments(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
) -> list[PaymentModel]:
    result = await db.execute(select(PaymentModel).offset(skip).limit(limit))
    return list(result.scalars().all())


async def update_payment(
    payment_id: int,
    payment: PaymentUpdateSchema,
    db: AsyncSession
) -> Optional[PaymentModel]:
    db_payment = await get_payment(payment_id, db)
    if db_payment:
        update_data = payment.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_payment, field, value)
        await db.commit()
        await db.refresh(db_payment)
    return db_payment


async def delete_payment(
    payment_id: int,
    db: AsyncSession
) -> Optional[PaymentModel]:
    db_payment = await get_payment(payment_id, db)
    if db_payment:
        await db.delete(db_payment)
        await db.commit()
    return db_payment


async def get_user_payments(
    user_id: int,
    db: AsyncSession
) -> list[PaymentModel]:
    result = await db.execute(select(PaymentModel).where(PaymentModel.user_id == user_id))
    return list(result.scalars().all())


async def get_all_payments(
    db: AsyncSession,
    payment_status: Optional[PaymentStatusSchema] = None
) -> list[PaymentModel]:
    query = select(PaymentModel)
    if payment_status:
        query = query.where(PaymentModel.status == payment_status)
    result = await db.execute(query)
    return list(result.scalars().all())


async def get_payment_by_id(payment_id: int, db: AsyncSession) -> PaymentModel | None:
    result = await db.execute(
        select(PaymentModel)
        .where(PaymentModel.id == payment_id)
        .options(
            selectinload(
                PaymentModel.payment_items
            ).selectinload(PaymentItemModel.order_item).selectinload(
                OrderItemModel.movie),
            selectinload(PaymentModel.user),
            selectinload(PaymentModel.order)
        )
    )
    return result.scalar_one_or_none()
