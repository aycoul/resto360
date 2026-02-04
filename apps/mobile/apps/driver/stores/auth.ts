/**
 * Auth store using Zustand for state management.
 * Handles driver authentication, token storage, and profile management.
 */
import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';

interface User {
  id: string;
  first_name: string;
  last_name: string;
  phone: string;
  role: string;
  restaurant_id: string;
}

interface Driver {
  id: string;
  user_name?: string;
  phone: string;
  vehicle_type: string;
  vehicle_plate?: string;
  is_available: boolean;
  total_deliveries: number;
  average_rating: number;
}

interface AuthState {
  user: User | null;
  driver: Driver | null;
  accessToken: string | null;
  refreshToken: string | null;
  isLoading: boolean;
  isAuthenticated: boolean;

  // Actions
  login: (phone: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  loadStoredAuth: () => Promise<void>;
  refreshAccessToken: () => Promise<void>;
  updateDriver: (driver: Partial<Driver>) => void;
}

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

export const useAuthStore = create<AuthState>((set, get) => ({
  user: null,
  driver: null,
  accessToken: null,
  refreshToken: null,
  isLoading: true,
  isAuthenticated: false,

  login: async (phone: string, password: string) => {
    set({ isLoading: true });

    try {
      // Get tokens
      const tokenResponse = await fetch(`${API_URL}/api/v1/auth/token/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone, password }),
      });

      if (!tokenResponse.ok) {
        const errorData = await tokenResponse.json().catch(() => ({}));
        throw new Error(errorData.detail || 'Invalid credentials');
      }

      const { access, refresh } = await tokenResponse.json();

      // Get user profile
      const userResponse = await fetch(`${API_URL}/api/v1/auth/me/`, {
        headers: { Authorization: `Bearer ${access}` },
      });

      if (!userResponse.ok) {
        throw new Error('Failed to get user profile');
      }

      const user = await userResponse.json();

      if (user.role !== 'driver') {
        throw new Error('This app is for drivers only');
      }

      // Get driver profile
      const driverResponse = await fetch(`${API_URL}/api/v1/delivery/drivers/me/`, {
        headers: { Authorization: `Bearer ${access}` },
      });

      let driver = null;
      if (driverResponse.ok) {
        driver = await driverResponse.json();
      }

      // Store tokens securely
      await SecureStore.setItemAsync('accessToken', access);
      await SecureStore.setItemAsync('refreshToken', refresh);
      await SecureStore.setItemAsync('user', JSON.stringify(user));
      if (driver) {
        await SecureStore.setItemAsync('driver', JSON.stringify(driver));
      }

      set({
        user,
        driver,
        accessToken: access,
        refreshToken: refresh,
        isAuthenticated: true,
        isLoading: false,
      });
    } catch (error) {
      set({ isLoading: false });
      throw error;
    }
  },

  logout: async () => {
    await SecureStore.deleteItemAsync('accessToken');
    await SecureStore.deleteItemAsync('refreshToken');
    await SecureStore.deleteItemAsync('user');
    await SecureStore.deleteItemAsync('driver');

    set({
      user: null,
      driver: null,
      accessToken: null,
      refreshToken: null,
      isAuthenticated: false,
    });
  },

  loadStoredAuth: async () => {
    try {
      const accessToken = await SecureStore.getItemAsync('accessToken');
      const refreshToken = await SecureStore.getItemAsync('refreshToken');
      const userStr = await SecureStore.getItemAsync('user');
      const driverStr = await SecureStore.getItemAsync('driver');

      if (accessToken && userStr) {
        const user = JSON.parse(userStr);
        const driver = driverStr ? JSON.parse(driverStr) : null;

        set({
          accessToken,
          refreshToken,
          user,
          driver,
          isAuthenticated: true,
          isLoading: false,
        });
      } else {
        set({ isLoading: false });
      }
    } catch {
      set({ isLoading: false });
    }
  },

  refreshAccessToken: async () => {
    const { refreshToken } = get();
    if (!refreshToken) return;

    try {
      const response = await fetch(`${API_URL}/api/v1/auth/token/refresh/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ refresh: refreshToken }),
      });

      if (response.ok) {
        const { access } = await response.json();
        await SecureStore.setItemAsync('accessToken', access);
        set({ accessToken: access });
      } else {
        // Refresh token invalid, logout
        await get().logout();
      }
    } catch {
      await get().logout();
    }
  },

  updateDriver: (updates: Partial<Driver>) => {
    const { driver } = get();
    if (driver) {
      const updated = { ...driver, ...updates };
      set({ driver: updated });
      SecureStore.setItemAsync('driver', JSON.stringify(updated));
    }
  },
}));
