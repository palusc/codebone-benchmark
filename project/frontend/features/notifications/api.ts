export const endpoint = "/v1/notifications";
export async function listNotifications() {
  const response = await fetch(endpoint);
  if (!response.ok) throw new Error("notifications request failed");
  return response.json();
}
