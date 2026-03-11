# Deployment Guide

## DNS Setup

| Hostname | Points to |
|----------|-----------|
| `jmpd.sh` | blog server public IP |
| `analytics.jmpd.sh` | shared server public IP |
| `grafana.jmpd.sh` | shared server public IP |
| `traefik.jmpd.sh` | shared server public IP (optional — restrict access) |

## Shared Server Deploy

Runs Umami, Grafana, Prometheus, Loki, and Traefik for the shared domain.

```bash
ssh deploy@<shared-ip>
cd /opt/shared
docker compose -f compose.yml -f compose.traefik.yml up -d
```

## Blog Server Deploy

Runs the FastAPI backend with its own Traefik instance. Umami services are excluded — they live on the shared server.

```bash
ssh deploy@<blog-ip>
cd /opt/blog
docker compose -f compose.yml -f compose.traefik.yml up -d
```

Do not pass `--profile local`. The `umami` and `umami-db` services will not start.

## Local Development

```bash
docker compose --profile local up -d
```

The `local` profile starts `umami` and `umami-db` alongside the rest of the stack so analytics can be tested locally.

## Environment Variables (production differences)

These differ from the defaults in `.env`:

| Variable | Production value |
|----------|-----------------|
| `UMAMI_HOST` | `https://analytics.jmpd.sh` |
| `OTEL_ENABLED` | `true` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | `http://10.0.1.1:4317` |
| `ENVIRONMENT` | `production` |
| `DOMAIN` | `jmpd.sh` |

## Verification Checklist

1. `curl https://jmpd.sh` returns the blog homepage
2. `curl https://analytics.jmpd.sh` returns the Umami login page
3. `curl https://grafana.jmpd.sh` returns the Grafana login page
4. In Grafana, confirm data sources: Prometheus and Loki are reachable
5. In Umami, confirm page views are being recorded
