import { CartProvider } from '@/lib/store/cartStore';

export default function POSLayout({ children }: { children: React.ReactNode }) {
  return <CartProvider>{children}</CartProvider>;
}
