'use client';

import { useTranslations } from 'next-intl';
import type { AllergenType, DietaryTagType, SpiceLevel } from '@/lib/api/types';

interface MenuMetadataEditorProps {
  allergens: AllergenType[];
  dietaryTags: DietaryTagType[];
  spiceLevel: SpiceLevel;
  prepTimeMinutes: number | null;
  ingredients: string;
  calories: number | null;
  proteinGrams: number | null;
  carbsGrams: number | null;
  fatGrams: number | null;
  fiberGrams: number | null;
  sodiumMg: number | null;
  onChange: (field: string, value: unknown) => void;
}

const ALLERGENS: AllergenType[] = [
  'celery', 'gluten', 'crustaceans', 'eggs', 'fish', 'lupin',
  'milk', 'molluscs', 'mustard', 'nuts', 'peanuts', 'sesame', 'soya', 'sulphites'
];

const DIETARY_TAGS: DietaryTagType[] = [
  'vegan', 'vegetarian', 'gluten_free', 'dairy_free', 'halal',
  'kosher', 'keto', 'low_carb', 'nut_free', 'organic'
];

const SPICE_LEVELS: SpiceLevel[] = [0, 1, 2, 3, 4];

export function MenuMetadataEditor({
  allergens,
  dietaryTags,
  spiceLevel,
  prepTimeMinutes,
  ingredients,
  calories,
  proteinGrams,
  carbsGrams,
  fatGrams,
  fiberGrams,
  sodiumMg,
  onChange,
}: MenuMetadataEditorProps) {
  const t = useTranslations('lite.menu.metadata');

  const toggleAllergen = (allergen: AllergenType) => {
    const newAllergens = allergens.includes(allergen)
      ? allergens.filter((a) => a !== allergen)
      : [...allergens, allergen];
    onChange('allergens', newAllergens);
  };

  const toggleDietaryTag = (tag: DietaryTagType) => {
    const newTags = dietaryTags.includes(tag)
      ? dietaryTags.filter((t) => t !== tag)
      : [...dietaryTags, tag];
    onChange('dietary_tags', newTags);
  };

  return (
    <div className="space-y-6 border-t border-gray-200 pt-6 mt-6">
      <h4 className="font-medium text-gray-900">{t('title')}</h4>

      {/* Allergens */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {t('allergens')}
        </label>
        <p className="text-xs text-gray-500 mb-3">{t('allergensHelp')}</p>
        <div className="flex flex-wrap gap-2">
          {ALLERGENS.map((allergen) => (
            <button
              key={allergen}
              type="button"
              onClick={() => toggleAllergen(allergen)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                allergens.includes(allergen)
                  ? 'bg-red-100 text-red-700 border-2 border-red-300'
                  : 'bg-gray-100 text-gray-600 border-2 border-transparent hover:bg-gray-200'
              }`}
            >
              {t(`allergenLabels.${allergen}`)}
            </button>
          ))}
        </div>
      </div>

      {/* Dietary Tags */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {t('dietaryTags')}
        </label>
        <p className="text-xs text-gray-500 mb-3">{t('dietaryTagsHelp')}</p>
        <div className="flex flex-wrap gap-2">
          {DIETARY_TAGS.map((tag) => (
            <button
              key={tag}
              type="button"
              onClick={() => toggleDietaryTag(tag)}
              className={`px-3 py-1.5 rounded-full text-sm font-medium transition-colors ${
                dietaryTags.includes(tag)
                  ? 'bg-emerald-100 text-emerald-700 border-2 border-emerald-300'
                  : 'bg-gray-100 text-gray-600 border-2 border-transparent hover:bg-gray-200'
              }`}
            >
              {t(`dietaryLabels.${tag}`)}
            </button>
          ))}
        </div>
      </div>

      {/* Spice Level */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {t('spiceLevel')}
        </label>
        <div className="flex gap-2">
          {SPICE_LEVELS.map((level) => (
            <button
              key={level}
              type="button"
              onClick={() => onChange('spice_level', level)}
              className={`flex-1 py-2 px-3 rounded-lg text-sm font-medium transition-colors ${
                spiceLevel === level
                  ? level === 0
                    ? 'bg-gray-200 text-gray-800'
                    : level <= 2
                    ? 'bg-yellow-100 text-yellow-800'
                    : 'bg-red-100 text-red-800'
                  : 'bg-gray-50 text-gray-600 hover:bg-gray-100'
              }`}
            >
              {level === 0 ? '' : '🌶️'.repeat(level)}
              <span className="block text-xs mt-1">{t(`spiceLevels.${level}`)}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Prep Time */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {t('prepTime')}
        </label>
        <div className="flex items-center gap-2">
          <input
            type="number"
            value={prepTimeMinutes ?? ''}
            onChange={(e) => onChange('prep_time_minutes', e.target.value ? parseInt(e.target.value) : null)}
            className="w-24 px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            placeholder="15"
            min="0"
            max="300"
          />
          <span className="text-gray-500 text-sm">min</span>
        </div>
      </div>

      {/* Ingredients */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {t('ingredients')}
        </label>
        <p className="text-xs text-gray-500 mb-2">{t('ingredientsHelp')}</p>
        <textarea
          value={ingredients}
          onChange={(e) => onChange('ingredients', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
          rows={2}
          placeholder="Rice, fish, tomatoes, onions..."
        />
      </div>

      {/* Nutrition Info */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {t('nutrition')}
        </label>
        <p className="text-xs text-gray-500 mb-3">{t('nutritionHelp')}</p>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          <div>
            <label className="block text-xs text-gray-500 mb-1">{t('calories')}</label>
            <input
              type="number"
              value={calories ?? ''}
              onChange={(e) => onChange('calories', e.target.value ? parseInt(e.target.value) : null)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 text-sm"
              placeholder="350"
              min="0"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">{t('protein')}</label>
            <input
              type="number"
              step="0.1"
              value={proteinGrams ?? ''}
              onChange={(e) => onChange('protein_grams', e.target.value ? parseFloat(e.target.value) : null)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 text-sm"
              placeholder="25"
              min="0"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">{t('carbs')}</label>
            <input
              type="number"
              step="0.1"
              value={carbsGrams ?? ''}
              onChange={(e) => onChange('carbs_grams', e.target.value ? parseFloat(e.target.value) : null)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 text-sm"
              placeholder="45"
              min="0"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">{t('fat')}</label>
            <input
              type="number"
              step="0.1"
              value={fatGrams ?? ''}
              onChange={(e) => onChange('fat_grams', e.target.value ? parseFloat(e.target.value) : null)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 text-sm"
              placeholder="12"
              min="0"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">{t('fiber')}</label>
            <input
              type="number"
              step="0.1"
              value={fiberGrams ?? ''}
              onChange={(e) => onChange('fiber_grams', e.target.value ? parseFloat(e.target.value) : null)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 text-sm"
              placeholder="5"
              min="0"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-500 mb-1">{t('sodium')}</label>
            <input
              type="number"
              value={sodiumMg ?? ''}
              onChange={(e) => onChange('sodium_mg', e.target.value ? parseInt(e.target.value) : null)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 text-sm"
              placeholder="600"
              min="0"
            />
          </div>
        </div>
      </div>
    </div>
  );
}
