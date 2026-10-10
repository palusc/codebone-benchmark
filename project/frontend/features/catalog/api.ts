export const endpoint = "/v1/catalog";
export async function listCatalog() {
  const response = await fetch(endpoint);
  if (!response.ok) throw new Error("catalog request failed");
  return response.json();
}
