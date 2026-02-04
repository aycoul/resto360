'use client';

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useLocale, useTranslations } from 'next-intl';
import { getAccessToken } from '@/lib/api/client';
import { useOnboarding } from '@/lib/hooks/useOnboarding';
import { StepIndicator } from '@/components/onboarding/StepIndicator';
import { RestaurantDetailsStep } from '@/components/onboarding/RestaurantDetailsStep';
import { CategoryStep } from '@/components/onboarding/CategoryStep';
import { MenuItemStep } from '@/components/onboarding/MenuItemStep';
import { QRCodeStep } from '@/components/onboarding/QRCodeStep';

export default function OnboardingPage() {
  const router = useRouter();
  const locale = useLocale();
  const t = useTranslations('onboarding');

  const {
    currentStep,
    completedSteps,
    restaurant,
    category,
    isLoading,
    nextStep,
    prevStep,
    completeStep,
    setCategory,
  } = useOnboarding();

  // Check authentication
  useEffect(() => {
    const token = getAccessToken();
    if (!token && !isLoading) {
      router.push(`/${locale}/register`);
    }
  }, [router, locale, isLoading]);

  // Check if restaurant data is available
  useEffect(() => {
    if (!isLoading && !restaurant) {
      // No restaurant data - redirect to registration
      router.push(`/${locale}/register`);
    }
  }, [isLoading, restaurant, router, locale]);

  // Loading state
  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-emerald-50 to-teal-50">
        <div className="text-center">
          <div className="w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500">Loading...</p>
        </div>
      </div>
    );
  }

  // No restaurant data
  if (!restaurant) {
    return null;
  }

  // Handle step navigation
  const handleDetailsNext = () => {
    completeStep(1);
    nextStep();
  };

  const handleDetailsSkip = () => {
    // Skip details but still complete step
    completeStep(1);
    nextStep();
  };

  const handleCategoryNext = (categoryId: string, categoryName: string) => {
    setCategory({ id: categoryId, name: categoryName });
    completeStep(2);
    nextStep();
  };

  const handleMenuItemNext = () => {
    completeStep(3);
    nextStep();
  };

  const handleQRCodeBack = () => {
    prevStep();
  };

  // Render current step
  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return (
          <RestaurantDetailsStep
            restaurantId={restaurant.id}
            initialName={restaurant.name}
            onNext={handleDetailsNext}
            onSkip={handleDetailsSkip}
          />
        );
      case 2:
        return (
          <CategoryStep
            onNext={handleCategoryNext}
            onBack={prevStep}
          />
        );
      case 3:
        if (!category) {
          // If no category exists yet, go back to step 2
          prevStep();
          return null;
        }
        return (
          <MenuItemStep
            categoryId={category.id}
            categoryName={category.name}
            onNext={handleMenuItemNext}
            onBack={prevStep}
          />
        );
      case 4:
        return (
          <QRCodeStep
            restaurantSlug={restaurant.slug}
            onBack={handleQRCodeBack}
          />
        );
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-teal-50 py-8 px-4">
      <div className="max-w-2xl mx-auto">
        {/* Header */}
        <div className="text-center mb-4">
          <h1 className="text-xl font-bold text-emerald-600">BIZ360</h1>
        </div>

        {/* Step Indicator */}
        <StepIndicator
          currentStep={currentStep}
          completedSteps={completedSteps}
        />

        {/* Step Content Card */}
        <div className="bg-white rounded-2xl shadow-xl p-6 sm:p-8">
          {renderStep()}
        </div>

        {/* Progress hint */}
        <p className="text-center text-gray-400 text-sm mt-6">
          Step {currentStep} of 4
        </p>
      </div>
    </div>
  );
}
