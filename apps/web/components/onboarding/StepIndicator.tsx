'use client';

import { useTranslations } from 'next-intl';

interface StepIndicatorProps {
  currentStep: number;
  completedSteps: number[];
}

export function StepIndicator({ currentStep, completedSteps }: StepIndicatorProps) {
  const t = useTranslations('onboarding.steps');

  const steps = [
    { key: 1, label: t('details') },
    { key: 2, label: t('category') },
    { key: 3, label: t('menuItem') },
    { key: 4, label: t('qrCode') },
  ];

  return (
    <div className="w-full py-6">
      <div className="flex items-center justify-between">
        {steps.map((step, index) => {
          const isCompleted = completedSteps.includes(step.key);
          const isCurrent = currentStep === step.key;
          const isLast = index === steps.length - 1;

          return (
            <div key={step.key} className="flex items-center flex-1">
              {/* Step circle and label */}
              <div className="flex flex-col items-center">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-semibold transition-all ${
                    isCompleted
                      ? 'bg-emerald-500 text-white'
                      : isCurrent
                      ? 'bg-emerald-100 text-emerald-700 ring-2 ring-emerald-500 ring-offset-2'
                      : 'bg-gray-100 text-gray-400'
                  }`}
                >
                  {isCompleted ? (
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : (
                    step.key
                  )}
                </div>
                <span
                  className={`mt-2 text-xs font-medium whitespace-nowrap ${
                    isCompleted || isCurrent ? 'text-gray-900' : 'text-gray-400'
                  }`}
                >
                  {step.label}
                </span>
              </div>

              {/* Connector line */}
              {!isLast && (
                <div
                  className={`flex-1 h-0.5 mx-2 ${
                    isCompleted ? 'bg-emerald-500' : 'bg-gray-200'
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
