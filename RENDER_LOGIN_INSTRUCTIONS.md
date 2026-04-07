# Render CLI Login Instructions

## Device Authorization Code: H31Z-FL12-1YOP-GI0U

### Step 1: Complete Authorization in Browser

1. Go to this URL in your web browser:
   ```
   https://dashboard.render.com/device-authorization/H31Z-FL12-1YOP-GI0U
   ```

2. You'll see a prompt asking to authorize the Render CLI device.

3. Click **Authorize** to approve CLI access to your account.

### Step 2: Verify Authentication

Once authorized, verify the CLI is logged in:

```bash
render whoami
```

Expected output:
```
Email:     <your-email>
Workspace: <your-workspace>
```

### Step 3: Set Environment Variables

Once authenticated, run the setup script:

```bash
./scripts/setup-render-env.sh
```

The script will:
- Read Modal credentials from `.env`
- Apply them to the data-management-api service
- Show verification instructions

---

## If Authorization Fails or You Don't Have Browser Access

**Use the API method instead** (no CLI authentication needed):

```bash
# Set your Render API key
export RENDER_API_KEY="<your-api-key>"

# Run the direct API script
./scripts/apply-render-env-api.sh
```

This bypasses CLI authentication entirely.

---

## Trouble Getting RENDER_API_KEY?

1. Go to: https://dashboard.render.com/api-keys
2. Click **Create New** API Key
3. Copy the key
4. Set it: `export RENDER_API_KEY="<your-key>"`

---

## Verification Command (After Variables are Set)

Once environment variables are applied (either method), test the API:

```bash
curl https://vecinita-data-management-api-v1.onrender.com/health
```

Expected response:
```json
{
  "status": "ok",
  "modal_reachable": true
}
```
