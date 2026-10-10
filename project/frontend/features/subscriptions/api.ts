export const endpoint = "/v1/subscriptions";
export async function listSubscriptions() {
  const response = await fetch(endpoint);
  if (!response.ok) throw new Error("subscriptions request failed");
  return response.json();
}
