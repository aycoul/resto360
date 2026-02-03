'use client';

import { createContext, useContext, useReducer, ReactNode } from 'react';
import { LocalOrderItem } from '@/lib/db/schema';

export interface CartItem extends LocalOrderItem {
  id: string; // temporary ID for cart
}

interface CartState {
  items: CartItem[];
  orderType: 'dine_in' | 'takeout' | 'delivery';
  tableId: string | null;
  customerName: string;
  customerPhone: string;
  notes: string;
}

type CartAction =
  | { type: 'ADD_ITEM'; payload: CartItem }
  | { type: 'REMOVE_ITEM'; payload: string }
  | { type: 'UPDATE_QUANTITY'; payload: { id: string; quantity: number } }
  | { type: 'UPDATE_ITEM_NOTES'; payload: { id: string; notes: string } }
  | { type: 'SET_ORDER_TYPE'; payload: 'dine_in' | 'takeout' | 'delivery' }
  | { type: 'SET_TABLE'; payload: string | null }
  | { type: 'SET_CUSTOMER_NAME'; payload: string }
  | { type: 'SET_CUSTOMER_PHONE'; payload: string }
  | { type: 'SET_NOTES'; payload: string }
  | { type: 'CLEAR_CART' };

const initialState: CartState = {
  items: [],
  orderType: 'dine_in',
  tableId: null,
  customerName: '',
  customerPhone: '',
  notes: '',
};

function cartReducer(state: CartState, action: CartAction): CartState {
  switch (action.type) {
    case 'ADD_ITEM':
      return { ...state, items: [...state.items, action.payload] };

    case 'REMOVE_ITEM':
      return { ...state, items: state.items.filter(i => i.id !== action.payload) };

    case 'UPDATE_QUANTITY':
      return {
        ...state,
        items: state.items.map(i =>
          i.id === action.payload.id
            ? { ...i, quantity: action.payload.quantity }
            : i
        ),
      };

    case 'UPDATE_ITEM_NOTES':
      return {
        ...state,
        items: state.items.map(i =>
          i.id === action.payload.id
            ? { ...i, notes: action.payload.notes }
            : i
        ),
      };

    case 'SET_ORDER_TYPE':
      return {
        ...state,
        orderType: action.payload,
        tableId: action.payload !== 'dine_in' ? null : state.tableId,
      };

    case 'SET_TABLE':
      return { ...state, tableId: action.payload };

    case 'SET_CUSTOMER_NAME':
      return { ...state, customerName: action.payload };

    case 'SET_CUSTOMER_PHONE':
      return { ...state, customerPhone: action.payload };

    case 'SET_NOTES':
      return { ...state, notes: action.payload };

    case 'CLEAR_CART':
      return initialState;

    default:
      return state;
  }
}

const CartContext = createContext<{
  state: CartState;
  dispatch: React.Dispatch<CartAction>;
} | null>(null);

export function CartProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(cartReducer, initialState);
  return (
    <CartContext.Provider value={{ state, dispatch }}>
      {children}
    </CartContext.Provider>
  );
}

export function useCartContext() {
  const context = useContext(CartContext);
  if (!context) {
    throw new Error('useCartContext must be used within CartProvider');
  }
  return context;
}
