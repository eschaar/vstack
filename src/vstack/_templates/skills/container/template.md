{{SKILL_CONTEXT}}

# container — Dockerfile & Compose

Write production-grade container configuration for the service.

## Out of scope

- CI/CD pipeline configuration (use `cicd`)
- Kubernetes manifests (use `cicd`)
- Application code changes (engineering role)

______________________________________________________________________

## Step 1: Detect context

```bash
# Detect runtime
ls pyproject.toml requirements.txt package.json go.mod Cargo.toml pom.xml 2>/dev/null | head -5

# Detect existing container config
ls Dockerfile* docker-compose* .dockerignore 2>/dev/null || echo "No container config found"
```

______________________________________________________________________

## Step 2: Dockerfile

Write a multi-stage `Dockerfile` following these rules:

**Base image:**

- Use an official, minimal image: `python:3.12-slim`, `node:22-alpine`, `golang:1.22-alpine`, etc.
- Never use `latest` — pin to a specific version tag
- Prefer `alpine` or `slim` variants for production stage

**Multi-stage build:**

```dockerfile
# Stage 1: build / install dependencies
FROM <runtime>:<version> AS builder
WORKDIR /app
COPY <dependency files> .
RUN <install deps>

# Stage 2: production image
FROM <runtime>:<version>-slim AS runtime
WORKDIR /app
COPY --from=builder /app /app
```

**Security hardening:**

- Run as non-root user:

  ```dockerfile
  RUN addgroup --system app && adduser --system --ingroup app app
  USER app
  ```

- Drop capabilities where applicable

- No secrets in image layers — use environment variables or mounted secrets at runtime

- Set `HEALTHCHECK` instruction

**Layer optimisation:**

- Copy dependency files first, then source (cache busting only on source change)
- Combine `RUN` steps with `&&` to minimise layers
- Add `.dockerignore` excluding: `.git`, `node_modules`, `__pycache__`, `*.pyc`, `dist`, `build`, local env files

**Port and entrypoint:**

```dockerfile
EXPOSE <port>
ENTRYPOINT ["<executable>"]
CMD ["<default args>"]
```

______________________________________________________________________

## Step 3: docker-compose.yml (local dev)

Write `docker-compose.yml` for local development:

```yaml
services:
  app:
    build: .
    ports:
      - "<host>:<container>"
    environment:
      - <ENV_VAR>=<value>
    depends_on:
      - <dependency>
    volumes:
      - .:/app          # hot-reload in dev only — remove for prod

  # Add dependencies: database, cache, broker
  # db:
  #   image: postgres:16-alpine
  # cache:
  #   image: redis:7-alpine
```

For production-like local testing, write a separate `docker-compose.prod.yml` without volume mounts.

______________________________________________________________________

## Step 4: Review checklist

- [ ] No `latest` tags
- [ ] Multi-stage build — production image contains no build tools
- [ ] Non-root user
- [ ] `.dockerignore` present and complete
- [ ] No secrets baked into image
- [ ] `HEALTHCHECK` defined
- [ ] Image builds successfully: `docker build -t app:local .`
- [ ] Container starts and responds: `docker run --rm -p <port>:<port> app:local`

______________________________________________________________________
