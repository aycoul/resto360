'use client';

import { useCartContext, CartItem } from '@/lib/store/cartStore';
import { LocalMenuItem } from '@/lib/db/schema';

export function useCart() {
  const { state, dispatch } = useCartContext();

  const addItem = (
    menuItem: LocalMenuItem,
    quantity: number = 1,
    selectedModifiers: { optionId: string; optionName: string; priceAdjustment: number }[] = [],
    notes: string = ''
  ) => {
    const modifierTotal = selectedModifiers.reduce(
      (sum, m) => sum + m.priceAdjustment,
      0
    );

    const cartItem: CartItem = {
      id: crypto.randomUUID(),
      menuItemId: menuItem.id,
      menuItemName: menuItem.name,
      quantity,
      unitPrice: menuItem.price + modifierTotal,
      notes,
      modifiers: selectedModifiers,
    };

    dispatch({ type: 'ADD_ITEM', payload: cartItem });
  };

  const removeItem = (id: string) => {
    dispatch({ type: 'REMOVE_ITEM', payload: id });
  };

  const updateQuantity = (id: string, quantity: number) => {
    if (quantity <= 0) {
      removeItem(id);
    } else {
      dispatch({ type: 'UPDATE_QUANTITY', payload: { id, quantity } });
    }
  };

  const updateItemNotes = (id: string, notes: string) => {
    dispatch({ type: 'UPDATE_ITEM_NOTES', payload: { id, notes } });
  };

  const setOrderType = (orderType: 'dine_in' | 'takeout' | 'delivery') => {
    dispatch({ type: 'SET_ORDER_TYPE', payload: orderType });
  };

  const setTable = (tableId: string | null) => {
    dispatch({ type: 'SET_TABLE', payload: tableId });
  };

  const setCustomerName = (name: string) => {
    dispatch({ type: 'SET_CUSTOMER_NAME', payload: name });
  };

  const setCustomerPhone = (phone: string) => {
    dispatch({ type: 'SET_CUSTOMER_PHONE', payload: phone });
  };

  const setNotes = (notes: string) => {
    dispatch({ type: 'SET_NOTES', payload: notes });
  };

  const clearCart = () => {
    dispatch({ type: 'CLEAR_CART' });
  };

  const subtotal = state.items.reduce(
    (sum, item) => sum + item.unitPrice * item.quantity,
    0
  );

  const total = subtotal; // Add tax/fees here if needed

  const itemCount = state.items.reduce((sum, item) => sum + item.quantity, 0);

  return {
    items: state.items,
    orderType: state.orderType,
    tableId: state.tableId,
    customerName: state.customerName,
    customerPhone: state.customerPhone,
    notes: state.notes,
    subtotal,
    total,
    itemCount,
    addItem,
    removeItem,
    updateQuantity,
    updateItemNotes,
    setOrderType,
    setTable,
    setCustomerName,
    setCustomerPhone,
    setNotes,
    clearCart,
  };
}
