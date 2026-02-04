'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { CategoryCard } from './CategoryCard';
import { MenuItemCard } from './MenuItemCard';

interface Category {
  id: string;
  name: string;
  display_order: number;
  is_visible: boolean;
}

interface MenuItem {
  id: string;
  category: string;
  name: string;
  description: string;
  price: number;
  thumbnail_url: string | null;
  is_available: boolean;
}

interface MenuEditorProps {
  categories: Category[];
  items: MenuItem[];
  onCategoryCreate: (name: string) => Promise<Category>;
  onCategoryUpdate: (id: string, data: Partial<Category>) => Promise<void>;
  onCategoryDelete: (id: string) => Promise<void>;
  onItemCreate: (data: Partial<MenuItem>) => Promise<MenuItem>;
  onItemUpdate: (id: string, data: Partial<MenuItem>) => Promise<void>;
  onItemDelete: (id: string) => Promise<void>;
}

export function MenuEditor({
  categories,
  items,
  onCategoryCreate,
  onCategoryUpdate,
  onCategoryDelete,
  onItemCreate,
  onItemUpdate,
  onItemDelete,
}: MenuEditorProps) {
  const t = useTranslations('lite.menu');
  const tCommon = useTranslations('common');

  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [showCategoryModal, setShowCategoryModal] = useState(false);
  const [showItemModal, setShowItemModal] = useState(false);
  const [editingCategory, setEditingCategory] = useState<Category | null>(null);
  const [editingItem, setEditingItem] = useState<MenuItem | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Filter items by selected category
  const filteredItems = selectedCategory
    ? items.filter((item) => item.category === selectedCategory)
    : items;

  const getItemCount = (categoryId: string) => {
    return items.filter((item) => item.category === categoryId).length;
  };

  // Category Modal
  const CategoryModal = () => {
    const [name, setName] = useState(editingCategory?.name || '');

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      if (!name.trim()) return;

      setIsSubmitting(true);
      try {
        if (editingCategory) {
          await onCategoryUpdate(editingCategory.id, { name });
        } else {
          await onCategoryCreate(name);
        }
        setShowCategoryModal(false);
        setEditingCategory(null);
        setName('');
      } catch (err) {
        console.error('Failed to save category:', err);
      } finally {
        setIsSubmitting(false);
      }
    };

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-xl w-full max-w-md shadow-xl">
          <div className="px-6 py-4 border-b border-gray-100">
            <h3 className="text-lg font-semibold">
              {editingCategory ? t('editCategory') : t('addCategory')}
            </h3>
          </div>
          <form onSubmit={handleSubmit} className="p-6">
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('categoryName')}
              </label>
              <input
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                placeholder={t('categoryName')}
                autoFocus
              />
            </div>
            <div className="flex gap-3 justify-end">
              <button
                type="button"
                onClick={() => {
                  setShowCategoryModal(false);
                  setEditingCategory(null);
                }}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              >
                {tCommon('cancel')}
              </button>
              <button
                type="submit"
                disabled={isSubmitting || !name.trim()}
                className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50"
              >
                {isSubmitting ? t('saving') : tCommon('save')}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  // Item Modal
  const ItemModal = () => {
    const [formData, setFormData] = useState({
      name: editingItem?.name || '',
      price: editingItem?.price?.toString() || '',
      description: editingItem?.description || '',
      category: editingItem?.category || selectedCategory || categories[0]?.id || '',
      is_available: editingItem?.is_available ?? true,
    });

    const handleSubmit = async (e: React.FormEvent) => {
      e.preventDefault();
      if (!formData.name.trim() || !formData.price || !formData.category) return;

      setIsSubmitting(true);
      try {
        const data = {
          name: formData.name,
          price: parseInt(formData.price, 10),
          description: formData.description,
          category: formData.category,
          is_available: formData.is_available,
        };

        if (editingItem) {
          await onItemUpdate(editingItem.id, data);
        } else {
          await onItemCreate(data);
        }
        setShowItemModal(false);
        setEditingItem(null);
      } catch (err) {
        console.error('Failed to save item:', err);
      } finally {
        setIsSubmitting(false);
      }
    };

    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-xl w-full max-w-md shadow-xl max-h-[90vh] overflow-y-auto">
          <div className="px-6 py-4 border-b border-gray-100">
            <h3 className="text-lg font-semibold">
              {editingItem ? t('editItem') : t('addItem')}
            </h3>
          </div>
          <form onSubmit={handleSubmit} className="p-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('itemName')} *
              </label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                placeholder={t('itemName')}
                autoFocus
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('price')} *
              </label>
              <input
                type="number"
                value={formData.price}
                onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                placeholder="0"
                min="0"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('description')}
              </label>
              <textarea
                value={formData.description}
                onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                rows={3}
                placeholder={t('description')}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                {t('allCategories')} *
              </label>
              <select
                value={formData.category}
                onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              >
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                id="is_available"
                checked={formData.is_available}
                onChange={(e) => setFormData({ ...formData, is_available: e.target.checked })}
                className="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
              />
              <label htmlFor="is_available" className="text-sm text-gray-700">
                {t('available')}
              </label>
            </div>

            <div className="flex gap-3 justify-end pt-4">
              <button
                type="button"
                onClick={() => {
                  setShowItemModal(false);
                  setEditingItem(null);
                }}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg"
              >
                {tCommon('cancel')}
              </button>
              <button
                type="submit"
                disabled={isSubmitting || !formData.name.trim() || !formData.price}
                className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50"
              >
                {isSubmitting ? t('saving') : tCommon('save')}
              </button>
            </div>
          </form>
        </div>
      </div>
    );
  };

  return (
    <div className="flex flex-col lg:flex-row gap-6">
      {/* Categories sidebar */}
      <div className="lg:w-72 flex-shrink-0">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
          <div className="p-4 border-b border-gray-100 flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">{t('allCategories')}</h2>
            <button
              onClick={() => {
                setEditingCategory(null);
                setShowCategoryModal(true);
              }}
              className="p-2 text-emerald-600 hover:bg-emerald-50 rounded-lg"
              title={t('addCategory')}
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </button>
          </div>
          <div className="divide-y divide-gray-100">
            {/* All items option */}
            <button
              onClick={() => setSelectedCategory(null)}
              className={`w-full px-4 py-3 text-left flex items-center justify-between hover:bg-gray-50 ${
                selectedCategory === null ? 'bg-emerald-50' : ''
              }`}
            >
              <span className={selectedCategory === null ? 'text-emerald-700 font-medium' : 'text-gray-700'}>
                {t('allCategories')}
              </span>
              <span className="text-sm text-gray-500">{items.length}</span>
            </button>

            {categories.length === 0 ? (
              <div className="p-4 text-center">
                <p className="text-gray-500 text-sm">{t('noCategories')}</p>
                <p className="text-gray-400 text-xs mt-1">{t('noCategoriesDesc')}</p>
              </div>
            ) : (
              categories.map((category) => (
                <CategoryCard
                  key={category.id}
                  category={category}
                  itemCount={getItemCount(category.id)}
                  isSelected={selectedCategory === category.id}
                  onClick={() => setSelectedCategory(category.id)}
                  onEdit={() => {
                    setEditingCategory(category);
                    setShowCategoryModal(true);
                  }}
                  onDelete={async () => {
                    if (confirm(t('deleteCategoryConfirm'))) {
                      await onCategoryDelete(category.id);
                      if (selectedCategory === category.id) {
                        setSelectedCategory(null);
                      }
                    }
                  }}
                />
              ))
            )}
          </div>
        </div>
      </div>

      {/* Items grid */}
      <div className="flex-1">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="p-4 border-b border-gray-100 flex items-center justify-between">
            <h2 className="font-semibold text-gray-900">
              {selectedCategory
                ? categories.find((c) => c.id === selectedCategory)?.name
                : t('allCategories')}
            </h2>
            {categories.length > 0 && (
              <button
                onClick={() => {
                  setEditingItem(null);
                  setShowItemModal(true);
                }}
                className="flex items-center gap-2 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                {t('addItem')}
              </button>
            )}
          </div>

          <div className="p-4">
            {filteredItems.length === 0 ? (
              <div className="text-center py-12">
                <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </div>
                <p className="text-gray-500">{t('noItems')}</p>
                <p className="text-gray-400 text-sm mt-1">{t('noItemsDesc')}</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
                {filteredItems.map((item) => (
                  <MenuItemCard
                    key={item.id}
                    item={item}
                    categoryName={categories.find((c) => c.id === item.category)?.name || ''}
                    onEdit={() => {
                      setEditingItem(item);
                      setShowItemModal(true);
                    }}
                    onDelete={async () => {
                      if (confirm(t('deleteItemConfirm'))) {
                        await onItemDelete(item.id);
                      }
                    }}
                    onToggleAvailability={async () => {
                      await onItemUpdate(item.id, { is_available: !item.is_available });
                    }}
                  />
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Modals */}
      {showCategoryModal && <CategoryModal />}
      {showItemModal && <ItemModal />}
    </div>
  );
}
