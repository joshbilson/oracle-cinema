// Always release the loading UI, including when a native fetch never settles.
export async function checkApiReachable(
  basePath?: string,
  timeoutMs = 8000,
): Promise<boolean> {
  if (!basePath) return false;
  const controller = new AbortController();
  let timer: ReturnType<typeof setTimeout> | undefined;
  const deadline = new Promise<boolean>((resolve) => {
    timer = setTimeout(() => {
      resolve(false);
      controller.abort();
    }, timeoutMs);
  });
  try {
    const url = basePath.endsWith("/") ? basePath : `${basePath}/`;
    const request = fetch(url, {
      method: "HEAD",
      signal: controller.signal,
    }).then((response) => response.ok);
    return await Promise.race([request, deadline]);
  } catch {
    return false;
  } finally {
    clearTimeout(timer);
  }
}
