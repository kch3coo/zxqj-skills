---
name: yudao-port-isolation
description: Prepare a local Yudao/ruoyi-vue-pro style multi-service project to run beside other already-running systems by detecting port conflicts and editing only local development configuration. Use when a user wants to run another system that may conflict on Docker MySQL, Docker Redis, backend server ports, frontend dev-server ports, or frontend-to-backend API endpoints, especially projects with docker-compose files, application-local.yaml/yml, Vite env files, or similar local config. Do not start the system or commit changes unless the user explicitly asks for a commit.
---

# Yudao Port Isolation

## Overview

Modify a project's local development ports so it can run alongside other systems on the same machine. Prefer targeted edits to Docker Compose, backend local profile config, and frontend local env/config files; do not start services.

## Workflow

### 1. Locate Config

From the project root, find likely files:

```powershell
rg --files -g "*docker-compose*" -g "application-local.y*ml" -g "application*.y*ml" -g ".env*" -g "vite.config.*" -g "package.json"
```

Open only the most relevant files first:

- Docker Compose under backend script/docker, deploy, or sql/tools directories.
- Backend `application-local.yaml` or `application-local.yml`.
- Frontend `.env.local`, `.env.development`, `.env.dev`, `vite.config.ts/js`, and `package.json`.

Prefer local config files over shared dev/prod files. If there is no local file, create or modify the least risky local override that the project already supports.

### 2. Detect Existing Conflicts

Check ports already in use before choosing replacements:

```powershell
docker ps --format "table {{.Names}}\t{{.Ports}}"
Get-NetTCPConnection -State Listen | Select-Object LocalAddress,LocalPort,OwningProcess | Sort-Object LocalPort
```

For a narrower check, query likely ports:

```powershell
Get-NetTCPConnection -State Listen -LocalPort 3306,3307,3310,3311,6379,6380,6381,48080,48081,8080,8081,8090,5173,5174,5175 -ErrorAction SilentlyContinue
```

Also inspect the target project's current declared ports:

```powershell
rg -n "3306|6379|server:\s*$|port:|datasource|redis|VITE_PORT|VITE_BASE_URL|VITE_API|proxy|target|localhost|127\.0\.0\.1"
```

### 3. Choose a Port Set

Pick a coherent unused set for the target system. Keep container-internal ports unchanged and only change host mappings and local clients.

Common default:

```text
MySQL host port: 3310 -> container 3306
Redis host port: 6380 -> container 6379
Backend: 48081 or 8090
Frontend: 5174
```

If those are occupied, increment predictably: MySQL `3311`, Redis `6381`, backend `48082`, frontend `5175`.

### 4. Edit Docker Compose

In the target project's Docker Compose file, change host ports only:

```yaml
services:
  mysql:
    ports:
      - "3310:3306"
  redis:
    ports:
      - "6380:6379"
```

Do not change the right side unless the container itself is intentionally reconfigured.

If Compose also includes Adminer, EMQX, MQTT, app containers, simulators, or other services with exposed host ports, check and adjust those too when they conflict.

### 5. Edit Backend Local Config

In `application-local.yaml` or `application-local.yml`, update:

```yaml
server:
  port: 48081

spring:
  datasource:
    dynamic:
      datasource:
        master:
          url: jdbc:mysql://127.0.0.1:3310/<database>
        slave:
          url: jdbc:mysql://127.0.0.1:3310/<database>
  data:
    redis:
      host: 127.0.0.1
      port: 6380
```

Adapt the exact property names to the project:

- `spring.datasource.dynamic.datasource.*.url` for dynamic-datasource projects.
- `spring.datasource.url` for ordinary Spring Boot projects.
- `spring.data.redis.*` for newer Spring Boot.
- `spring.redis.*` for older Spring Boot.

Confirm the backend actually activates the local profile, usually in `application.yaml`:

```yaml
spring:
  profiles:
    active: local
```

If not, update the IDE/run arguments only when the project stores them in versioned or local run configuration files; otherwise tell the user what argument to use, such as `--spring.profiles.active=local`.

### 6. Edit Frontend Local Config

For Vite projects, prefer `.env.local` or the env file used by the `dev` script. Update both the frontend dev-server port and the backend API base:

```env
VITE_PORT=5174
VITE_BASE_URL='http://localhost:48081'
```

If the project uses a proxy in `vite.config.ts/js`, update the proxy target:

```ts
server: {
  port: Number(env.VITE_PORT) || 5174,
  proxy: {
    '/admin-api': {
      target: env.VITE_BASE_URL
    }
  }
}
```

If `vite.config` already reads `env.VITE_PORT`, only setting `VITE_PORT` is enough.

### 7. Validate Without Starting

Do not run `docker compose up`, backend applications, or frontend dev servers. Validation should be static:

```powershell
docker compose -f <compose-file> config
git diff -- <edited-files>
git status --short -- <edited-files>
```

Use `docker compose config` only to validate Compose syntax and port mappings. A warning that Compose `version` is obsolete is not a blocker.

## Git Safety

Never commit local project port changes unless the user explicitly asks. Do not stage files during ordinary port-isolation work. If the user says "do not add to Git", interpret it as no `git add` and no commit; the working tree may still show modified files.

When possible, use local-only files that are already ignored, such as `.env.local`. If a required local config file is tracked, modify it only because the user asked for local machine configuration and report the exact files changed.

Do not create upgrade SQL or rollback SQL while making SQL-adjacent project configuration changes.

## Final Response

Report the resulting mapping and changed files. Include the exact commands the user should run if they want to start it later, but make clear that you did not start the system.
