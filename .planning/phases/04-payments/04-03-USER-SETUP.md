# Phase 04-03: User Setup Required

**Generated:** 2026-02-04
**Phase:** 04-payments (Orange Money and MTN MoMo Providers)
**Status:** Incomplete

## Overview

This phase introduced Orange Money and MTN MoMo payment integrations. Both require API credentials from their respective developer portals.

---

## Orange Money Configuration

### Environment Variables

| Status | Variable | Source | Add to |
|--------|----------|--------|--------|
| [ ] | `ORANGE_CLIENT_ID` | Orange Developer Portal -> My Apps -> App Details | `.env` |
| [ ] | `ORANGE_CLIENT_SECRET` | Orange Developer Portal -> My Apps -> App Details | `.env` |
| [ ] | `ORANGE_MERCHANT_KEY` | Orange Money Business Dashboard | `.env` |
| [ ] | `ORANGE_API_URL` | Default: `https://api.orange.com/orange-money-webpay/dev/v1` (optional) | `.env` |

### Account Setup

1. [ ] Create account at [Orange Developer Portal](https://developer.orange.com/)
2. [ ] Register your application
3. [ ] Subscribe to Orange Money Webpay API
4. [ ] Get Client ID and Client Secret from app details
5. [ ] Apply for Orange Money Business account for Merchant Key (production)

### Notes

- **Sandbox testing:** Use dev API URL for testing
- **Production:** Change ORANGE_API_URL to production endpoint
- **Currency:** Orange uses "OUV" internally but our code handles XOF conversion

---

## MTN MoMo Configuration

### Environment Variables

| Status | Variable | Source | Add to |
|--------|----------|--------|--------|
| [ ] | `MTN_SUBSCRIPTION_KEY` | MTN MoMo Developer Portal -> Profile -> Subscriptions | `.env` |
| [ ] | `MTN_USER_ID` | Generated via MTN API user provisioning | `.env` |
| [ ] | `MTN_API_SECRET` | Generated via MTN API user provisioning | `.env` |
| [ ] | `MTN_ENVIRONMENT` | Set to `sandbox` or `production` | `.env` |
| [ ] | `MTN_CALLBACK_URL` | Your webhook endpoint (production only) | `.env` |

### Account Setup

1. [ ] Create account at [MTN MoMo Developer Portal](https://momodeveloper.mtn.com/)
2. [ ] Subscribe to Collection API product
3. [ ] Get your Primary Key (Ocp-Apim-Subscription-Key)
4. [ ] Generate API User ID via sandbox provisioning endpoint
5. [ ] Generate API Key for the API User

### API User Provisioning (Sandbox)

For sandbox testing, you need to provision an API user:

```bash
# 1. Generate UUID for user ID
export MTN_USER_ID=$(uuidgen)

# 2. Create API user
curl -X POST "https://sandbox.momodeveloper.mtn.com/v1_0/apiuser" \
  -H "X-Reference-Id: $MTN_USER_ID" \
  -H "Ocp-Apim-Subscription-Key: YOUR_SUBSCRIPTION_KEY" \
  -H "Content-Type: application/json" \
  -d '{"providerCallbackHost": "https://your-domain.com"}'

# 3. Generate API key
curl -X POST "https://sandbox.momodeveloper.mtn.com/v1_0/apiuser/$MTN_USER_ID/apikey" \
  -H "Ocp-Apim-Subscription-Key: YOUR_SUBSCRIPTION_KEY"
```

### Notes

- **Sandbox uses EUR:** MTN sandbox only accepts EUR currency, not XOF
- **No sandbox callbacks:** MTN sandbox does not send webhook callbacks - polling is essential
- **Production:** Change MTN_ENVIRONMENT to `production` and set MTN_CALLBACK_URL

---

## Verification

After setting up credentials, verify with:

```bash
cd apps/api

# Test Orange provider
DJANGO_SETTINGS_MODULE=config.settings.development python -c "
from apps.payments.providers import get_provider
p = get_provider('orange')
print(f'Orange configured: {bool(p.client_id)}')"

# Test MTN provider
DJANGO_SETTINGS_MODULE=config.settings.development python -c "
from apps.payments.providers import get_provider
p = get_provider('mtn')
print(f'MTN configured: {bool(p.subscription_key)}')"
```

---

## Example .env Additions

```env
# Orange Money
ORANGE_CLIENT_ID=your_client_id_here
ORANGE_CLIENT_SECRET=your_client_secret_here
ORANGE_MERCHANT_KEY=your_merchant_key_here

# MTN MoMo
MTN_SUBSCRIPTION_KEY=your_subscription_key_here
MTN_USER_ID=your_api_user_uuid_here
MTN_API_SECRET=your_api_secret_here
MTN_ENVIRONMENT=sandbox
MTN_CALLBACK_URL=
```

---

**Once all items complete:** Mark status as "Complete"
