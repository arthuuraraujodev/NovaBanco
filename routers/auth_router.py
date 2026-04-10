import random
import string
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from auth import (
    hash_password, verify_password,
    create_access_token, get_current_user
)
import models
import schemas

router = APIRouter(prefix="/auth", tags=["Autenticação"])


def _gerar_numero_conta() -> str:
    """Gera número de conta aleatório no formato XXXXX-D."""
    numero = "".join(random.choices(string.digits, k=5))
    digito = str(sum(int(d) for d in numero) % 10)
    return f"{numero}-{digito}"


def _criar_pix_keys_padrao(db: Session, account: models.Account, user: models.User):
    """Cria chaves Pix padrão ignorando chaves já existentes."""
    candidatas = [
        (models.PixKeyType.cpf,   user.cpf),
        (models.PixKeyType.email, user.email),
    ]
    if user.telefone:
        candidatas.append((models.PixKeyType.telefone, user.telefone))

    for tipo, chave in candidatas:
        existe = db.query(models.PixKey).filter(models.PixKey.chave == chave).first()
        if not existe:
            db.add(models.PixKey(account_id=account.id, tipo=tipo, chave=chave))

    aleatoria = "-".join(
        "".join(random.choices(string.ascii_lowercase + string.digits, k=8))
        for _ in range(4)
    )
    db.add(models.PixKey(account_id=account.id, tipo=models.PixKeyType.aleatoria, chave=aleatoria))


@router.post("/register", response_model=schemas.TokenResponse, status_code=status.HTTP_201_CREATED)
def register(payload: schemas.RegisterRequest, db: Session = Depends(get_db)):
    """Cadastra novo usuário, cria conta corrente e chaves Pix padrão."""

    # Verifica duplicatas
    if db.query(models.User).filter(models.User.cpf == payload.cpf).first():
        raise HTTPException(status_code=409, detail="CPF já cadastrado")
    if db.query(models.User).filter(models.User.email == payload.email).first():
        raise HTTPException(status_code=409, detail="E-mail já cadastrado")

    # Cria usuário
    user = models.User(
        nome=payload.nome,
        sobrenome=payload.sobrenome,
        cpf=payload.cpf,
        email=payload.email,
        telefone=payload.telefone,
        data_nascimento=payload.data_nascimento,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    db.flush()  # obtém user.id antes do commit

    # Cria conta corrente com saldo inicial de R$1.000 (demonstração)
    account = models.Account(
        user_id=user.id,
        numero=_gerar_numero_conta(),
        saldo=1000.0,
    )
    db.add(account)
    db.flush()

    # Transação de boas-vindas
    db.add(models.Transaction(
        account_id=account.id,
        tipo=models.TransactionType.credito,
        valor=1000.0,
        descricao="Bônus de abertura de conta",
        categoria="bonus",
    ))

    # Chaves Pix padrão
    _criar_pix_keys_padrao(db, account, user)

    db.commit()

    token = create_access_token({"sub": user.id})
    return schemas.TokenResponse(access_token=token)


@router.post("/login", response_model=schemas.TokenResponse)
def login(payload: schemas.LoginRequest, db: Session = Depends(get_db)):
    """Login por CPF ou e-mail + senha. Retorna JWT."""

    # Busca por e-mail ou CPF
    user = (
        db.query(models.User)
        .filter(
            (models.User.email == payload.login) |
            (models.User.cpf   == payload.login)
        )
        .first()
    )

    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas"
        )

    if not user.ativo:
        raise HTTPException(status_code=403, detail="Conta desativada")

    token = create_access_token({"sub": user.id})
    return schemas.TokenResponse(access_token=token)


@router.get("/me", response_model=schemas.UserOut)
def me(current_user: models.User = Depends(get_current_user)):
    """Retorna dados do usuário autenticado."""
    return current_user
