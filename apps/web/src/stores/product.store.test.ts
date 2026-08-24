import { beforeEach, describe, expect, it, vi } from "vitest";

const serviceMocks = vi.hoisted(() => ({
  connectLinkedIn: vi.fn(),
  getBrandProfile: vi.fn(),
  getPublishingSettings: vi.fn(),
  linkedinStatus: vi.fn(),
  socialConnections: vi.fn(),
}));

vi.mock("@/services/product.service", () => ({
  productService: serviceMocks,
}));

import { resetAuthBoundState } from "@/lib/auth-bound-state";
import { useProductStore } from "@/stores/product.store";

function deferred<T>() {
  let resolve!: (value: T) => void;
  let reject!: (reason?: unknown) => void;
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

beforeEach(() => {
  useProductStore.getState().reset();
  for (const mock of Object.values(serviceMocks)) mock.mockReset();
  serviceMocks.getBrandProfile.mockResolvedValue(null);
  serviceMocks.getPublishingSettings.mockResolvedValue(null);
  serviceMocks.socialConnections.mockResolvedValue([]);
});

describe("product store containment", () => {
  it("does not persist server-returned product data", () => {
    useProductStore.setState({
      suggestions: [{ id: "private-suggestion" } as never],
      error: "private error",
      lastUpdated: { dashboard: Date.now() },
    });

    expect(localStorage.getItem("iterra-product-store")).toBeNull();
  });

  it("clears in-memory product data at workspace boundaries", () => {
    useProductStore.setState({
      suggestions: [{ id: "workspace-a" } as never],
      error: "workspace-a error",
      lastUpdated: { dashboard: Date.now() },
    });

    resetAuthBoundState("workspace");

    const state = useProductStore.getState();
    expect(state.suggestions).toEqual([]);
    expect(state.error).toBeNull();
    expect(state.lastUpdated).toEqual({});
  });

  it("ignores a dashboard response that settles after a boundary reset", async () => {
    const linkedinResponse = deferred<{ connected: boolean }>();
    serviceMocks.linkedinStatus.mockReturnValue(linkedinResponse.promise);

    const load = useProductStore.getState().loadDashboard();
    expect(useProductStore.getState().loadingStates.dashboard).toBe("loading");

    resetAuthBoundState("auth");
    linkedinResponse.resolve({ connected: true });
    await load;

    const state = useProductStore.getState();
    expect(state.linkedin).toBeNull();
    expect(state.socialConnections).toEqual([]);
    expect(state.loadingStates.dashboard).toBe("idle");
    expect(state.error).toBeNull();
    expect(state.lastUpdated).toEqual({});
  });

  it("does not resume popup-backed connection work after a boundary reset", async () => {
    const popupCompletion = deferred<void>();
    serviceMocks.connectLinkedIn.mockReturnValue(popupCompletion.promise);

    const connect = useProductStore.getState().connectLinkedIn();
    expect(useProductStore.getState().isLoading).toBe(true);

    resetAuthBoundState("workspace");
    popupCompletion.resolve();
    await connect;

    expect(serviceMocks.linkedinStatus).not.toHaveBeenCalled();
    expect(serviceMocks.socialConnections).not.toHaveBeenCalled();
    expect(useProductStore.getState().isLoading).toBe(false);
    expect(useProductStore.getState().error).toBeNull();
  });
});
