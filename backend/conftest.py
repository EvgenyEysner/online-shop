import os

# Muss gesetzt sein, bevor Django/pytest-django die Settings laden (siehe
# config/settings.py: CELERY_TASK_ALWAYS_EAGER liest diese Env-Var). Tests
# laufen so ohne laufenden Celery-Worker/Redis-Broker der Task wird
# synchron im Testprozess ausgeführt.
os.environ.setdefault("CELERY_TASK_ALWAYS_EAGER", "True")
