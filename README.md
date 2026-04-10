# 🏛 NovaBanco — Back-end FastAPI

Back-end completo do sistema bancário NovaBanco.  
**Stack:** Python · FastAPI · SQLite · SQLAlchemy · JWT (python-jose) · Passlib (bcrypt)

---

## 📁 Estrutura do projeto

```
novabanco/
├── main.py                  # Ponto de entrada FastAPI + CORS + routers
├── database.py              # Conexão SQLite e SessionLocal
├── models.py                # Modelos ORM (User, Account, Transaction, ...)
├── schemas.py               # Schemas Pydantic (request/response)
├── auth.py                  # JWT: criar/decodificar token, dependências
├── routers/
│   ├── auth_router.py       # POST /auth/register  POST /auth/login  GET /auth/me
│   ├── accounts_router.py   # GET /accounts/me  GET /accounts/transactions  GET /accounts/summary
│   ├── payments_router.py   # POST /payments  GET /payments  GET /payments/{id}
│   ├── transfers_router.py  # POST /transfers  GET /transfers  GET /transfers/{id}
│   ├── pix_router.py        # GET /pix/keys  POST /pix/send  GET /pix/history
│   └── loans_router.py      # POST /loans  GET /loans  GET /loans/simulate  GET /loans/{id}
├── static/
│   └── index.html           # Front-end integrado com a API
└── requirements.txt
```

---

## 🚀 Como rodar

### 1. Crie o ambiente virtual
```bash
python -m venv venv
source venv/bin/activate        # Linux/Mac
venv\Scripts\activate           # Windows
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Inicie o servidor
```bash
python main.py
# ou
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Acesse

| URL | Descrição |
|-----|-----------|
| `http://localhost:8000` | Front-end (index.html) |
| `http://localhost:8000/docs` | Swagger UI interativo |
| `http://localhost:8000/redoc` | ReDoc — documentação completa |
| `http://localhost:8000/health` | Health check |

> **Nota:** O banco de dados `novabanco.db` é criado automaticamente na primeira execução.

---

## 🔐 Autenticação JWT

Todas as rotas protegidas exigem o header:
```
Authorization: Bearer <token>
```

O token é retornado no login e tem validade de **24 horas**.

### Fluxo
```
POST /auth/register  →  { access_token }
POST /auth/login     →  { access_token }
GET  /auth/me        →  dados do usuário  [requer token]
```

---

## 📡 Endpoints

### Conta
```
GET /accounts/me            → saldo, agência, número, dados do usuário
GET /accounts/transactions  → extrato (limit, offset)
GET /accounts/summary       → entradas, saídas e saldo do mês
```

### Pagamentos
```
POST /payments              → realiza pagamento (debita saldo)
GET  /payments              → lista pagamentos
GET  /payments/{id}         → detalhe de um pagamento
```

### Transferências
```
POST /transfers             → envia TED ou DOC (debita saldo)
GET  /transfers             → lista transferências
GET  /transfers/{id}        → detalhe de uma transferência
```

### Pix
```
GET  /pix/keys              → lista chaves Pix ativas
POST /pix/send              → envia Pix (debita + credita se conta interna)
GET  /pix/history           → histórico de Pix enviados
```

### Empréstimos
```
POST /loans                 → solicita empréstimo (crédito automático na demo)
GET  /loans                 → lista empréstimos
GET  /loans/simulate        → simula parcela sem autenticação
GET  /loans/{id}            → detalhe de um empréstimo
```

---

## 💡 Destaques técnicos

- **Fórmula Price** no cálculo de parcelas: `PMT = PV * [r(1+r)^n] / [(1+r)^n - 1]`
- **Pix interno**: se a chave destino pertencer a uma conta NovaBanco, o crédito é feito automaticamente
- **Saldo inicial**: R$ 1.000,00 ao criar conta (modo demo)
- **Chaves Pix automáticas**: CPF, e-mail, telefone e chave aleatória criadas no cadastro
- **CORS aberto** para facilitar desenvolvimento local (restrinja em produção)
- **SQLite**: banco criado automaticamente, sem instalação adicional

---

## 🧪 Exemplo de uso com curl

```bash
# Registrar
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"nome":"João","sobrenome":"Silva","cpf":"123.456.789-00","email":"joao@email.com","password":"senha123"}'

# Login
TOKEN=$(curl -s -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"login":"joao@email.com","password":"senha123"}' | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Ver conta
curl http://localhost:8000/accounts/me -H "Authorization: Bearer $TOKEN"

# Enviar Pix
curl -X POST http://localhost:8000/pix/send \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"chave_tipo":"email","chave":"outro@email.com","valor":50.00,"mensagem":"Almoço"}'
```
