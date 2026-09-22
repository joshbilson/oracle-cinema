import { afterEach, expect, spyOn, test } from "bun:test";
import { checkApiReachable } from "./serverConnection";

let fetchSpy: ReturnType<typeof spyOn> | undefined;
afterEach(() => fetchSpy?.mockRestore());

test("a stalled connection releases the UI even if fetch ignores abort", async () => {
  fetchSpy = spyOn(globalThis, "fetch").mockImplementation(
    () => new Promise<Response>(() => {}),
  );
  expect(await checkApiReachable("https://example.invalid", 20)).toBe(false);
});

test("a healthy server is reachable", async () => {
  fetchSpy = spyOn(globalThis, "fetch").mockResolvedValue(new Response(null));
  expect(await checkApiReachable("https://example.invalid")).toBe(true);
});

test("an offline server is reported as unreachable", async () => {
  fetchSpy = spyOn(globalThis, "fetch").mockRejectedValue(new Error("offline"));
  expect(await checkApiReachable("https://example.invalid")).toBe(false);
});

test("a missing server does not make a request", async () => {
  fetchSpy = spyOn(globalThis, "fetch");
  expect(await checkApiReachable()).toBe(false);
  expect(fetchSpy).not.toHaveBeenCalled();
});
