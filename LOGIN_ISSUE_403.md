# Google OAuth 403 Error - Login Issue

## Current Status
The application is currently stuck on a **Google 403 Forbidden** error when attempting to log in via OAuth. This file documents the issue for future debugging.

## Symptoms
1. User clicks "Sign in with Google".
2. Google login page appears.
3. User selects their `bits-pilani` or `gmail` account.
4. Google immediately returns a **403 Forbidden** page saying:
   > "We're sorry, but you do not have access to this page. That’s all we know."

## Configuration Verified (As Correct)
- **Client ID & Secret**: Correctly loaded from `client_secret.json`.
- **Redirect URI**: Set to `http://localhost:8501` in both Python code and Google Cloud Console.
- **Test Users**: The email addresses being used ARE listed in the "Test Users" section of the OAuth consent screen.
- **Publishing Status**: App is in "Testing" mode.

## What Has Been Tried
1. **Added Test Users**: Added both university and personal Gmail accounts.
2. **Cleared Cache**: Tested in Incognito mode to remove cookie conflicts.
3. **Restored Old Code**: Reverted `auth.py` and `app.py` to a known previous implementation.
4. **Target="_top"**: Updated login link to break out of Streamlit iframes.
5. **People API**: Checked that Google People API is enabled.

## Likely Root Causes
1. **University Workspace Policy**: The `@goa.bits-pilani.ac.in` domain likely has strict admin policies blocking "Testing" status apps, regardless of Test User settings.
2. **Project ID Mismatch**: There remains a possibility that the `client_secret.json` corresponds to a different Google Cloud Project than the one where Test Users were added.
3. **Google Safety Net**: Google sometimes blocks unverified apps requesting sensitive scopes (`profile`, `email`) if they detect "suspicious" patterns, even in testing.

## Next Steps for Future Fix
- **Create a Fresh Project**: Delete the current Cloud Project credentials and start from scratch with a personal Gmail account as the project owner.
- **Verify Project ID**: Ensure the top-left dropdown in Google Cloud Console matches the `project_id` in `client_secret.json`.
- **Check Admin Logs**: If possible, check Google Workspace admin logs for the university domain to see if the OAuth request was blocked by policy.
