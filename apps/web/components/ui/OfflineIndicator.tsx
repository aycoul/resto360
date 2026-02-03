"use client";

import { useTranslations } from "next-intl";
import { useOnlineStatus } from "@/lib/hooks/useOnlineStatus";
import { useLiveQuery } from "dexie-react-hooks";
import { db } from "@/lib/db/schema";

export function OfflineIndicator() {
  const t = useTranslations("offline");
  const isOnline = useOnlineStatus();

  const pendingCount = useLiveQuery(
    () => db.pendingOps.where("syncStatus").equals("pending").count(),
    [],
    0
  );

  if (isOnline && pendingCount === 0) {
    return null;
  }

  return (
    <div
      className={`fixed bottom-4 right-4 px-4 py-2 rounded-lg shadow-lg ${
        isOnline ? "bg-yellow-500" : "bg-red-500"
      } text-white`}
    >
      {!isOnline && (
        <span className="flex items-center gap-2">
          <span className="w-2 h-2 bg-white rounded-full animate-pulse" />
          {t("status")}
        </span>
      )}
      {pendingCount > 0 && (
        <span className="text-sm">
          {pendingCount} {t("pendingOrders")}
        </span>
      )}
    </div>
  );
}
