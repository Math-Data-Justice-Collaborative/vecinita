# PgAdmin

PostgreSQL management UI deployed as a Render private service.

## Runtime

- Docker image: `dpage/pgadmin4`
- Deploy target: Render private service (not publicly accessible)
- Access: Internal via Render network only

## Configuration

Server configuration for connecting to the Vecinita PostgreSQL instance
lives in `config/`. See the `docker-compose.yml` for local development setup.
