# vulne

## n8n

This repo includes a Docker Compose setup for running [n8n](https://n8n.io/), a workflow
automation tool.

### Prerequisites

- Docker and the Docker Compose plugin installed.

### Setup

1. Copy the example environment file and set your own credentials:

   ```bash
   cp .env.example .env
   ```

2. Start n8n:

   ```bash
   docker compose up -d
   ```

3. Open [http://localhost:5678](http://localhost:5678) and log in with the
   `N8N_BASIC_AUTH_USER` / `N8N_BASIC_AUTH_PASSWORD` you set in `.env`.

Workflow data is persisted in the `n8n_data` Docker volume, so it survives
container restarts.

### Stopping

```bash
docker compose down
```
