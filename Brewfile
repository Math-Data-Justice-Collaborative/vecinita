# Vecinita local macOS dependencies (Homebrew Bundle).
# Install:  brew bundle --no-upgrade
# Check:    brew bundle check
#
# Exact versions below are the verified pins for this file (Homebrew is
# rolling-release and cannot install arbitrary older bottles; use
# `brew bundle --no-upgrade` so already-installed kegs are not upgraded).
#
# Runtime: Colima (no Docker Desktop). After install: colima start && make db-ready

# --- Container runtime (Postgres via infra/docker-compose.yml) ---
brew "colima"          # =0.10.3
brew "docker"          # =29.7.1
brew "docker-compose"  # =5.4.0
brew "lima"            # =2.2.0  (colima runtime dep; keep explicit)

# --- Language / package tooling (docs/LOCAL_DEV.md) ---
brew "uv"              # =0.12.1
brew "fnm"             # =1.39.0

# --- Repo scripts / ops CLI ---
brew "jq"              # =1.8.2
brew "gh"              # =2.97.0
# Supabase Auth config / migrations (supabase/README.md, ADR-027)
brew "supabase"        # =2.111.0
