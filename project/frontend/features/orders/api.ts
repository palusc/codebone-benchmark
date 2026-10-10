export const endpoint = "/v1/orders";
export async function listOrders() {
  const response = await fetch(endpoint);
  if (!response.ok) throw new Error("orders request failed");
  return response.json();
}
