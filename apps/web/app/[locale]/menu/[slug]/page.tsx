'use client';

import { useState } from 'react';
import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import { usePublicMenu } from '@/lib/hooks/usePublicMenu';
import { useCart } from '@/lib/hooks/useCart';
import { PublicMenuGrid } from '@/components/menu/PublicMenuGrid';
import { CustomerCart } from '@/components/menu/CustomerCart';
import { LocaleSwitcher } from '@/components/ui/LocaleSwitcher';

export default function PublicMenuPage() {
  const params = useParams();
  const slug = params.slug as string;
  const t = useTranslations('pos');
  const { data, isLoading, error } = usePublicMenu(slug);
  const { itemCount, total } = useCart();
  const [showCart, setShowCart] = useState(false);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500">{t('menu.title')}...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <p className="text-red-500 mb-2">Restaurant not found</p>
          <p className="text-gray-500 text-sm">
            Please check the QR code and try again
          </p>
        </div>
      </div>
    );
  }

  if (!data) return null;

  return (
    <div className="pb-24">
      {/* Header */}
      <header className="bg-white shadow-sm sticky top-0 z-10">
        <div className="max-w-lg mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-xl font-bold">{data.restaurant.name}</h1>
              {data.restaurant.address && (
                <p className="text-sm text-gray-500">{data.restaurant.address}</p>
              )}
            </div>
            <LocaleSwitcher />
          </div>
        </div>
      </header>

      {/* Menu */}
      <main className="max-w-lg mx-auto px-4 py-4">
        {data.categories.length === 0 ? (
          <p className="text-gray-400 text-center py-8">No menu items available</p>
        ) : (
          data.categories.map(category => (
            <div key={category.id} className="mb-6">
              <h2 className="text-lg font-bold mb-3 sticky top-16 bg-gray-50 py-2">
                {category.name}
              </h2>
              <PublicMenuGrid items={category.items} />
            </div>
          ))
        )}
      </main>

      {/* Cart FAB */}
      {itemCount > 0 && (
        <button
          onClick={() => setShowCart(true)}
          className="fixed bottom-4 left-4 right-4 max-w-lg mx-auto bg-blue-600 text-white py-4 rounded-lg shadow-lg flex items-center justify-between px-6"
        >
          <span className="flex items-center gap-2">
            <span className="bg-white/20 px-2 py-1 rounded">{itemCount}</span>
            <span>{t('cart.title')}</span>
          </span>
          <span className="font-bold">{total.toLocaleString()} XOF</span>
        </button>
      )}

      {/* Cart Modal */}
      {showCart && (
        <CustomerCart
          restaurantSlug={slug}
          onClose={() => setShowCart(false)}
        />
      )}
    </div>
  );
}
