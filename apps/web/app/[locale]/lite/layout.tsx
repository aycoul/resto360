'use client';

import { useState, useEffect, createContext, useContext } from 'react';
import { useRouter } from 'next/navigation';
import { useLocale } from 'next-intl';
import { getAccessToken, api } from '@/lib/api/client';
import { LiteSidebar } from '@/components/lite/LiteSidebar';
import { LiteHeader } from '@/components/lite/LiteHeader';

interface Restaurant {
  id: string;
  name: string;
  slug: string;
  phone?: string;
  email?: string;
  address?: string;
  plan_type: 'free' | 'pro' | 'full';
  logo?: string;
  primary_color?: string;
  show_branding: boolean;
}

interface User {
  id: string;
  name: string;
  email: string;
  phone: string;
  role: string;
}

interface LiteContextValue {
  restaurant: Restaurant | null;
  user: User | null;
  isLoading: boolean;
  refreshUser?: () => Promise<void>;
}

const LiteContext = createContext<LiteContextValue>({
  restaurant: null,
  user: null,
  isLoading: true,
});

export function useLiteContext() {
  return useContext(LiteContext);
}

export default function LiteLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const locale = useLocale();
  const [restaurant, setRestaurant] = useState<Restaurant | null>(null);
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const loadUserData = async () => {
    const token = getAccessToken();

    if (!token) {
      router.push(`/${locale}/register`);
      return;
    }

    try {
      // Fetch user and restaurant info
      const userData = await api.get<{ user: User; restaurant: Restaurant }>('/api/v1/auth/me/');

      setUser(userData.user);
      setRestaurant(userData.restaurant);

      // If user has full plan, redirect to main POS dashboard
      if (userData.restaurant.plan_type === 'full') {
        router.push(`/${locale}/pos`);
        return;
      }
    } catch (error) {
      console.error('Failed to load user data:', error);
      router.push(`/${locale}/register`);
      return;
    } finally {
      setIsLoading(false);
    }
  };

  const refreshUser = async () => {
    await loadUserData();
  };

  useEffect(() => {
    loadUserData();
  }, [router, locale]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen bg-gray-50">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500">Loading...</p>
        </div>
      </div>
    );
  }

  return (
    <LiteContext.Provider value={{ restaurant, user, isLoading, refreshUser }}>
      <div className="min-h-screen bg-gray-50">
        {/* Mobile sidebar overlay */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-black/50 z-40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Sidebar */}
        <LiteSidebar
          isOpen={sidebarOpen}
          onClose={() => setSidebarOpen(false)}
        />

        {/* Main content area */}
        <div className="lg:pl-64">
          <LiteHeader onMenuToggle={() => setSidebarOpen(true)} />
          <main className="p-4 lg:p-6">
            {children}
          </main>
        </div>
      </div>
    </LiteContext.Provider>
  );
}
