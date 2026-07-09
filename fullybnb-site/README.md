# Fully BnB Site

Single-page React site for 埔里富莉庭緣民宿.

## Local Development

```bash
npm install
npm run dev
```

By default, Vite proxies `/api/public` to `http://localhost:5001`.
To use the real backend locally through Docker:

```bash
cd ..
cp .env.local.template .env.local # first time only
docker compose --env-file .env.local -f docker-compose.yaml -f docker-compose.local.yaml up -d --build local-db line-bot-server
curl http://localhost:5001/health
cd fullybnb-site
npm run dev
```

The local compose override starts a dedicated Postgres container on host port `5433`,
initializes it from `db/sql`, and forces the backend to connect to that container
instead of any production database.

## E2E Tests

The e2e tests use the real backend at `http://localhost:5001` and do not create reservations.

```bash
npm run test:e2e:install
npm run test:e2e
```

Override endpoints when needed:

```bash
E2E_API_BASE_URL=http://localhost:5001 E2E_BASE_URL=http://localhost:5174 npm run test:e2e
```

## Production Build

```bash
npm run build
```

The Docker image builds the Vite app and serves the static output with nginx.
