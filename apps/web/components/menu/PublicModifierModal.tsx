'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { LocalMenuItem } from '@/lib/db/schema';
import { Button } from '@/components/ui/Button';

interface PublicModifierModalProps {
  item: LocalMenuItem;
  onClose: () => void;
  onAdd: (modifiers: { optionId: string; optionName: string; priceAdjustment: number }[]) => void;
}

export function PublicModifierModal({ item, onClose, onAdd }: PublicModifierModalProps) {
  const t = useTranslations('common');
  const [selectedOptions, setSelectedOptions] = useState<Record<string, string[]>>({});

  const toggleOption = (modifierId: string, optionId: string, maxSelections: number) => {
    setSelectedOptions(prev => {
      const current = prev[modifierId] || [];
      if (current.includes(optionId)) {
        return { ...prev, [modifierId]: current.filter(id => id !== optionId) };
      }
      if (maxSelections === 1) {
        return { ...prev, [modifierId]: [optionId] };
      }
      if (maxSelections === 0 || current.length < maxSelections) {
        return { ...prev, [modifierId]: [...current, optionId] };
      }
      return prev;
    });
  };

  const handleAdd = () => {
    const missingRequired = item.modifiers.filter(
      m => m.required && (!selectedOptions[m.id] || selectedOptions[m.id].length === 0)
    );
    if (missingRequired.length > 0) {
      alert(`Please select: ${missingRequired.map(m => m.name).join(', ')}`);
      return;
    }

    const modifiers: { optionId: string; optionName: string; priceAdjustment: number }[] = [];
    for (const modifier of item.modifiers) {
      const selected = selectedOptions[modifier.id] || [];
      for (const optionId of selected) {
        const option = modifier.options.find(o => o.id === optionId);
        if (option) {
          modifiers.push({
            optionId: option.id,
            optionName: option.name,
            priceAdjustment: option.priceAdjustment,
          });
        }
      }
    }

    onAdd(modifiers);
  };

  const totalAdjustment = Object.entries(selectedOptions).reduce((sum, [modifierId, optionIds]) => {
    const modifier = item.modifiers.find(m => m.id === modifierId);
    if (!modifier) return sum;
    return sum + optionIds.reduce((optSum, optId) => {
      const option = modifier.options.find(o => o.id === optId);
      return optSum + (option?.priceAdjustment || 0);
    }, 0);
  }, 0);

  return (
    <div className="fixed inset-0 bg-black/50 flex items-end justify-center z-50">
      <div className="bg-white rounded-t-2xl w-full max-w-lg max-h-[80vh] overflow-hidden animate-slide-up">
        {/* Header */}
        <div className="p-4 border-b flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold">{item.name}</h2>
            <p className="text-sm text-gray-500">
              {item.price.toLocaleString()} XOF
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-2xl text-gray-400 hover:text-gray-600 w-8 h-8 flex items-center justify-center"
            aria-label="Close"
          >
            &times;
          </button>
        </div>

        {/* Modifiers */}
        <div className="p-4 overflow-y-auto max-h-[50vh]">
          {item.modifiers.map(modifier => (
            <div key={modifier.id} className="mb-4">
              <h3 className="font-medium mb-2">
                {modifier.name}
                {modifier.required && <span className="text-red-500 ml-1">*</span>}
                {modifier.maxSelections > 1 && (
                  <span className="text-gray-400 text-sm ml-2">
                    (max {modifier.maxSelections})
                  </span>
                )}
              </h3>
              <div className="space-y-2">
                {modifier.options.filter(o => o.isAvailable).map(option => {
                  const isSelected = (selectedOptions[modifier.id] || []).includes(option.id);
                  return (
                    <button
                      key={option.id}
                      onClick={() => toggleOption(modifier.id, option.id, modifier.maxSelections)}
                      className={`w-full p-3 rounded-lg border text-left flex justify-between transition-colors ${
                        isSelected
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <span>{option.name}</span>
                      {option.priceAdjustment !== 0 && (
                        <span className="text-blue-600">
                          {option.priceAdjustment > 0 ? '+' : ''}
                          {option.priceAdjustment.toLocaleString()} XOF
                        </span>
                      )}
                    </button>
                  );
                })}
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="p-4 border-t bg-gray-50">
          <Button onClick={handleAdd} className="w-full" size="lg">
            {t('add')} - {(item.price + totalAdjustment).toLocaleString()} XOF
          </Button>
        </div>
      </div>
    </div>
  );
}
