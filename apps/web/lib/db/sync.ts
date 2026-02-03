import { db, PendingOperation } from "./schema";

// Add operation to sync queue
export async function queueOperation(
  type: PendingOperation["type"],
  payload: Record<string, unknown>
): Promise<number> {
  return db.pendingOps.add({
    type,
    payload,
    createdAt: new Date(),
    syncStatus: "pending",
    retryCount: 0,
  });
}

// Get all pending operations
export async function getPendingOperations(): Promise<PendingOperation[]> {
  return db.pendingOps.where("syncStatus").equals("pending").sortBy("createdAt");
}

// Mark operation as syncing
export async function markSyncing(id: number): Promise<void> {
  await db.pendingOps.update(id, { syncStatus: "syncing" });
}

// Mark operation as synced (delete it)
export async function markSynced(id: number): Promise<void> {
  await db.pendingOps.delete(id);
}

// Mark operation as failed
export async function markFailed(id: number, error: string): Promise<void> {
  const op = await db.pendingOps.get(id);
  if (op) {
    await db.pendingOps.update(id, {
      syncStatus: op.retryCount >= 3 ? "failed" : "pending",
      retryCount: op.retryCount + 1,
      lastError: error,
    });
  }
}

// Update sync metadata
export async function updateSyncMeta(
  key: string,
  value: string | Date
): Promise<void> {
  await db.syncMeta.put({ key, value });
}

// Get sync metadata
export async function getSyncMeta(
  key: string
): Promise<string | Date | undefined> {
  const record = await db.syncMeta.get(key);
  return record?.value;
}

// Get pending operation count
export async function getPendingCount(): Promise<number> {
  return db.pendingOps.where("syncStatus").equals("pending").count();
}
