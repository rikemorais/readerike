# readerike

> Transcrição de vídeos local e privada, powered by [OpenAI Whisper](https://github.com/openai/whisper) + FFmpeg.

---

## Arquitetura

O projeto segue **Clean Architecture** (Ports & Adapters / Hexagonal), garantindo que a lógica de negócio seja independente de tecnologias concretas.

```
┌─────────────────────────────────────────────────────────┐
│                        CLI (click)                       │
└────────────────────────┬────────────────────────────────┘
                         │ chama
┌────────────────────────▼────────────────────────────────┐
│              Use Case: TranscribeVideoUseCase            │
│         (orquestra o pipeline via injeção de deps)       │
└───────┬─────────────────────┬──────────────────┬────────┘
        │                     │                  │
   IAudioExtractor      ITranscriber    ITranscriptionRepository
        │                     │                  │
┌───────▼────────┐  ┌─────────▼──────┐  ┌───────▼──────────┐
│ FFmpegExtractor│  │WhisperTranscri-│  │FileTranscription │
│ (ffmpeg-python)│  │ber (local GPU) │  │Repository (.json)│
└────────────────┘  └────────────────┘  └──────────────────┘
```

### Camadas

| Camada | Localização | Responsabilidade |
|---|---|---|
| **Core / Domain** | `src/readerike/core/` | Entidades, Ports (interfaces), Use Cases. Zero dependências externas. |
| **Adapters** | `src/readerike/adapters/` | Implementações concretas dos ports (FFmpeg, Whisper, JSON). |
| **Infrastructure** | `src/readerike/infrastructure/` | Config via env vars, logging. |
| **CLI** | `src/readerike/cli/` | Ponto de entrada — usa `click` + `rich`. |

### Decisões Arquitetônicas

- **Dependency Inversion (DIP):** O use case depende apenas de abstrações (`IAudioExtractor`, `ITranscriber`, `ITranscriptionRepository`), não de implementações concretas. Isso facilita trocar Whisper por outra engine sem alterar o core.
- **Imutabilidade nas entidades:** `Video`, `Transcription` e `TranscriptionSegment` são `frozen=True` (Pydantic). Evita mutação acidental de estado.
- **Temp dir para áudio:** O áudio extraído vive em `tempfile.TemporaryDirectory()` — nunca polui o disco do usuário.
- **Modelo Whisper carregado uma vez:** O `WhisperTranscriber` carrega os pesos no `__init__`, reutilizando-os em chamadas batch.

---

## Pré-requisitos

- Python 3.10+
- FFmpeg instalado no sistema (`brew install ffmpeg` / `apt install ffmpeg`)
- (Opcional) GPU NVIDIA com CUDA para acelerar Whisper

---

## Instalação Local

```bash
# Clone o repositório
git clone https://github.com/rikemorais/readerike.git
cd readerike

# Crie e ative o virtualenv
python3 -m venv .venv
source .venv/bin/activate

# Instale com dependências de desenvolvimento
pip install -e ".[dev]"
```

---

## Uso via CLI

```bash
# Transcrever um vídeo (idioma auto-detectado)
readerike transcribe meu-video.mp4

# Especificar idioma e diretório de saída
readerike transcribe meu-video.mp4 --language pt --output-dir ./saida

# Escolher modelo Whisper (tiny | base | small | medium | large)
readerike transcribe meu-video.mp4 --model medium
```

O resultado é um arquivo `.json` salvo em `--output-dir` (padrão: mesma pasta do vídeo).

---

## Uso via Docker

```bash
# Build da imagem
docker compose build

# Criar pastas locais necessárias
mkdir -p videos output

# Copie seu vídeo para videos/
cp meu-video.mp4 videos/

# Transcrever
docker compose run readerike transcribe /videos/meu-video.mp4 --language pt

# O JSON de saída estará em output/
```

### Variáveis de ambiente Docker

| Variável | Padrão | Descrição |
|---|---|---|
| `VIDEOS_DIR` | `./videos` | Diretório local com vídeos a transcrever |
| `OUTPUT_DIR` | `./output` | Diretório local para JSONs de saída |
| `WHISPER_MODEL` | `base` | Modelo Whisper (tiny/base/small/medium/large) |
| `LOG_LEVEL` | `INFO` | Nível de log |

---

## Desenvolvimento

```bash
# Rodar todos os testes
make test

# Apenas unitários
make test-unit

# Apenas integração
make test-integration

# Lint + format
make lint

# Type check
make typecheck

# Verificação de segurança (bandit)
make security

# Tudo junto (CI local)
make lint typecheck test security
```

---

## Estrutura de Testes

```
tests/
├── conftest.py                    # Fixtures compartilhadas
├── unit/
│   ├── core/
│   │   ├── entities/
│   │   │   ├── test_video.py
│   │   │   └── test_transcription.py
│   │   └── use_cases/
│   │       └── test_transcribe_video.py
│   └── adapters/
│       ├── test_ffmpeg_extractor.py
│       ├── test_whisper_transcriber.py
│       └── test_file_repository.py
└── integration/
    └── test_transcription_pipeline.py
```

---

## CI/CD (GitHub Actions)

| Workflow | Trigger | Jobs |
|---|---|---|
| `ci.yml` | Push / PR em `main` ou `develop` | lint, typecheck, unit tests (py 3.10/3.11/3.12), integration tests, security scan, docker build |
| `release.yml` | Push de tag `v*.*.*` | build + publish no PyPI, Docker image no GHCR |

---

## Formatos de Saída

Cada transcrição gera um JSON com esta estrutura:

```json
{
  "video_path": "/videos/meu-video.mp4",
  "language": "pt",
  "model": "base",
  "created_at": "2024-01-01T12:00:00+00:00",
  "word_count": 42,
  "text": "Transcrição completa do vídeo aqui...",
  "segments": [
    { "start": 0.0, "end": 3.5, "text": "Primeiro segmento." },
    { "start": 3.5, "end": 7.2, "text": "Segundo segmento." }
  ]
}
```

---

## Licença

MIT
