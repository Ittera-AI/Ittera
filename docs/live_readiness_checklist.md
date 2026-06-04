# Live-Readiness Checklist

Before pushing any publishing features to production or running live traffic, verify the following steps. 
**Do not skip this manual audit.**

## 1. Authentication & OAuth
- [ ] **Connect Flow:** Connect LinkedIn and X via the Settings panel using test accounts.
- [ ] **Reconnect Flow (X):** Manually revoke app permissions in X settings, then attempt to publish. Ensure the UI clearly shows `Reconnect required` and blocks the HTTP publish attempt entirely.
- [ ] **Scope Verification:** For LinkedIn, verify that absent `r_member_social` scopes show "Read sync pending approval and separate from posting" in Settings.

## 2. Publishing & Queue Safety
- [ ] **Idempotency:** Force-schedule two identical posts to the same time. Ensure the Celery `publishing-queue` picks them up sequentially and does not infinitely loop on failures.
- [ ] **Immutability:** Once a draft enters `publishing` or `published` status, verify via API and UI that content, media, and schedule changes are strictly blocked.
- [ ] **Error Handling:** Simulate a network failure (e.g., block the host locally) during publishing. Verify that bounded HTTP retries apply, and the draft transitions to `failed` without Celery retrying infinitely.

## 3. Media & Limits
- [ ] **LinkedIn Limits:** Upload two images to a LinkedIn draft. Verify that the UI warning ("LinkedIn publishing supports one image in this version") is visible in Create and Calendar panels.
- [ ] **Media Upload:** Verify that image initialization and upload HTTP failures gracefully fail the entire draft publishing process without posting partial content.

## 4. Logging & Secrets
- [ ] **Secret-Safe Logs:** Trigger an API error on X or LinkedIn publishing. Tail the logs to ensure NO raw HTTP response bodies, `access_token`, or `refresh_token` are outputted.
- [ ] **Structured Logging:** Check that publishing failure logs contain ONLY `draft_id`, `user_id`, `platform`, and `error_category` alongside the exception class.

## 5. Deployment & Rollback
- [ ] **Celery Registration:** Verify `workers.celery.tasks.publisher.process_publishing_queue` is registered:
  `docker compose exec -T worker celery -A workers.celery.app inspect registered`
- [ ] **Environment Checks:** Verify staging/prod `.env` does not accidentally contain live test keys for unapproved features.
- [ ] **Rollback Checks:** Ensure Alembic down revisions are tested for any recent migrations.
