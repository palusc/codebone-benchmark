export const endpoint = "/v1/analytics";
export async function listAnalytics() {
  const response = await fetch(endpoint);
  if (!response.ok) throw new Error("analytics request failed");
  return response.json();
}
