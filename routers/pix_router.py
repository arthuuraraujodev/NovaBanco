from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from auth import get_current_account
import models
import schemas

router = APIRouter(prefix="/pix", tags=["Pix"])


@router.get("/keys", response_model=List[schemas.PixKeyOut])
def get_pix_keys(
    account: models.Account = Depends(get_current_account),
    db:      Session = Depends(get_db),
):
    """Retorna todas as chaves Pix ativas da conta."""
    return (
        db.query(models.PixKey)
        .filter(
            models.PixKey.account_id == account.id,
            models.PixKey.ativo == True,
        )
        .all()
    )


@router.post("/send", response_model=schemas.PixTransactionOut, status_code=status.HTTP_201_CREATED)
def send_pix(
    payload: schemas.PixSendRequest,
    account: models.Account = Depends(get_current_account),
    db:      Session = Depends(get_db),
):
    """
    Envia um Pix para uma chave.
    Valida saldo, debita e registra no extrato.
    Se a chave pertencer a uma conta NovaBanco, credita automaticamente.
    """
    if account.saldo < payload.valor:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Saldo insuficiente para este Pix"
        )

    # Impede Pix para a própria chave
    propria_chave = db.query(models.PixKey).filter(
        models.PixKey.account_id == account.id,
        models.PixKey.chave == payload.chave,
        models.PixKey.ativo == True,
    ).first()
    if propria_chave:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Não é possível enviar Pix para a própria chave"
        )

    # Débito remetente
    account.saldo = round(account.saldo - payload.valor, 2)

    # Verifica se é uma conta interna (chave registrada no NovaBanco)
    chave_destino = db.query(models.PixKey).filter(
        models.PixKey.chave == payload.chave,
        models.PixKey.ativo == True,
    ).first()

    if chave_destino:
        conta_destino = db.query(models.Account).filter(
            models.Account.id == chave_destino.account_id
        ).first()
        if conta_destino:
            conta_destino.saldo = round(conta_destino.saldo + payload.valor, 2)
            db.add(models.Transaction(
                account_id=conta_destino.id,
                tipo=models.TransactionType.credito,
                valor=payload.valor,
                descricao=payload.mensagem or "Pix recebido",
                categoria="pix",
            ))

    # Registro da transação Pix
    pix_txn = models.PixTransaction(
        account_id=account.id,
        chave_tipo=payload.chave_tipo,
        chave=payload.chave,
        valor=payload.valor,
        mensagem=payload.mensagem,
        status=models.PaymentStatus.confirmado,
    )
    db.add(pix_txn)

    # Extrato remetente
    db.add(models.Transaction(
        account_id=account.id,
        tipo=models.TransactionType.debito,
        valor=payload.valor,
        descricao=payload.mensagem or f"Pix enviado → {payload.chave}",
        categoria="pix",
    ))

    db.commit()
    db.refresh(pix_txn)
    return pix_txn


@router.get("/history", response_model=List[schemas.PixTransactionOut])
def pix_history(
    account: models.Account = Depends(get_current_account),
    db:      Session = Depends(get_db),
):
    """Histórico de Pix enviados."""
    return (
        db.query(models.PixTransaction)
        .filter(models.PixTransaction.account_id == account.id)
        .order_by(models.PixTransaction.created_at.desc())
        .all()
    )
