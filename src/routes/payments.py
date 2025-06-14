from datetime import datetime

import stripe
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config.dependencies import get_current_user, require_admin
from crud.payments import create_payment, get_payment_by_id
from database.deps import get_db
from database.models import UserModel
from database.models.payments import PaymentModel, PaymentStatus
from schemas.payments import (
    PaymentBaseSchema,
    PaymentCreateSchema,
    PaymentListSchema,
    PaymentStatusSchema,
)
from services.stripe_service import StripeService, stripe_settings

router = APIRouter(tags=["payments"])


@router.post("/create-intent", response_model=dict)
async def create_payment_intent(
    payment_data: PaymentCreateSchema,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if payment_data.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Payment amount must be greater than 0"
        )

    try:
        payment = await create_payment(payment_data, current_user.id, db)
        intent_data = await StripeService.create_payment_intent(payment_data)
        payment.external_payment_id = intent_data["payment_intent_id"]
        await db.commit()

        return {
            "payment_url": intent_data["payment_url"],
            "payment_id": payment.id,
            "external_payment_id": intent_data["payment_intent_id"]
        }
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/webhook")
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)) -> dict:
    try:
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")

        if not sig_header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No Stripe signature found"
            )

        webhook_data = await StripeService.handle_webhook(payload, sig_header)

        if webhook_data:
            result = await db.execute(
                select(PaymentModel).where(
                    PaymentModel.external_payment_id == webhook_data["external_payment_id"]
                )
            )
            payment = result.scalar_one_or_none()

            if payment:
                payment.status = webhook_data["status"]
                await db.commit()

        return {"status": "success"}
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/history", response_model=PaymentListSchema)
async def get_payment_history(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
) -> PaymentListSchema:
    query = (
        select(PaymentModel)
        .where(PaymentModel.user_id == current_user.id)
        .options(
            selectinload(PaymentModel.payment_items),
            selectinload(PaymentModel.order)
        )
        .order_by(PaymentModel.created_at.desc())
    )
    total = await db.scalar(select(func.count()).select_from(query.subquery()))

    result = await db.execute(
        query.offset(skip).limit(limit)
    )
    payments = result.scalars().all()

    return PaymentListSchema(
        payments=payments,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/admin", response_model=PaymentListSchema)
async def admin_get_payments(
    is_admin: bool = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    user_id: int | None = None,
    payment_status: PaymentStatusSchema | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
) -> PaymentListSchema:
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access admin endpoints"
        )

    query = (
        select(PaymentModel)
        .options(
            selectinload(PaymentModel.payment_items),
            selectinload(PaymentModel.order)
        )
    )

    if user_id:
        query = query.where(PaymentModel.user_id == user_id)
    if payment_status:
        query = query.where(PaymentModel.status == payment_status)
    if start_date:
        query = query.where(PaymentModel.created_at >= start_date)
    if end_date:
        query = query.where(PaymentModel.created_at <= end_date)

    total = await db.scalar(select(func.count()).select_from(query.subquery()))
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    payments = result.scalars().all()

    return PaymentListSchema(
        payments=payments,
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/admin/statistics")
async def get_payment_statistics(
    is_admin: bool = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> dict:
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access admin endpoints"
        )

    query = select(PaymentModel)

    if start_date:
        query = query.where(PaymentModel.created_at >= start_date)
    if end_date:
        query = query.where(PaymentModel.created_at <= end_date)

    result = await db.execute(query)
    payments = result.scalars().all()

    total_amount = sum(payment.amount for payment in payments)
    successful_payments = sum(1 for p in payments if p.status == PaymentStatus.SUCCESSFUL)
    refunded_payments = sum(1 for p in payments if p.status == PaymentStatus.REFUNDED)

    return {
        "total_amount": total_amount,
        "total_payments": len(payments),
        "successful_payments": successful_payments,
        "refunded_payments": refunded_payments,
        "success_rate": (successful_payments / len(payments)) * 100 if payments else 0
    }


@router.post("/{payment_id}/refund")
async def refund_payment(
    payment_id: int,
    is_admin: bool = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> dict:
    if not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to refund payments"
        )

    payment = await get_payment_by_id(payment_id, db)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    if payment.status != PaymentStatus.SUCCESSFUL:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only refund successful payments"
        )

    try:
        success = await StripeService.refund_payment(payment)
        if success:
            payment.status = PaymentStatus.REFUNDED
            await db.commit()
            return {"status": "refunded"}

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to process refund"
        )
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/{payment_id}", response_model=PaymentBaseSchema)
async def get_payment_details(
    payment_id: int,
    current_user: UserModel = Depends(get_current_user),
    is_admin: bool = Depends(require_admin),
    db: AsyncSession = Depends(get_db),

) -> PaymentBaseSchema:
    payment = await get_payment_by_id(payment_id, db)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    if payment.user_id != current_user.id and not is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this payment"
        )

    return payment


@router.get("/success/")
async def payment_success(
    session_id: str,
    db: AsyncSession = Depends(get_db)
) -> RedirectResponse:
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        result = await db.execute(
            select(PaymentModel).where(
                PaymentModel.external_payment_id == session.id
            )
        )
        payment = result.scalar_one_or_none()

        if payment:
            payment.status = PaymentStatus.SUCCESSFUL
            await db.commit()

        return RedirectResponse(url=f"{stripe_settings.FRONTEND_URL}/payments/history/")
    except Exception:
        return RedirectResponse(url=f"{stripe_settings.FRONTEND_URL}/payments/history/")


@router.get("/cancel/")
async def payment_cancel(
    session_id: str,
    db: AsyncSession = Depends(get_db)
) -> RedirectResponse:
    try:
        session = stripe.checkout.Session.retrieve(session_id)
        result = await db.execute(
            select(PaymentModel).where(
                PaymentModel.external_payment_id == session.id
            )
        )
        payment = result.scalar_one_or_none()

        if payment:
            payment.status = PaymentStatus.CANCELED
            await db.commit()

        return RedirectResponse(url=f"{stripe_settings.FRONTEND_URL}/payments/history/")
    except Exception:
        return RedirectResponse(url=f"{stripe_settings.FRONTEND_URL}/payments/history/")
