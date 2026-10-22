# QuizForge

Aplikacja webowa do tworzenia i przeprowadzania quizów, z pytaniami generowanymi przez AI z materiałów
użytkownika, oraz narzędzie do porównywania modeli i strategii generowania pytań. Praca inżynierska.

## Wymagania

- Docker Desktop
- Python 3.13 i [uv](https://docs.astral.sh/uv/) (`pip install uv`, potem `uv` albo `python -m uv`)
- Node.js 24

## Pierwsze uruchomienie

```bash
cp .env.example .env
docker compose up -d
cd backend
uv sync
uv run alembic upgrade head
cd ../frontend
npm install
```

## Praca na co dzień

| Co | Gdzie | Komenda |
|---|---|---|
| Bazy i usługi | główny folder | `docker compose up -d` |
| Backend (http://localhost:8000) | `backend/` | `uv run uvicorn app.main:app --reload` |
| Frontend (http://localhost:5173) | `frontend/` | `npm run dev` |
| Testy backendu | `backend/` | `uv run pytest` |
| Lint backendu | `backend/` | `uv run ruff check .` i `uv run ruff format .` |
| Testy frontendu | `frontend/` | `npm test` |
| Lint frontendu | `frontend/` | `npm run lint` i `npm run format` |
| Nowa migracja | `backend/` | `uv run alembic revision --autogenerate -m "opis"` |

Usługi pomocnicze: podgląd poczty Mailpit http://localhost:8025, podgląd bazy Adminer http://localhost:8080
(system: PostgreSQL, serwer: `db`, dane z `.env`). Dokumentacja API: http://localhost:8000/docs.

## Struktura

```
backend/            FastAPI (Python)
  app/              kod: config, db, auth, quizzes, ai, learn, modes, common
  migrations/       migracje Alembic
  tests/
frontend/           React + TypeScript + Vite + Tailwind
  src/              pages, components, api, hooks, lib, locales, modes, styles, assets
tools/forgepixel/   źródła fontu pikselowego ForgePixel (python build.py)
research/           analiza wyników badań
```
