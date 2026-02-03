'use client';

import { useCart } from '@/lib/hooks/useCart';
import { CartItem as CartItemType } from '@/lib/store/cartStore';

interface CartItemProps {
  item: CartItemType;
}

export function CartItem({ item }: CartItemProps) {
  const { updateQuantity, removeItem } = useCart();

  return (
    <div className="bg-gray-50 rounded-lg p-3">
      <div className="flex justify-between items-start mb-2">
        <div>
          <h4 className="font-medium">{item.menuItemName}</h4>
          {item.modifiers.length > 0 && (
            <p className="text-sm text-gray-500">
              {item.modifiers.map(m => m.optionName).join(', ')}
            </p>
          )}
          {item.notes && (
            <p className="text-xs text-gray-400 italic">{item.notes}</p>
          )}
        </div>
        <button
          onClick={() => removeItem(item.id)}
          className="text-red-500 hover:text-red-700"
        >
          &times;
        </button>
      </div>
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <button
            onClick={() => updateQuantity(item.id, item.quantity - 1)}
            className="w-8 h-8 rounded bg-gray-200 hover:bg-gray-300"
          >
            -
          </button>
          <span className="w-8 text-center">{item.quantity}</span>
          <button
            onClick={() => updateQuantity(item.id, item.quantity + 1)}
            className="w-8 h-8 rounded bg-gray-200 hover:bg-gray-300"
          >
            +
          </button>
        </div>
        <span className="font-medium">
          {(item.unitPrice * item.quantity).toLocaleString()} XOF
        </span>
      </div>
    </div>
  );
}
