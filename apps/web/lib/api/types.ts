export interface Category {
  id: string;
  name: string;
  display_order: number;
  is_visible: boolean;
  items: MenuItem[];
}

export interface MenuItem {
  id: string;
  category: string;
  name: string;
  description: string;
  price: number;
  thumbnail_url: string | null;
  is_available: boolean;
  modifiers: Modifier[];
}

export interface Modifier {
  id: string;
  name: string;
  required: boolean;
  max_selections: number;
  options: ModifierOption[];
}

export interface ModifierOption {
  id: string;
  name: string;
  price_adjustment: number;
  is_available: boolean;
}

export interface Order {
  id: string;
  order_number: number;
  order_type: "dine_in" | "takeout" | "delivery";
  status: "pending" | "preparing" | "ready" | "completed" | "cancelled";
  table: string | null;
  customer_name: string;
  customer_phone: string;
  notes: string;
  subtotal: number;
  total: number;
  items: OrderItem[];
  created_at: string;
}

export interface OrderItem {
  id: string;
  menu_item: string;
  menu_item_name: string;
  quantity: number;
  unit_price: number;
  notes: string;
  modifiers: OrderItemModifier[];
}

export interface OrderItemModifier {
  modifier_option: string;
  modifier_option_name: string;
  price_adjustment: number;
}

export interface CreateOrderPayload {
  order_type: "dine_in" | "takeout" | "delivery";
  table?: string;
  customer_name?: string;
  customer_phone?: string;
  notes?: string;
  items: {
    menu_item_id: string;
    quantity: number;
    notes?: string;
    modifiers: { modifier_option_id: string }[];
  }[];
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface ApiError {
  detail: string;
  code?: string;
}
