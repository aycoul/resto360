'use client';

import { useState, useEffect, useCallback } from 'react';

interface RestaurantInfo {
  id: string;
  name: string;
  slug: string;
}

interface CategoryInfo {
  id: string;
  name: string;
}

interface OnboardingState {
  currentStep: number;
  completedSteps: number[];
  restaurant: RestaurantInfo | null;
  category: CategoryInfo | null;
}

const STORAGE_KEY = 'resto360_onboarding';

const initialState: OnboardingState = {
  currentStep: 1,
  completedSteps: [],
  restaurant: null,
  category: null,
};

export function useOnboarding() {
  const [state, setState] = useState<OnboardingState>(initialState);
  const [isLoading, setIsLoading] = useState(true);

  // Load state from localStorage on mount
  useEffect(() => {
    if (typeof window === 'undefined') {
      setIsLoading(false);
      return;
    }

    try {
      // First check for restaurant info from registration
      const registrationData = sessionStorage.getItem('onboarding_restaurant');
      let restaurant: RestaurantInfo | null = null;

      if (registrationData) {
        restaurant = JSON.parse(registrationData);
      }

      // Then load full onboarding state
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored) as OnboardingState;
        setState({
          ...parsed,
          // Use fresh restaurant data from registration if available
          restaurant: restaurant || parsed.restaurant,
        });
      } else if (restaurant) {
        // Fresh start with restaurant from registration
        setState({
          ...initialState,
          restaurant,
        });
      }
    } catch (error) {
      console.error('Failed to load onboarding state:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // Persist state to localStorage whenever it changes
  useEffect(() => {
    if (typeof window === 'undefined' || isLoading) return;

    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
    } catch (error) {
      console.error('Failed to save onboarding state:', error);
    }
  }, [state, isLoading]);

  const nextStep = useCallback(() => {
    setState(prev => ({
      ...prev,
      currentStep: Math.min(prev.currentStep + 1, 4),
    }));
  }, []);

  const prevStep = useCallback(() => {
    setState(prev => ({
      ...prev,
      currentStep: Math.max(prev.currentStep - 1, 1),
    }));
  }, []);

  const goToStep = useCallback((step: number) => {
    if (step >= 1 && step <= 4) {
      setState(prev => ({
        ...prev,
        currentStep: step,
      }));
    }
  }, []);

  const completeStep = useCallback((step: number) => {
    setState(prev => ({
      ...prev,
      completedSteps: prev.completedSteps.includes(step)
        ? prev.completedSteps
        : [...prev.completedSteps, step].sort((a, b) => a - b),
    }));
  }, []);

  const setRestaurant = useCallback((restaurant: RestaurantInfo) => {
    setState(prev => ({
      ...prev,
      restaurant,
    }));
  }, []);

  const setCategory = useCallback((category: CategoryInfo) => {
    setState(prev => ({
      ...prev,
      category,
    }));
  }, []);

  const getProgress = useCallback(() => {
    return {
      current: state.currentStep,
      total: 4,
      percentage: (state.completedSteps.length / 4) * 100,
    };
  }, [state.currentStep, state.completedSteps.length]);

  const resetOnboarding = useCallback(() => {
    setState(initialState);
    if (typeof window !== 'undefined') {
      localStorage.removeItem(STORAGE_KEY);
      sessionStorage.removeItem('onboarding_restaurant');
    }
  }, []);

  const isStepCompleted = useCallback((step: number) => {
    return state.completedSteps.includes(step);
  }, [state.completedSteps]);

  return {
    // State
    currentStep: state.currentStep,
    completedSteps: state.completedSteps,
    restaurant: state.restaurant,
    category: state.category,
    isLoading,

    // Actions
    nextStep,
    prevStep,
    goToStep,
    completeStep,
    setRestaurant,
    setCategory,
    getProgress,
    resetOnboarding,
    isStepCompleted,
  };
}
