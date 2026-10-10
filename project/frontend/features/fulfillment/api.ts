export const endpoint = "/v1/fulfillment";
export async function listFulfillment() {
  const response = await fetch(endpoint);
  if (!response.ok) throw new Error("fulfillment request failed");
  return response.json();
}
