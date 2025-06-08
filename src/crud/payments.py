from typing import Any, Optional

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database.deps import get_db
from database.models.orders import OrderItemModel, OrderModel
from database.models.payments import PaymentItemModel, PaymentModel
from schemas.payments import PaymentCreate, PaymentStatusSchema, PaymentUpdate


async def create_payment(
    payment: PaymentCreate,
    db: AsyncSession = Depends(get_db)
) -> PaymentModel:
    db_payment = PaymentModel(**payment.model_dump())
    db.add(db_payment)
    await db.commit()
    await db.refresh(db_payment)
    return db_payment


async def get_payment(
    payment_id: int,
    db: AsyncSession = Depends(get_db)
) -> Optional[PaymentModel]:
    result = await db.execute(select(PaymentModel).filter(PaymentModel.id == payment_id))
    return result.scalar_one_or_none()


async def get_payments(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> list[PaymentModel]:
    result = await db.execute(select(PaymentModel).offset(skip).limit(limit))
    return list(result.scalars().all())


async def update_payment(
    payment_id: int,
    payment: PaymentUpdate,
    db: AsyncSession = Depends(get_db)
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
    db: AsyncSession = Depends(get_db)
) -> Optional[PaymentModel]:
    db_payment = await get_payment(payment_id, db)
    if db_payment:
        await db.delete(db_payment)
        await db.commit()
    return db_payment


async def get_user_payments(
    user_id: int,
    db: AsyncSession = Depends(get_db)
) -> list[PaymentModel]:
    result = await db.execute(select(PaymentModel).where(PaymentModel.user_id == user_id))
    return list(result.scalars().all())


async def get_all_payments(
    db: AsyncSession = Depends(get_db),
    payment_status: Optional[PaymentStatusSchema] = None
) -> list[PaymentModel]:
    query = select(PaymentModel)
    if payment_status:
        query = query.where(PaymentModel.status == payment_status)
    result = await db.execute(query)
    return list(result.scalars().all())
