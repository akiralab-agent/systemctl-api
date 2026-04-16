# Systemctl API

API em FastAPI para listar services conhecidos pelo systemd e executar comandos
controlados em um service via `systemctl`.

## Requisitos

- Python 3.10+
- Linux com `systemctl`
- Permissão do usuário que executa a API para chamar os comandos desejados

## Instalação

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edite o arquivo `.env` e defina a chave:

```env
SECRET_KEY=sua-chave-secreta
```

## Executar

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Instalar como serviço no Ubuntu

O script abaixo cria o virtualenv, instala as dependências, cria `.env` se ele
não existir, registra o serviço no systemd e sobe a API na porta `51000`.

```bash
sudo ./scripts/install-systemd-service.sh
```

Por padrão, o serviço será criado com o nome `systemctl-api` e rodará como
`root`, porque a API executa comandos `systemctl`. Para sobrescrever:

```bash
sudo SERVICE_NAME=systemctl-api PORT=51000 SERVICE_USER=root \
  ./scripts/install-systemd-service.sh
```

Comandos úteis:

```bash
systemctl status systemctl-api
journalctl -u systemctl-api -f
systemctl restart systemctl-api
```

## Autenticação

Envie a chave no header `Authorization`:

```bash
Authorization: sua-chave-secreta
```

## Endpoints

### Health check

```bash
curl http://localhost:8000/health
```

### Listar services

Equivalente a:

```bash
systemctl list-units --type=service --all --no-pager
```

Request:

```bash
curl -H "Authorization: sua-chave-secreta" \
  http://localhost:8000/services
```

### Executar comando em um service

Equivalente a:

```bash
systemctl restart django.service
```

Request:

```bash
curl -X POST http://localhost:8000/services/command \
  -H "Authorization: sua-chave-secreta" \
  -H "Content-Type: application/json" \
  -d '{"action":"restart","service":"django"}'
```

Ações permitidas:

- `start`
- `stop`
- `restart`
- `reload`
- `enable`
- `disable`
- `status`
