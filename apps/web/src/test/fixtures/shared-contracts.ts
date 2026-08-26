import type { components } from "@iterra/shared-types";

type Schemas = components["schemas"];

export type WaitlistRequestContract = Schemas["WaitlistRequest"];
export type WaitlistResponseContract = Schemas["WaitlistResponse"];
export type WaitlistStatsContract = Schemas["WaitlistStatsResponse"];
export type WaitlistMemberStatusContract = Schemas["WaitlistMemberStatusResponse"];
export type PlatformStatusContract = Schemas["PlatformStatusResponse"];
export type ConnectSessionResponseContract = Schemas["ConnectSessionResponseV1"];
export type AuthorizationContextContract = Schemas["AuthorizationContextV1"];

export const CONNECT_SESSION_FIXTURE = {
  schema_version: "connect-session.v1",
  connect_token: "ct-fixture-single-use",
} satisfies ConnectSessionResponseContract;

/** Developer B fake for the Developer A-owned authorization boundary. */
export const AUTHORIZATION_CONTEXT_FIXTURE = {
  schema_version: "authorization-context.v1",
  availability: "available",
  reason: null,
  workspace: {
    schema_version: "workspace-summary.v1",
    availability: "available",
    reason: null,
    id: "workspace-fixture",
    organization_id: "organization-fixture",
    organization_name: "Fixture Organization",
    name: "Fixture Workspace",
    slug: "fixture-workspace",
    is_active: true,
  },
  brand: {
    schema_version: "brand-summary.v1",
    availability: "degraded",
    reason: "brand_profile_not_provisioned",
    id: null,
    workspace_id: "workspace-fixture",
    name: "Fixture Workspace",
    profile_version: null,
    brand_colors: {},
    logo_url: null,
  },
  role: "manager",
  permissions: ["workspace:view"],
  white_label: {
    schema_version: "white-label-summary.v1",
    availability: "available",
    reason: null,
    enabled: false,
    primary_color: "#6366F1",
    secondary_color: "#A5B4FC",
    logo_url: null,
    sender_name: "Iterra Reports",
    hide_powered_by: false,
  },
} satisfies AuthorizationContextContract;

export const WAITLIST_REQUEST_FIXTURE = {
  email: "member@example.test",
  name: "Member",
  profession: "Creator",
} satisfies WaitlistRequestContract;

export const WAITLIST_RESPONSE_FIXTURE = {
  message: "Already on the waitlist",
  position: 4,
  already_joined: true,
  total_joined: 42,
  total_seats: 100,
  remaining_seats: 58,
  recent_joiners: [],
} satisfies WaitlistResponseContract;

export const WAITLIST_STATS_FIXTURE = {
  total_joined: 42,
  total_seats: 100,
  remaining_seats: 58,
  recent_joiners: [],
} satisfies WaitlistStatsContract;

export function createWaitlistMemberStatusFixture(
  overrides: Partial<WaitlistMemberStatusContract> = {},
): WaitlistMemberStatusContract {
  return {
    email: "member@example.test",
    joined: true,
    access_approved: false,
    approved_at: null,
    position: 4,
    total_joined: 42,
    total_seats: 100,
    remaining_seats: 58,
    ...overrides,
  };
}

export const EMPTY_PLATFORM_STATUS_FIXTURE = [] satisfies PlatformStatusContract[];

export const PLATFORM_STATUS_FIXTURE = {
  platform: "linkedin",
  connected: true,
  platform_username: "mock-linkedin",
  last_synced_at: null,
  synced_posts: 0,
  scopes: [],
  posting_ready: false,
  read_sync_ready: false,
  missing_posting_scopes: [],
  missing_read_scopes: [],
  reconnect_required: false,
  message: null,
  sync_status: null,
  sync_error: null,
  sync_started_at: null,
} satisfies PlatformStatusContract;
