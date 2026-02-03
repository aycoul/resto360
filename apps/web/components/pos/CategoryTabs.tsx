'use client';

import { LocalCategory } from '@/lib/db/schema';

interface CategoryTabsProps {
  categories: (LocalCategory & { items: unknown[] })[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}

export function CategoryTabs({ categories, selectedId, onSelect }: CategoryTabsProps) {
  return (
    <div className="flex gap-2 px-4 py-2 bg-white border-b overflow-x-auto">
      {categories.map(category => (
        <button
          key={category.id}
          onClick={() => onSelect(category.id)}
          className={`px-4 py-2 rounded-lg whitespace-nowrap transition-colors ${
            selectedId === category.id
              ? 'bg-blue-600 text-white'
              : 'bg-gray-100 hover:bg-gray-200'
          }`}
        >
          {category.name}
          <span className="ml-2 text-sm opacity-75">
            ({category.items.length})
          </span>
        </button>
      ))}
    </div>
  );
}
