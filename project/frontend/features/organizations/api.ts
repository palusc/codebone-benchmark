export const endpoint = "/v1/organizations";
export async function listOrganizations() {
  const response = await fetch(endpoint);
  if (!response.ok) throw new Error("organizations request failed");
  return response.json();
}
