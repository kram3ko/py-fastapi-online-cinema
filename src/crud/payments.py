from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from database.models.payments import PaymentModel
from schemas.payments import PaymentCreateSchema, PaymentStatusSchema, PaymentUpdateSchema


async def create_payment(
    payment: PaymentCreateSchema,
    user_id: int,
    db: AsyncSession
) -> PaymentModel:
    try:
        payment_data = payment.model_dump()
        payment_data["user_id"] = user_id
        db_payment = PaymentModel(**payment_data)
        db.add(db_payment)
        await db.flush()
        await db.refresh(db_payment)
        await db.commit()
        return db_payment
    except Exception as e:
        await db.rollback()
        raise e


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
            selectinload(PaymentModel.payment_items),
            selectinload(PaymentModel.user),
            selectinload(PaymentModel.order)
        )
    )
    return result.scalar_one_or_none()
