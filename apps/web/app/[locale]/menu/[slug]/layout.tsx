import { CartProvider } from '@/lib/store/cartStore';

export default function MenuLayout({ children }: { children: React.ReactNode }) {
  return (
    <CartProvider>
      <div className="min-h-screen bg-gray-50">
        {children}
      </div>
    </CartProvider>
  );
}
