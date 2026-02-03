import Dexie, { Table } from "dexie";

// Types for IndexedDB storage
export interface LocalMenuItem {
  id: string;
  categoryId: string;
  name: string;
  description: string;
  price: number;
  thumbnailUrl: string | null;
  isAvailable: boolean;
  modifiers: LocalModifier[];
  syncedAt: Date;
}

export interface LocalModifier {
  id: string;
  name: string;
  required: boolean;
  maxSelections: number;
  options: LocalModifierOption[];
}

export interface LocalModifierOption {
  id: string;
  name: string;
  priceAdjustment: number;
  isAvailable: boolean;
}

export interface LocalCategory {
  id: string;
  name: string;
  displayOrder: number;
  isVisible: boolean;
  syncedAt: Date;
}

export interface LocalOrder {
  localId: string;
  serverId: string | null;
  orderNumber: number | null;
  orderType: "dine_in" | "takeout" | "delivery";
  status: "pending" | "preparing" | "ready" | "completed" | "cancelled";
  tableId: string | null;
  customerName: string;
  customerPhone: string;
  notes: string;
  items: LocalOrderItem[];
  subtotal: number;
  total: number;
  createdAt: Date;
  syncedAt: Date | null;
}

export interface LocalOrderItem {
  menuItemId: string;
  menuItemName: string;
  quantity: number;
  unitPrice: number;
  notes: string;
  modifiers: {
    optionId: string;
    optionName: string;
    priceAdjustment: number;
  }[];
}

export interface PendingOperation {
  id?: number;
  type: "CREATE_ORDER" | "UPDATE_STATUS";
  payload: Record<string, unknown>;
  createdAt: Date;
  syncStatus: "pending" | "syncing" | "failed";
  retryCount: number;
  lastError?: string;
}

export interface SyncMeta {
  key: string;
  value: string | Date;
}

class RestaurantDB extends Dexie {
  categories!: Table<LocalCategory>;
  menuItems!: Table<LocalMenuItem>;
  orders!: Table<LocalOrder>;
  pendingOps!: Table<PendingOperation>;
  syncMeta!: Table<SyncMeta>;

  constructor() {
    super("resto360");

    this.version(1).stores({
      categories: "id, name, displayOrder",
      menuItems: "id, categoryId, name, isAvailable",
      orders: "localId, serverId, status, createdAt",
      pendingOps: "++id, type, syncStatus, createdAt",
      syncMeta: "key",
    });
  }
}

export const db = new RestaurantDB();

// Helper to check if database is available
export async function isDatabaseReady(): Promise<boolean> {
  try {
    await db.open();
    return true;
  } catch {
    return false;
  }
}
