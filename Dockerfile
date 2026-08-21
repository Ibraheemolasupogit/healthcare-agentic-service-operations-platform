# Engineering-baseline image for the Healthcare Agentic Service Operations
# Platform portfolio project.
#
# NOTE: Milestone 1 (Repository Foundation) has no runtime service to serve.
# This image exists to give CI/CD an environment for installing the project
# and running its automated tests reproducibly — it is not a production
# deployment artefact and implies no live service.

FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY . .

RUN pip install --upgrade pip \
    && pip install -e .[dev]

RUN python -m pytest -q

CMD ["python", "-c", "print('Healthcare Agentic Service Operations Platform — Milestone 1 foundation image. No runtime service is implemented in this milestone.')"]
