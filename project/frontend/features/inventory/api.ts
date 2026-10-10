export const endpoint = "/v1/inventory";
export async function listInventory() {
  const response = await fetch(endpoint);
  if (!response.ok) throw new Error("inventory request failed");
  return response.json();
}
