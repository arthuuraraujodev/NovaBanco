from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_account
import models
import schemas

router = APIRouter(prefix="/transfers", tags=["Transferências"])


@router.post("", response_model=schemas.TransferOut, status_code=status.HTTP_201_CREATED)
def create_transfer(
    payload: schemas.TransferRequest,
    account: models.Account = Depends(get_current_account),
    db:      Session = Depends(get_db),
):
    """
    Realiza TED ou DOC para outro banco.
    Valida saldo, debita o valor e registra no extrato.
    """
    if account.saldo < payload.valor:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Saldo insuficiente para esta transferência"
        )

    # Débito no saldo
    account.saldo = round(account.saldo - payload.valor, 2)

    transfer = models.Transfer(
        account_id=account.id,
        banco=payload.banco,
        agencia=payload.agencia,
        conta=payload.conta,
        tipo_conta=payload.tipo_conta,
        cpf_favorecido=payload.cpf_favorecido,
        nome_favorecido=payload.nome_favorecido,
        valor=payload.valor,
        modalidade=payload.modalidade,
        mensagem=payload.mensagem,
        status=models.PaymentStatus.confirmado,
    )
    db.add(transfer)

    # Extrato
    db.add(models.Transaction(
        account_id=account.id,
        tipo=models.TransactionType.debito,
        valor=payload.valor,
        descricao=f"{payload.modalidade.value} para {payload.nome_favorecido}",
        categoria=payload.modalidade.value.lower(),
    ))

    db.commit()
    db.refresh(transfer)
    return transfer


@router.get("", response_model=List[schemas.TransferOut])
def list_transfers(
    account: models.Account = Depends(get_current_account),
    db:      Session = Depends(get_db),
):
    """Lista todas as transferências enviadas (mais recentes primeiro)."""
    return (
        db.query(models.Transfer)
        .filter(models.Transfer.account_id == account.id)
        .order_by(models.Transfer.created_at.desc())
        .all()
    )


@router.get("/{transfer_id}", response_model=schemas.TransferOut)
def get_transfer(
    transfer_id: int,
    account:     models.Account = Depends(get_current_account),
    db:          Session = Depends(get_db),
):
    """Detalha uma transferência específica."""
    transfer = db.query(models.Transfer).filter(
        models.Transfer.id == transfer_id,
        models.Transfer.account_id == account.id,
    ).first()
    if not transfer:
        raise HTTPException(status_code=404, detail="Transferência não encontrada")
    return transfer
