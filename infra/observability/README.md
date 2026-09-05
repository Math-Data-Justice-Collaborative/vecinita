# Staging observability (F84 / ADR-055)

Privacy-safe **Grafana + Loki + Alloy + Prometheus + Alertmanager** for **staging
only**. Admin product metrics remain on `/monitoring` (M138); this stack does not
replace AC-MON1–5.

**Do not** point production log shippers at this Loki. **Do not** enable live prod
corpus mutate from monitoring tools.

[Corpus: feature-list.md §F84]
[Spec: docs/adr/ADR-055-operational-monitoring-grafana-loki.md]
[Corpus: staging]

## Host

| Item | Value |
|------|--------|
| Droplet | `s-1vcpu-1gb` (ADR-004 cost) |
| Compose | this directory |
| Ports (loopback on Droplet; tunnel or reverse-proxy as needed) | Grafana `3000`, Loki `3100`, Prometheus `9090`, Alertmanager `9093`, Alloy UI `12345` |

## Image pins

| Service | Image |
|---------|--------|
| Grafana | `grafana/grafana:11.6.1` |
| Loki | `grafana/loki:3.4.2` |
| Alloy | `grafana/alloy:v1.8.3` |
| Prometheus | `prom/prometheus:v2.55.1` |
| Alertmanager | `prom/alertmanager:v0.28.1` |

Also listed in `docs/dependency-inventory.md` §EV-036.

## Secrets (staging only)

| Env | Purpose |
|-----|---------|
| `GRAFANA_ADMIN_PASSWORD` | Grafana admin password (required) |
| `GRAFANA_ADMIN_USER` | Default `admin` |
| `VECINITA_GRAFANA_URL` | Public root URL for Grafana links |
| `VECINITA_ALERTMANAGER_WEBHOOK_URL` | Alertmanager receiver webhook |

Copy `.env.example` → `.env` on the Droplet (gitignored locally if you create one).

### Render Alertmanager webhook

`alertmanager.yml` ships with a local sink URL. Before starting in staging:

```bash
export VECINITA_ALERTMANAGER_WEBHOOK_URL='https://hooks.example/staging'
# Option A: sed in place on the Droplet (keep a pristine copy)
sed "s|http://127.0.0.1:9/dev-null|${VECINITA_ALERTMANAGER_WEBHOOK_URL}|g" \
  alertmanager.yml > alertmanager.rendered.yml
# Point compose volume at alertmanager.rendered.yml, or overwrite carefully.
```

## Bring up

```bash
cd infra/observability
cp .env.example .env   # edit passwords + webhook
docker compose up -d
docker compose ps
```

## Smoke checklist (TC-305 / TC-306)

See [CHECKLIST-tc305-tc306.md](CHECKLIST-tc305-tc306.md).

## Privacy

- Loki retention **168h** (`loki-config.yaml`).
- Alloy `loki.process` drops/redacts `question` / `answer` / `prompt` / `message` /
  `raw_prompt` (F17 / ADR-004).
- Alert annotations use service/job labels only — never chat text.
- App logs must continue using `JsonLogFormatter` (`packages/shared-schemas/.../observability.py`).

## Prometheus targets

Edit `prometheus/prometheus.yml` scrape `targets` to real staging DO hostnames
(`/health`). Placeholder hosts keep compose valid offline; replace before relying on
`VecinitaStagingTargetDown` / ingest absence alerts.
