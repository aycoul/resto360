'use client';

import { Button } from '@/components/ui/Button';

interface OrderConfirmationProps {
  orderNumber: number;
  total: number;
  estimatedWait: number;
  onClose: () => void;
}

export function OrderConfirmation({
  orderNumber,
  total,
  estimatedWait,
  onClose,
}: OrderConfirmationProps) {
  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-2xl w-full max-w-sm p-6 text-center">
        {/* Success Icon */}
        <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
          <svg
            className="w-8 h-8 text-green-600"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>
        </div>

        <h2 className="text-2xl font-bold mb-2">Order Confirmed!</h2>

        {/* Order Number */}
        <div className="bg-gray-100 rounded-lg p-4 my-4">
          <p className="text-gray-500 text-sm">Order Number</p>
          <p className="text-4xl font-bold text-blue-600">#{orderNumber}</p>
        </div>

        {/* Order Details */}
        <p className="text-gray-600 mb-2">
          Total: <span className="font-bold">{total.toLocaleString()} XOF</span>
        </p>

        <p className="text-gray-500 text-sm mb-6">
          Estimated wait: ~{estimatedWait} minutes
        </p>

        {/* Instructions */}
        <div className="bg-blue-50 rounded-lg p-3 mb-4">
          <p className="text-sm text-blue-700">
            Your order has been sent to the kitchen.
            <br />
            Please wait for your number to be called.
          </p>
        </div>

        <Button onClick={onClose} className="w-full">
          Done
        </Button>
      </div>
    </div>
  );
}
