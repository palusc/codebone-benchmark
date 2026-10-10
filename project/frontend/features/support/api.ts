export const endpoint = "/v1/support";
export async function listSupport() {
  const response = await fetch(endpoint);
  if (!response.ok) throw new Error("support request failed");
  return response.json();
}
