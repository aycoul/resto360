'use client';

import type { AllergenType, DietaryTagType, SpiceLevel } from '@/lib/api/types';

interface MenuItemBadgesProps {
  allergens?: AllergenType[];
  dietaryTags?: DietaryTagType[];
  spiceLevel?: SpiceLevel;
  prepTimeMinutes?: number | null;
  compact?: boolean;
}

const ALLERGEN_ICONS: Record<AllergenType, string> = {
  celery: '🥬',
  gluten: '🌾',
  crustaceans: '🦐',
  eggs: '🥚',
  fish: '🐟',
  lupin: '🌸',
  milk: '🥛',
  molluscs: '🦪',
  mustard: '🟡',
  nuts: '🥜',
  peanuts: '🥜',
  sesame: '⚪',
  soya: '🫘',
  sulphites: '🍷',
};

const DIETARY_ICONS: Record<DietaryTagType, { icon: string; color: string }> = {
  vegan: { icon: '🌱', color: 'bg-green-100 text-green-800' },
  vegetarian: { icon: '🥬', color: 'bg-green-100 text-green-800' },
  gluten_free: { icon: 'GF', color: 'bg-amber-100 text-amber-800' },
  dairy_free: { icon: 'DF', color: 'bg-blue-100 text-blue-800' },
  halal: { icon: '☪️', color: 'bg-emerald-100 text-emerald-800' },
  kosher: { icon: '✡️', color: 'bg-purple-100 text-purple-800' },
  keto: { icon: 'K', color: 'bg-orange-100 text-orange-800' },
  low_carb: { icon: 'LC', color: 'bg-yellow-100 text-yellow-800' },
  nut_free: { icon: '🚫🥜', color: 'bg-red-100 text-red-800' },
  organic: { icon: '🌿', color: 'bg-lime-100 text-lime-800' },
};

const DIETARY_LABELS: Record<DietaryTagType, string> = {
  vegan: 'Vegan',
  vegetarian: 'Vegetarian',
  gluten_free: 'Gluten-Free',
  dairy_free: 'Dairy-Free',
  halal: 'Halal',
  kosher: 'Kosher',
  keto: 'Keto',
  low_carb: 'Low Carb',
  nut_free: 'Nut-Free',
  organic: 'Organic',
};

export function MenuItemBadges({
  allergens = [],
  dietaryTags = [],
  spiceLevel = 0,
  prepTimeMinutes,
  compact = false,
}: MenuItemBadgesProps) {
  if (allergens.length === 0 && dietaryTags.length === 0 && spiceLevel === 0 && !prepTimeMinutes) {
    return null;
  }

  return (
    <div className={`flex flex-wrap gap-1.5 ${compact ? '' : 'mt-2'}`}>
      {/* Dietary Tags */}
      {dietaryTags.map((tag) => {
        const { icon, color } = DIETARY_ICONS[tag];
        return (
          <span
            key={tag}
            className={`inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium ${color}`}
            title={DIETARY_LABELS[tag]}
          >
            <span>{icon}</span>
            {!compact && <span>{DIETARY_LABELS[tag]}</span>}
          </span>
        );
      })}

      {/* Spice Level */}
      {spiceLevel > 0 && (
        <span
          className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
            spiceLevel <= 2 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
          }`}
          title={`Spice Level: ${spiceLevel}`}
        >
          {'🌶️'.repeat(spiceLevel)}
        </span>
      )}

      {/* Prep Time */}
      {prepTimeMinutes && (
        <span
          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-gray-100 text-gray-700"
          title="Preparation time"
        >
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          {prepTimeMinutes}m
        </span>
      )}

      {/* Allergens (show as warning) */}
      {allergens.length > 0 && (
        <span
          className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium bg-red-50 text-red-700 border border-red-200"
          title={`Contains: ${allergens.join(', ')}`}
        >
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
          </svg>
          {compact ? allergens.length : `${allergens.length} allergen${allergens.length > 1 ? 's' : ''}`}
        </span>
      )}
    </div>
  );
}

// Expanded allergen list for item detail view
export function AllergenList({ allergens }: { allergens: AllergenType[] }) {
  if (allergens.length === 0) return null;

  return (
    <div className="mt-3 p-3 bg-red-50 rounded-lg border border-red-100">
      <div className="flex items-center gap-2 text-red-700 text-sm font-medium mb-2">
        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
        Contains Allergens
      </div>
      <div className="flex flex-wrap gap-2">
        {allergens.map((allergen) => (
          <span
            key={allergen}
            className="inline-flex items-center gap-1 px-2 py-1 bg-white rounded-md text-xs text-red-600 border border-red-200"
          >
            <span>{ALLERGEN_ICONS[allergen]}</span>
            <span className="capitalize">{allergen}</span>
          </span>
        ))}
      </div>
    </div>
  );
}

// Nutrition info display
export function NutritionInfo({
  calories,
  protein,
  carbs,
  fat,
}: {
  calories?: number | null;
  protein?: number | null;
  carbs?: number | null;
  fat?: number | null;
}) {
  if (!calories && !protein && !carbs && !fat) return null;

  return (
    <div className="mt-3 p-3 bg-gray-50 rounded-lg">
      <div className="text-xs text-gray-500 font-medium mb-2">Nutrition (per serving)</div>
      <div className="grid grid-cols-4 gap-2 text-center">
        {calories !== undefined && calories !== null && (
          <div>
            <div className="text-lg font-bold text-gray-900">{calories}</div>
            <div className="text-xs text-gray-500">Cal</div>
          </div>
        )}
        {protein !== undefined && protein !== null && (
          <div>
            <div className="text-lg font-bold text-gray-900">{protein}g</div>
            <div className="text-xs text-gray-500">Protein</div>
          </div>
        )}
        {carbs !== undefined && carbs !== null && (
          <div>
            <div className="text-lg font-bold text-gray-900">{carbs}g</div>
            <div className="text-xs text-gray-500">Carbs</div>
          </div>
        )}
        {fat !== undefined && fat !== null && (
          <div>
            <div className="text-lg font-bold text-gray-900">{fat}g</div>
            <div className="text-xs text-gray-500">Fat</div>
          </div>
        )}
      </div>
    </div>
  );
}
