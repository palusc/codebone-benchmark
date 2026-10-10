export const endpoint = "/v1/audit";
export async function listAudit() {
  const response = await fetch(endpoint);
  if (!response.ok) throw new Error("audit request failed");
  return response.json();
}
