# GitHub Codespaces Secrets Setup Guide

This guide lists all secrets from `.env` that should be added to GitHub Codespaces for this repository.

## How to Add Secrets to GitHub Codespaces

1. Go to GitHub.com and click your **profile picture** (top right)
2. Click **Settings**
3. In the left sidebar under "Code, planning, and automation," click **Codespaces**
4. Click **New secret** button
5. For each secret below:
   - Enter the **Name** (exactly as listed)
   - Enter the **Value** (copy from your `.env` file)
   - Select **Repository access** and check `acadiagit/vecinita` (or your repo name)
   - Click **Add secret**

---

## Secrets to Add

### API Keys & Authentication

#### 1. GROQ_API_KEY
- **Current Value Location:** `.env` line with `GROQ_API_KEY=`
- **Purpose:** Groq LLM API key for generating responses
- **Rules:** Must not be shared; keep confidential

#### 2. OPEN_API_KEY
- **Current Value Location:** `.env` line with `OPEN_API_KEY=`
- **Purpose:** OpenAI API key for embeddings/LLM fallback
- **Rules:** Must not be shared; keep confidential
- **Optional:** Can be skipped if not using OpenAI

### LangSmith Configuration (Tracing & Monitoring)

#### 3. LANGSMITH_API_KEY
- **Current Value Location:** `.env` line with `LANGSMITH_API_KEY=`
- **Purpose:** LangSmith tracing and monitoring API key
- **Rules:** Must not be shared; keep confidential
- **Optional:** Can be skipped if not using LangSmith tracing

#### 4. LANGSMITH_PROJECT
- **Current Value Location:** `.env` line with `LANGSMITH_PROJECT=`
- **Purpose:** LangSmith project name for organizing traces
- **Example Value:** `pr-trustworthy-sundial-70`

### Supabase Configuration

#### 5. SUPABASE_URL
- **Current Value Location:** `.env` line with `SUPABASE_URL=`
- **Purpose:** Supabase instance URL for vector database
- **Format:** Must start with `https://`
- **Example:** `https://dosbzlhijkeircyainwz.supabase.co`

#### 6. SUPABASE_KEY
- **Current Value Location:** `.env` line with `SUPABASE_KEY=`
- **Purpose:** Supabase API key for authentication
- **Rules:** Must not be shared; keep confidential
- **Note:** This is the anon or service key

### Database Configuration

#### 7. DATABASE_URL
- **Current Value Location:** `.env` line with `DATABASE_URL=`
- **Purpose:** Direct PostgreSQL connection string for vector_loader.py and data scraping
- **Format:** Must start with `postgresql://`
- **Rules:** Must not be shared; keep confidential
- **Example:** `postgresql://postgres:password@db.xxxxx.supabase.co:5432/postgres?sslmode=require`

#### 8. DB_HOST
- **Current Value Location:** `.env` line with `DB_HOST=`
- **Purpose:** Database server hostname
- **Example:** `db.dosbzlhijkeircyainwz.supabase.co`

#### 9. DB_PORT
- **Current Value Location:** `.env` line with `DB_PORT=`
- **Purpose:** Database port
- **Default:** `5432`

#### 10. DB_NAME
- **Current Value Location:** `.env` line with `DB_NAME=`
- **Purpose:** Database name
- **Default:** `postgres`

#### 11. DB_USER
- **Current Value Location:** `.env` line with `DB_USER=`
- **Purpose:** Database username
- **Default:** `postgres`

#### 12. DB_PASSWORD
- **Current Value Location:** `.env` line with `DB_PASSWORD=`
- **Purpose:** Database password
- **Rules:** Must not be shared; keep confidential

### Embedding Model Configuration

#### 13. EMBEDDING_MODEL
- **Current Value Location:** `.env` line with `EMBEDDING_MODEL=`
- **Purpose:** Model identifier for embeddings
- **Example:** `text-embedding-3-small`

#### 14. USE_LOCAL_EMBEDDINGS
- **Current Value Location:** `.env` line with `USE_LOCAL_EMBEDDINGS=`
- **Purpose:** Whether to use local embeddings (HuggingFace) vs cloud API
- **Values:** `true` or `false`

### Local LLM Configuration (Optional)

#### 15. OLLAMA_BASE_URL
- **Current Value Location:** `.env` line with `OLLAMA_BASE_URL=`
- **Purpose:** Base URL for local Ollama LLM server
- **Default:** `http://localhost:11434`
- **Optional:** Only needed if using Ollama as fallback

---

## Secret Naming Rules (GitHub Codespaces)

✅ **Allowed:**
- Alphanumeric characters: `[a-z]`, `[A-Z]`, `[0-9]`
- Underscores: `_`

❌ **Not Allowed:**
- Spaces
- Starting with `GITHUB_` prefix
- Starting with numbers

✅ All secrets listed above follow these rules.

---

## Repository Access

When adding each secret, make sure to:
1. Select **Repository access** dropdown
2. Check the box for `acadiagit/vecinita` (or your forked repository name)
3. Click **Add secret**

---

## After Adding Secrets

Once secrets are added to GitHub Codespaces:

1. **For currently running codespaces:** Stop and restart the codespace
   - Open Command Palette (`Cmd+Shift+P` / `Ctrl+Shift+P`)
   - Type "Codespaces: Stop Current Codespace"
   - Restart the codespace
   
2. **For new codespaces:** Secrets are automatically available when the codespace starts

3. **Verify secrets are loaded:**
   ```bash
   echo $GROQ_API_KEY
   echo $SUPABASE_URL
   ```
   These commands should output the secret values.

---

## Environment Files Reference

### Files Using These Secrets
- **Backend:** `backend/.env` (loaded by `python-dotenv`)
- **Frontend:** May read `VITE_BACKEND_URL` from environment
- **Scripts:** `scripts/data_scrape_load.sh` uses DB credentials
- **Vector Loader:** `src/utils/vector_loader.py` uses Supabase credentials
- **Scraper:** `src/utils/scraper_to_text.py` may use API keys

---

## Security Best Practices

1. ✅ **Never commit `.env` to git** (it's in `.gitignore`)
2. ✅ **Use GitHub Codespaces secrets** instead of local `.env` files in shared environments
3. ✅ **Rotate API keys regularly** (especially if compromised)
4. ✅ **Use least-privileged credentials** (e.g., anon keys when possible)
5. ✅ **Keep `.env.example`** without sensitive values for documentation
6. ❌ **Never paste secrets in chat, PRs, or issues**

---

## Troubleshooting

### Secrets not appearing in codespace
- **Solution:** Stop and restart the codespace
- **Time:** Allow ~30 seconds for secrets to load after restart

### "Permission denied" errors
- **Likely cause:** DB credentials are incorrect or user lacks permissions
- **Solution:** Verify credentials in `.env` file with your Supabase dashboard

### API key not recognized
- **Likely cause:** Secret value has extra spaces or newlines
- **Solution:** When copying from `.env`, ensure no trailing whitespace

---

## Questions?

Refer to:
- [GitHub Codespaces Secrets Documentation](https://docs.github.com/en/codespaces/managing-your-codespaces/managing-encrypted-secrets-for-your-codespaces)
- [Vecinita Architecture Documentation](./ARCHITECTURE_MICROSERVICE.md)
- [Environment Configuration Guide](../backend/README.md)
