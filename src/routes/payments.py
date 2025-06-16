import logging
from datetime import datetime
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from config.dependencies import allow_roles, get_current_user, require_admin
from crud.payments import create_payment, get_payment_by_id
from database.deps import get_db
from database.models import OrderItemModel, OrderModel, UserGroupEnum, UserModel
from database.models.orders import OrderStatus
from database.models.payments import PaymentItemModel, PaymentModel, PaymentStatus
from schemas.payments import (
    CheckoutSessionResponse,
    PaymentBaseSchema,
    PaymentCreateSchema,
    PaymentListSchema,
    PaymentStatisticsResponse,
    PaymentStatusSchema,
    RefundResponse,
    WebhookResponse,
)
from services.stripe_service import StripeService

logger = logging.getLogger(__name__)
router = APIRouter(tags=["payments"])


@router.post("/create-intent", response_model=CheckoutSessionResponse)
async def create_checkout_session(
    payment_data: PaymentCreateSchema,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
) -> CheckoutSessionResponse:
    # Create payment and get validated order through crud
    payment = await create_payment(payment_data, current_user.id, db)

    session_data = await StripeService.create_checkout_session(
        request,
        payment.order
    )

    payment.external_payment_id = session_data.external_payment_id
    await db.commit()
    await db.refresh(payment)

    return CheckoutSessionResponse(
        payment_url=session_data.payment_url,
        payment_id=payment.id,
        external_payment_id=session_data.external_payment_id
    )


@router.post("/webhook", response_model=WebhookResponse)
async def stripe_webhook(request: Request, db: AsyncSession = Depends(get_db)) -> WebhookResponse:
    try:
        payload = await request.body()
        sig_header = request.headers.get("stripe-signature")

        if not sig_header:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No Stripe signature found"
            )

        webhook_data = await StripeService.handle_webhook(payload, sig_header)
        if not webhook_data:
            return WebhookResponse()

        result = await db.execute(
            select(PaymentModel).where(
                PaymentModel.external_payment_id == webhook_data["external_payment_id"]
            )
        )
        payment = result.scalar_one_or_none()
        if not payment:
            return WebhookResponse()

        payment.status = webhook_data["status"]
        order = await db.get(OrderModel, payment.order_id)
        if not order:
            await db.commit()
            return WebhookResponse()

        if webhook_data["status"] == PaymentStatus.SUCCESSFUL:
            order.status = OrderStatus.PAID
        elif webhook_data["status"] == PaymentStatus.CANCELED:
            order.status = OrderStatus.CANCELED
        else:
            order.status = order.status

        await db.commit()
        return WebhookResponse()
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
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
            selectinload(PaymentModel.payment_items).selectinload(PaymentItemModel.order_item).selectinload(
                OrderItemModel.movie),
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


@router.get("/admin/statistics", response_model=PaymentStatisticsResponse)
async def get_payment_statistics(
    is_admin: bool = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
) -> PaymentStatisticsResponse:
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

    return PaymentStatisticsResponse(
        total_amount=Decimal(total_amount),
        total_payments=len(payments),
        successful_payments=successful_payments,
        refunded_payments=refunded_payments,
        success_rate=(successful_payments / len(payments)) * 100 if payments else 0
    )


@router.post("/{payment_id}/refund", response_model=RefundResponse)
async def refund_payment(
    payment_id: int,
    is_admin: bool = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
) -> RefundResponse:
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
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to process refund"
            )

        payment.status = PaymentStatus.REFUNDED
        await db.commit()
        return RefundResponse()
    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get(
    "/pays/{payment_id}",
    response_model=PaymentBaseSchema,
    dependencies=[Depends(allow_roles(UserGroupEnum.ADMIN, UserGroupEnum.USER))]
)
async def get_payment_details(
    payment_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> PaymentBaseSchema:
    payment = await get_payment_by_id(payment_id, db)
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )

    if current_user.group.name == UserGroupEnum.ADMIN:
        return PaymentBaseSchema.model_validate(payment)

    if payment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this payment"
        )

    return PaymentBaseSchema.model_validate(payment)
