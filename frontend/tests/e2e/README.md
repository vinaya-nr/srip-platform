# Playwright E2E Suite

## Install

```bash
cd frontend
npm install
npm run test:e2e:install
```

## Environment

```bash
# optional overrides
E2E_FRONTEND_URL=http://localhost:3000
E2E_API_BASE_URL=http://localhost:8000/api/v1
E2E_PASSWORD=Passw0rd!123
```

## Run

```bash
npm run test:e2e
```

## Structure

```
tests/e2e/
  pom/               # page objects
  setup/             # storage state bootstrap
  utils/             # API client + auth/session helpers
  *.spec.ts          # feature/domain specs
```
