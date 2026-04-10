from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_account
import models
import schemas

router = APIRouter(prefix="/payments", tags=["Pagamentos"])


@router.post("", response_model=schemas.PaymentOut, status_code=status.HTTP_201_CREATED)
def create_payment(
    payload: schemas.PaymentRequest,
    account: models.Account = Depends(get_current_account),
    db:      Session = Depends(get_db),
):
    """
    Realiza um pagamento (boleto, conta, cartão ou tributo).
    Debita o valor do saldo e registra a movimentação.
    """
    if account.saldo < payload.valor:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Saldo insuficiente para este pagamento"
        )

    # Débito no saldo
    account.saldo = round(account.saldo - payload.valor, 2)

    # Registro do pagamento
    payment = models.Payment(
        account_id=account.id,
        tipo=payload.tipo,
        codigo_barras=payload.codigo_barras,
        valor=payload.valor,
        data_pagamento=payload.data_pagamento,
        descricao=payload.descricao,
        status=models.PaymentStatus.confirmado,
    )
    db.add(payment)

    # Transação no extrato
    db.add(models.Transaction(
        account_id=account.id,
        tipo=models.TransactionType.debito,
        valor=payload.valor,
        descricao=payload.descricao or f"Pagamento {payload.tipo}",
        categoria="pagamento",
    ))

    db.commit()
    db.refresh(payment)
    return payment


@router.get("", response_model=List[schemas.PaymentOut])
def list_payments(
    account: models.Account = Depends(get_current_account),
    db:      Session = Depends(get_db),
):
    """Lista todos os pagamentos da conta (mais recentes primeiro)."""
    return (
        db.query(models.Payment)
        .filter(models.Payment.account_id == account.id)
        .order_by(models.Payment.created_at.desc())
        .all()
    )


@router.get("/{payment_id}", response_model=schemas.PaymentOut)
def get_payment(
    payment_id: int,
    account:    models.Account = Depends(get_current_account),
    db:         Session = Depends(get_db),
):
    """Detalha um pagamento específico."""
    payment = db.query(models.Payment).filter(
        models.Payment.id == payment_id,
        models.Payment.account_id == account.id,
    ).first()
    if not payment:
        raise HTTPException(status_code=404, detail="Pagamento não encontrado")
    return payment
