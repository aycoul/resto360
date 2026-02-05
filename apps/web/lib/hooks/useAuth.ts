'use client';

import { useState, useEffect, useCallback } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { getAccessToken, clearTokens } from '@/lib/api/client';

interface UseAuthOptions {
  required?: boolean;
  redirectTo?: string;
}

export function useAuth(options: UseAuthOptions = {}) {
  const { required = false, redirectTo = '/login' } = options;
  const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  useEffect(() => {
    const checkAuth = () => {
      const token = getAccessToken();
      const authenticated = !!token;
      setIsAuthenticated(authenticated);
      setIsLoading(false);

      if (required && !authenticated) {
        // Extract locale from pathname (e.g., /fr/pos -> fr)
        const locale = pathname.split('/')[1] || 'fr';
        router.replace(`/${locale}${redirectTo}`);
      }
    };

    checkAuth();
  }, [required, redirectTo, router, pathname]);

  const logout = useCallback(() => {
    clearTokens();
    setIsAuthenticated(false);
    const locale = pathname.split('/')[1] || 'fr';
    router.replace(`/${locale}/login`);
  }, [router, pathname]);

  return {
    isAuthenticated,
    isLoading,
    logout,
  };
}
