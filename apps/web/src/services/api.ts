/**
 * Compatibility shim.
 *
 * The single source of truth for API transport now lives in `@/lib/api`.
 * This module re-exports the low-level `apiFetch` and `ApiError` so existing
 * consumers (`product.service.ts`, `waitlist-access.ts`, the waitlist status
 * page) keep working without duplicating token/refresh/error-handling logic.
 *
 * New code should import from `@/lib/api` directly.
 */

export { ApiError, apiFetch } from "@/lib/api";
