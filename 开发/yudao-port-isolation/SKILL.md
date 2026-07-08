---
name: yudao-port-isolation
description: Use when a local Yudao/ruoyi-vue-pro style project must run beside other systems and may conflict on Docker MySQL, Redis, EMQX/MQTT, Adminer, simulators, backend server ports, frontend dev-server ports, or API base URLs.
---

# Yudao Port Isolation

## Overview

Modify local development ports so one or more Yudao-style systems can run on the same machine. Prefer targeted edits to the actual Docker Compose file the user will run, backend local profile config, frontend/mobile local env files, and gateway/simulator local config. Do not start services unless the user explicitly asks.

## Workflow

### 1. Confirm the Actual Target Path

If the user provides a command, path, or error log with `docker compose -f <file>`, treat that compose file as the primary target. Do not modify a same-named project elsewhere unless the user confirms it is the one they run.

When multiple copies of a project exist, list the candidates and choose only from evidence:

- Explicit user path or command.
- Current working directory or opened repo.
- Matching backend path such as `{project}-backend\script\docker\docker-compose.yml`.
- Recent failure path in Docker output.

Before editing, state the exact compose path you will modify. If the actual path is unknown and multiple candidates exist, ask for the path instead of guessing.

### 2. Locate Config

From the project root, find likely files:

```powershell
rg --files -g "*docker-compose*" -g "application-local.y*ml" -g "application*.y*ml" -g ".env*" -g "vite.config.*" -g "package.json" -g "pubspec.yaml"
```

Open only the most relevant files first:

- Primary Docker Compose: usually `{backend}\script\docker\docker-compose.yml`.
- Secondary DB-tool Compose: usually `{backend}\sql\tools\docker-compose.yaml`.
- Backend `application-local.yaml` or `application-local.yml`.
- Frontend `.env.local`, `.env.development`, `.env.dev`, `vite.config.ts/js`, and `package.json`.
- Mobile/uniapp/Flutter env files such as `env/.env.development` or root `.env`.
- IoT gateway, simulator, or plugin local YAML files that reference Redis, MQTT, EMQX, or the main backend URL.

Prefer local config files over shared dev/prod files. If there is no local file, create or modify the least risky local override that the project already supports.

### 3. Detect Existing Conflicts

Check ports already in use before choosing replacements:

```powershell
docker ps --format "table {{.Names}}\t{{.Ports}}"
Get-NetTCPConnection -State Listen | Select-Object LocalAddress,LocalPort,OwningProcess | Sort-Object LocalPort
```

For a narrower check, query likely ports:

```powershell
Get-NetTCPConnection -State Listen -LocalPort 3306,3310,3311,3312,3313,3314,6379,6380,6381,6382,6383,6384,48080,48081,48082,48083,48084,5173,5174,5175,5176,8080,8081,8083,8084,8085,8086,8087,8883,8884,18080,18081,18082,18083,18084,18085,38384,38385,38386,38387 -ErrorAction SilentlyContinue
```

Also inspect the target project's current declared ports:

```powershell
rg -n "3306|6379|1883|8083|8883|18083|18080|38384|server:\s*$|port:|datasource|redis|emqx|mqtt|simulator|VITE_PORT|VITE_BASE_URL|VITE_API|DEV_SERVER_IP|DEV_SERVER_PORT|PROD_SERVER_PORT|proxy|target|localhost|127\.0\.0\.1|10\.0\.2\.2"
```

### 4. Build a Port Matrix

For multiple systems, create a compact matrix before editing:

```text
System      MySQL  Redis  Backend  Frontend  Adminer  EMQX TCP/WS/Dashboard  Simulator
warden      3310   6380   48081    5174      38384    1883/8083/18083        18080
yian        3311   6381   48084    5175      38387    1885/8087/18085        18082
checknm     3312   6382   48082    5175      38385    1884/8085/18084        -
effy        3313   6383   48083    5176      38386    -                      -
```

Adapt the names and values to occupied ports, but keep each system's ports grouped and predictable. Keep container-internal ports unchanged; change host mappings and local clients.

Common single-system default:

```text
MySQL host port: 3310 -> container 3306
Redis host port: 6380 -> container 6379
Backend: 48081 or 8090
Frontend: 5174
Adminer host port: 38384 -> container 8080
EMQX host ports: 1883, 8083, 8084, 8883, 18083 -> same container ports
```

If those are occupied, increment predictably: MySQL `3311`, Redis `6381`, backend `48082`, frontend `5175`.

### 5. Edit Docker Compose

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

Scan every `ports:` block, not just MySQL and Redis. Change host ports for services such as:

- `adminer`: `38384:8080`, then increment for other systems.
- `emqx` or MQTT: change host `1883`, `8083`, `8084`, `8883`, and `18083` as a group.
- `server` app containers: align both host and container mapping with the backend `server.port`, or pass `--server.port=<port>` if the container uses `ARGS`.
- simulators: change host ports such as `18080:18080` when multiple systems expose the same simulator.

### 6. Edit Backend Local Config

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

Confirm the backend activates the local profile, usually in `application.yaml`:

```yaml
spring:
  profiles:
    active: local
```

If not, update the IDE/run arguments only when the project stores them in versioned or local run configuration files; otherwise tell the user what argument to use, such as `--spring.profiles.active=local`.

When the Docker Compose includes a backend `server` service, update the Compose runtime too:

```yaml
ports:
  - "48082:48082"
environment:
  ARGS:
    --server.port=48082
```

Keep container-to-container datasource and Redis URLs pointed at service names and internal ports, such as `mysql:3306` and `redis:6379`. Host port changes are for host-to-container access.

### 7. Edit Frontend, Mobile, and Gateway Local Config

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

For mobile or uniapp projects, update development-only env files:

```env
DEV_SERVER_IP=127.0.0.1
DEV_SERVER_PORT=48082
VITE_BASE_URL=http://localhost:48082
```

Do not change production variables unless the user explicitly asks.

For IoT gateway or simulator config, align references to:

- Main backend API URL, for example `http://127.0.0.1:48084`.
- Redis host port when it runs on the host.
- MQTT/EMQX host ports when the gateway connects through the host network.

### 8. Validate Without Starting

Do not run `docker compose up`, backend applications, or frontend dev servers. Validation should be static:

```powershell
docker compose -f <compose-file> config
docker compose -f <compose-file> config | Select-String -Pattern 'published: "6381"|published: "3311"'
git diff -- <edited-files>
git status --short -- <edited-files>
```

Use `docker compose config` to validate syntax and rendered port mappings. A warning that Compose `version` is obsolete is not a blocker.

If a previous `docker compose up` failed with "port is already allocated", check for a leftover created container:

```powershell
docker ps -a --filter name=<container-name> --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

If it exists, tell the user to recreate the service with `--force-recreate` or remove the created container. Do not remove containers automatically unless the user asks.

## Git Safety

Never commit local project port changes unless the user explicitly asks. Do not stage files during ordinary port-isolation work. If the user says "do not add to Git", interpret it as no `git add` and no commit; the working tree may still show modified files.

When possible, use local-only files that are already ignored, such as `.env.local`. If a required local config file is tracked, modify it only because the user asked for local machine configuration and report the exact files changed.

Do not create upgrade SQL or rollback SQL while making SQL-adjacent project configuration changes.

## Final Response

Report the resulting mapping and changed files. Include the exact commands the user should run if they want to start it later, but make clear that you did not start the system.
