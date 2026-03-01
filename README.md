# readerike

Transcrição de vídeos local e privada, powered by [OpenAI Whisper](https://github.com/openai/whisper) + FFmpeg.

Upload um vídeo → receba texto, SRT e JSON. Tudo roda na sua máquina, nada vai para nuvem.

---

## Rodando com Docker

**Pré-requisito:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) instalado.

```bash
git clone https://github.com/rikemorais/readerike.git
cd readerike
mkdir -p data
docker compose up --build
```

Aguarde o build (~2 min na primeira vez). Quando estiver pronto:

| Serviço | URL |
|---|---|
| Interface web | http://localhost:3000 |
| API / Swagger | http://localhost:8000/docs |

Para parar: `Ctrl+C` → `docker compose down`

---

## Uso

1. Abra http://localhost:3000
2. Arraste um vídeo (MP4, MOV, MKV, AVI ou WebM) ou clique em **Browse**
3. Escolha o idioma e o modelo Whisper
4. Clique em **Transcribe** e acompanhe o progresso em tempo real
5. Quando concluir, leia o transcript sincronizado com o vídeo e exporte em **JSON**, **TXT** ou **SRT**

### Modelos Whisper

| Modelo | RAM | Velocidade | Qualidade |
|---|---|---|---|
| `tiny` | ~1 GB | ⚡⚡⚡ | ★★☆ |
| `base` | ~1 GB | ⚡⚡⚡ | ★★★ |
| `small` | ~2 GB | ⚡⚡ | ★★★★ |
| `medium` | ~5 GB | ⚡ | ★★★★★ |
| `large` | ~10 GB | 🐢 | ★★★★★ |

O padrão é `base`. Para mudar:

```bash
WHISPER_MODEL=small docker compose up
```

---

## Variáveis de ambiente

Crie um arquivo `.env` na raiz do projeto para sobrescrever os padrões:

```env
WHISPER_MODEL=base
LOG_LEVEL=INFO
CORS_ORIGINS=["http://localhost:3000"]
```

| Variável | Padrão | Descrição |
|---|---|---|
| `WHISPER_MODEL` | `base` | Modelo Whisper |
| `LOG_LEVEL` | `INFO` | Nível de log (`DEBUG`, `INFO`, `WARNING`) |
| `CORS_ORIGINS` | `["http://localhost:3000"]` | Origens permitidas no CORS (JSON array) |

---

## Arquitetura

O projeto segue **Clean Architecture** (Ports & Adapters):

```
┌──────────────────────────────────────────────┐
│           API (FastAPI) + CLI (click)         │
└──────────────────────┬───────────────────────┘
                       │
┌──────────────────────▼───────────────────────┐
│         Use Case: TranscribeVideoUseCase      │
└───────┬──────────────┬───────────────┬───────┘
        │              │               │
  IAudioExtractor  ITranscriber  ITranscriptionRepository
        │              │               │
  FFmpegExtractor  WhisperTranscriber  FileRepository / SQLiteJobRepository
```

| Camada | Localização | Responsabilidade |
|---|---|---|
| Core | `src/readerike/core/` | Entidades, ports, use cases. Zero deps externas. |
| Adapters | `src/readerike/adapters/` | FFmpeg, Whisper, SQLite, JSON. |
| Infrastructure | `src/readerike/infrastructure/` | Config via env vars, logging. |
| API | `src/readerike/api/` | FastAPI, WebSocket, schemas. |
| CLI | `src/readerike/cli/` | Interface de linha de comando. |
| Frontend | `frontend/` | Next.js 14, Tailwind CSS, TypeScript. |

---

## Desenvolvimento

```bash
# Instalar dependências Python (requer Python 3.10+, FFmpeg e Whisper)
pip install -e ".[dev]"

# Rodar testes
make test          # todos
make test-unit     # só unitários (sem FFmpeg/Whisper)

# Lint, tipos e segurança
make lint
make typecheck
make security

# API local (porta 8000)
make api-dev

# Frontend local (porta 3000)
make frontend-dev
```

---

## Licença

MIT
