# PVShop – Backend

Django/DRF/adrf-API für den Shop (siehe `docs/architecture/` für ADRs und
Architekturüberblick).

## Setup

```bash
uv sync
cp ../.env.example ../.env   # Werte anpassen
uv run python manage.py migrate
uv run python manage.py createsuperuser
uv run python manage.py runserver
```

Postgres und Redis lokal per Docker Compose starten (aus dem Projekt-Root):

```bash
docker compose up -d db redis
```

## Tests, Linting, Typprüfung

```bash
uv run pytest
uv run black .
uv run ruff check .
uv run mypy .
```

`CELERY_TASK_ALWAYS_EAGER` wird für Testläufe automatisch über `conftest.py`
auf `True` gesetzt – Celery-Tasks laufen dabei synchron im Testprozess,
ohne dass ein Redis-Broker/Worker laufen muss.

## Rechnungs-PDF (WeasyPrint)

Rechnungen werden bei Zahlungseingang automatisch als PDF gerendert
(`InvoiceService`, siehe ADR
[0009](../docs/architecture/decisions/0009-rechnungsmodell-nummernvergabe-und-erzeugungszeitpunkt.md)/
[0010](../docs/architecture/decisions/0010-rechnung-pdf-generierung.md)).
Dafür nutzt das Backend [WeasyPrint](https://weasyprint.org/), das native
Systembibliotheken (Pango, HarfBuzz, Fontconfig) benötigt – diese sind
**nicht** über `uv sync`/PyPI installierbar und müssen einmalig pro Umgebung
über den Systempaketmanager eingerichtet werden:

```bash
# Debian/Ubuntu
sudo apt install libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0

# macOS
brew install pango
```

Ohne diese Pakete schlägt der Import von `weasyprint` bzw. die
PDF-Erzeugung fehl.

## Celery (asynchroner Rechnungsversand per E-Mail)

Der E-Mail-Versand der Rechnung (siehe ADR
[0011](../docs/architecture/decisions/0011-rechnung-e-mail-versand.md))
läuft über einen Celery-Task, entkoppelt vom Request-/Webhook-Zyklus.
Dafür wird ein laufender Redis-Broker sowie ein Celery-Worker-Prozess
benötigt:

```bash
# Redis (falls nicht bereits über docker compose gestartet)
docker compose up -d redis

# Worker
uv run celery -A config worker -l info

# Optional: Monitoring-UI für die Task-Queue
uv run celery -A config flower
```

Für lokale Entwicklung ohne laufenden Worker kann `CELERY_TASK_ALWAYS_EAGER=True`
in `.env` gesetzt werden – Tasks laufen dann synchron im selben Prozess.
