'use client';

import { useState } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import Link from 'next/link';
import type { MenuTheme, ThemeChoices, MenuTemplate, FontChoice, LogoPosition } from '@/lib/api/types';

interface ThemeEditorProps {
  theme: MenuTheme;
  choices: ThemeChoices;
  onSave: (theme: MenuTheme) => Promise<void>;
}

const TEMPLATE_PREVIEWS: Record<MenuTemplate, { description: string; icon: string }> = {
  minimalist: { description: 'Clean and simple', icon: '⬜' },
  elegant: { description: 'Sophisticated style', icon: '🎩' },
  modern: { description: 'Contemporary design', icon: '🔷' },
  casual: { description: 'Friendly and relaxed', icon: '☀️' },
  fine_dining: { description: 'Premium experience', icon: '🍷' },
  vibrant: { description: 'Bold and colorful', icon: '🌈' },
};

export function ThemeEditor({ theme: initialTheme, choices, onSave }: ThemeEditorProps) {
  const t = useTranslations('lite.themes');
  const tCommon = useTranslations('common');
  const locale = useLocale();

  const [theme, setTheme] = useState<MenuTheme>(initialTheme);
  const [isSaving, setIsSaving] = useState(false);
  const [showSaved, setShowSaved] = useState(false);
  const [activeTab, setActiveTab] = useState<'template' | 'colors' | 'typography' | 'layout'>('template');

  const handleChange = (field: keyof MenuTheme, value: unknown) => {
    setTheme({ ...theme, [field]: value });
    setShowSaved(false);
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      await onSave(theme);
      setShowSaved(true);
      setTimeout(() => setShowSaved(false), 3000);
    } catch (error) {
      console.error('Failed to save theme:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const tabs = [
    { id: 'template', label: t('tabs.template'), icon: '🎨' },
    { id: 'colors', label: t('tabs.colors'), icon: '🌈' },
    { id: 'typography', label: t('tabs.typography'), icon: 'Aa' },
    { id: 'layout', label: t('tabs.layout'), icon: '📐' },
  ];

  return (
    <div className="grid lg:grid-cols-2 gap-6">
      {/* Editor Panel */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        {/* Tabs */}
        <div className="flex border-b border-gray-200">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'text-emerald-600 border-b-2 border-emerald-600 bg-emerald-50'
                  : 'text-gray-500 hover:text-gray-700 hover:bg-gray-50'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        <div className="p-6">
          {activeTab === 'template' && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  {t('selectTemplate')}
                </label>
                <div className="grid grid-cols-2 gap-3">
                  {choices.templates.map((template) => {
                    const preview = TEMPLATE_PREVIEWS[template.value as MenuTemplate];
                    return (
                      <button
                        key={template.value}
                        onClick={() => handleChange('template', template.value)}
                        className={`p-4 rounded-xl border-2 text-left transition-all ${
                          theme.template === template.value
                            ? 'border-emerald-500 bg-emerald-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        <span className="text-2xl mb-2 block">{preview?.icon || '📄'}</span>
                        <span className="font-medium text-gray-900 block">{template.label}</span>
                        <span className="text-xs text-gray-500">{preview?.description}</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'colors' && (
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t('primaryColor')}
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      value={theme.primary_color}
                      onChange={(e) => handleChange('primary_color', e.target.value)}
                      className="w-12 h-12 rounded-lg border border-gray-300 cursor-pointer"
                    />
                    <input
                      type="text"
                      value={theme.primary_color}
                      onChange={(e) => handleChange('primary_color', e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm"
                      placeholder="#059669"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t('secondaryColor')}
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      value={theme.secondary_color}
                      onChange={(e) => handleChange('secondary_color', e.target.value)}
                      className="w-12 h-12 rounded-lg border border-gray-300 cursor-pointer"
                    />
                    <input
                      type="text"
                      value={theme.secondary_color}
                      onChange={(e) => handleChange('secondary_color', e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm"
                      placeholder="#14b8a6"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t('backgroundColor')}
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      value={theme.background_color}
                      onChange={(e) => handleChange('background_color', e.target.value)}
                      className="w-12 h-12 rounded-lg border border-gray-300 cursor-pointer"
                    />
                    <input
                      type="text"
                      value={theme.background_color}
                      onChange={(e) => handleChange('background_color', e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm"
                      placeholder="#ffffff"
                    />
                  </div>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    {t('textColor')}
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="color"
                      value={theme.text_color}
                      onChange={(e) => handleChange('text_color', e.target.value)}
                      className="w-12 h-12 rounded-lg border border-gray-300 cursor-pointer"
                    />
                    <input
                      type="text"
                      value={theme.text_color}
                      onChange={(e) => handleChange('text_color', e.target.value)}
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm"
                      placeholder="#111827"
                    />
                  </div>
                </div>
              </div>

              {/* Quick Color Presets */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('colorPresets')}
                </label>
                <div className="flex gap-2">
                  {[
                    { primary: '#059669', secondary: '#14b8a6', name: 'Emerald' },
                    { primary: '#2563eb', secondary: '#3b82f6', name: 'Blue' },
                    { primary: '#7c3aed', secondary: '#8b5cf6', name: 'Purple' },
                    { primary: '#dc2626', secondary: '#ef4444', name: 'Red' },
                    { primary: '#ea580c', secondary: '#f97316', name: 'Orange' },
                    { primary: '#1f2937', secondary: '#374151', name: 'Gray' },
                  ].map((preset) => (
                    <button
                      key={preset.name}
                      onClick={() => {
                        handleChange('primary_color', preset.primary);
                        handleChange('secondary_color', preset.secondary);
                      }}
                      className="w-8 h-8 rounded-full border-2 border-white shadow-md"
                      style={{ backgroundColor: preset.primary }}
                      title={preset.name}
                    />
                  ))}
                </div>
              </div>
            </div>
          )}

          {activeTab === 'typography' && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('headingFont')}
                </label>
                <select
                  value={theme.heading_font}
                  onChange={(e) => handleChange('heading_font', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  {choices.fonts.map((font) => (
                    <option key={font.value} value={font.value}>
                      {font.label}
                    </option>
                  ))}
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('bodyFont')}
                </label>
                <select
                  value={theme.body_font}
                  onChange={(e) => handleChange('body_font', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                >
                  {choices.fonts.map((font) => (
                    <option key={font.value} value={font.value}>
                      {font.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          )}

          {activeTab === 'layout' && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('logoPosition')}
                </label>
                <div className="flex gap-2">
                  {(['left', 'center', 'right'] as LogoPosition[]).map((position) => (
                    <button
                      key={position}
                      onClick={() => handleChange('logo_position', position)}
                      className={`flex-1 py-2 px-4 rounded-lg border-2 capitalize ${
                        theme.logo_position === position
                          ? 'border-emerald-500 bg-emerald-50 text-emerald-700'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      {t(`positions.${position}`)}
                    </button>
                  ))}
                </div>
              </div>

              <div className="space-y-3">
                <label className="block text-sm font-medium text-gray-700">
                  {t('displayOptions')}
                </label>
                {[
                  { key: 'show_prices', label: t('showPrices') },
                  { key: 'show_descriptions', label: t('showDescriptions') },
                  { key: 'show_images', label: t('showImages') },
                  { key: 'compact_mode', label: t('compactMode') },
                ].map((option) => (
                  <label key={option.key} className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={theme[option.key as keyof MenuTheme] as boolean}
                      onChange={(e) => handleChange(option.key as keyof MenuTheme, e.target.checked)}
                      className="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
                    />
                    <span className="text-gray-700">{option.label}</span>
                  </label>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Save Button */}
        <div className="px-6 py-4 bg-gray-50 border-t border-gray-200 flex items-center justify-between">
          <Link
            href={`/${locale}/menu/${theme.id ? 'preview' : 'demo'}`}
            target="_blank"
            className="text-emerald-600 hover:text-emerald-700 text-sm font-medium"
          >
            {t('previewMenu')} →
          </Link>
          <button
            onClick={handleSave}
            disabled={isSaving}
            className="px-6 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 flex items-center gap-2"
          >
            {isSaving ? (
              <>
                <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                {t('saving')}
              </>
            ) : showSaved ? (
              <>
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                {t('saved')}
              </>
            ) : (
              tCommon('save')
            )}
          </button>
        </div>
      </div>

      {/* Preview Panel */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="font-semibold text-gray-900">{t('preview')}</h3>
        </div>
        <div
          className="p-6 min-h-[500px]"
          style={{ backgroundColor: theme.background_color }}
        >
          {/* Preview Header */}
          <div
            className={`mb-6 ${
              theme.logo_position === 'center'
                ? 'text-center'
                : theme.logo_position === 'right'
                ? 'text-right'
                : 'text-left'
            }`}
          >
            <div
              className="w-16 h-16 rounded-full flex items-center justify-center mb-2"
              style={{ backgroundColor: theme.primary_color }}
            >
              <span className="text-white text-xl font-bold">R</span>
            </div>
            <h2
              className="text-2xl font-bold"
              style={{ color: theme.text_color, fontFamily: theme.heading_font }}
            >
              Restaurant Name
            </h2>
          </div>

          {/* Preview Categories */}
          <div className="space-y-4">
            <div
              className="text-lg font-semibold pb-2 border-b"
              style={{
                color: theme.primary_color,
                borderColor: theme.secondary_color,
                fontFamily: theme.heading_font,
              }}
            >
              Main Dishes
            </div>

            {/* Preview Items */}
            <div className={theme.compact_mode ? 'space-y-2' : 'space-y-4'}>
              {[
                { name: 'Kédjenou', price: '4,500 XOF', desc: 'Poulet mijoté aux légumes' },
                { name: 'Garba', price: '1,500 XOF', desc: 'Attiéké au thon frit' },
              ].map((item) => (
                <div
                  key={item.name}
                  className={`flex gap-3 ${theme.compact_mode ? 'py-2' : 'p-3'} rounded-lg`}
                  style={{
                    backgroundColor:
                      theme.background_color === '#ffffff' ? '#f9fafb' : 'rgba(255,255,255,0.1)',
                  }}
                >
                  {theme.show_images && (
                    <div
                      className={`${theme.compact_mode ? 'w-12 h-12' : 'w-16 h-16'} rounded-lg`}
                      style={{ backgroundColor: theme.secondary_color + '40' }}
                    />
                  )}
                  <div className="flex-1">
                    <div className="flex justify-between">
                      <span
                        className="font-medium"
                        style={{ color: theme.text_color, fontFamily: theme.body_font }}
                      >
                        {item.name}
                      </span>
                      {theme.show_prices && (
                        <span
                          className="font-semibold"
                          style={{ color: theme.primary_color }}
                        >
                          {item.price}
                        </span>
                      )}
                    </div>
                    {theme.show_descriptions && (
                      <p
                        className="text-sm opacity-70"
                        style={{ color: theme.text_color, fontFamily: theme.body_font }}
                      >
                        {item.desc}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
