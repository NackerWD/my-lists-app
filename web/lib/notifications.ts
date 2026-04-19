import { PushNotifications } from "@capacitor/push-notifications";
import { Capacitor } from "@capacitor/core";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

function mapPlatform(): "android" | "ios" | "web" {
  const p = Capacitor.getPlatform();
  if (p === "ios") return "ios";
  if (p === "android") return "android";
  return "web";
}

export async function registerPushNotifications(accessToken: string): Promise<void> {
  if (!Capacitor.isNativePlatform()) return;
  const perm = await PushNotifications.requestPermissions();
  if (perm.receive !== "granted") return;
  await PushNotifications.removeAllListeners();
  await PushNotifications.register();
  PushNotifications.addListener("registration", async ({ value: token }) => {
    await fetch(`${API_URL}/api/v1/device-tokens/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${accessToken}`,
      },
      body: JSON.stringify({ token, platform: mapPlatform() }),
    });
  });
  PushNotifications.addListener("pushNotificationActionPerformed", ({ notification }) => {
    const listId = notification.data?.list_id as string | undefined;
    if (listId) window.location.href = `/lists/${listId}`;
  });
}

export async function unregisterPushNotifications(
  token: string,
  accessToken: string
): Promise<void> {
  if (!Capacitor.isNativePlatform()) return;
  await PushNotifications.removeAllListeners();
  await fetch(`${API_URL}/api/v1/device-tokens/${encodeURIComponent(token)}`, {
    method: "DELETE",
    headers: { Authorization: `Bearer ${accessToken}` },
  });
}
