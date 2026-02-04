'use client';

import { useState, useRef } from 'react';
import { useTranslations } from 'next-intl';
import { api } from '@/lib/api/client';
import type {
  MenuImportBatch,
  ImportedMenuItem,
  AIPhotoAnalysis,
  AIPriceSuggestion,
} from '@/lib/api/types';

type TabType = 'import' | 'ocr' | 'generate' | 'translate';

export default function AIBuilderPage() {
  const t = useTranslations('lite.aiBuilder');
  const tCommon = useTranslations('common');

  const [activeTab, setActiveTab] = useState<TabType>('import');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Import state
  const [importBatch, setImportBatch] = useState<MenuImportBatch | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // OCR state
  const [ocrImage, setOcrImage] = useState<File | null>(null);
  const [ocrPreview, setOcrPreview] = useState<string | null>(null);

  // Generate state
  const [generateForm, setGenerateForm] = useState({
    item_name: '',
    category: '',
    ingredients: '',
    language: 'en' as 'en' | 'fr',
  });
  const [generatedDescription, setGeneratedDescription] = useState<string | null>(null);

  // Price suggestion state
  const [priceForm, setPriceForm] = useState({
    item_name: '',
    category: '',
    description: '',
  });
  const [priceSuggestion, setPriceSuggestion] = useState<AIPriceSuggestion | null>(null);

  // Translate state
  const [translateForm, setTranslateForm] = useState({
    name: '',
    description: '',
    source_lang: 'fr' as 'en' | 'fr',
    target_lang: 'en' as 'en' | 'fr',
  });
  const [translatedItem, setTranslatedItem] = useState<{ name: string; description: string | null } | null>(null);

  const tabs = [
    { id: 'import' as TabType, label: t('tabs.import'), icon: '📁' },
    { id: 'ocr' as TabType, label: t('tabs.ocr'), icon: '📷' },
    { id: 'generate' as TabType, label: t('tabs.generate'), icon: '✨' },
    { id: 'translate' as TabType, label: t('tabs.translate'), icon: '🌐' },
  ];

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setIsLoading(true);
    setError(null);
    setSuccess(null);
    setImportBatch(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await api.postFormData<MenuImportBatch>('/api/v1/ai/import/file/', formData);
      setImportBatch(response);
      if (response.errors.length > 0) {
        setError(t('importWarnings', { count: response.errors.length }));
      }
    } catch (err) {
      console.error('Import error:', err);
      setError(t('importError'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleConfirmImport = async () => {
    if (!importBatch) return;

    setIsLoading(true);
    setError(null);

    try {
      await api.post(`/api/v1/ai/import/${importBatch.id}/confirm/`, {
        items: importBatch.items,
        create_categories: true,
      });
      setSuccess(t('importSuccess', { count: importBatch.items.length }));
      setImportBatch(null);
    } catch (err) {
      console.error('Confirm error:', err);
      setError(t('importConfirmError'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleOCRUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setOcrImage(file);
    setOcrPreview(URL.createObjectURL(file));
  };

  const handleOCRExtract = async () => {
    if (!ocrImage) return;

    setIsLoading(true);
    setError(null);
    setImportBatch(null);

    const formData = new FormData();
    formData.append('image', ocrImage);
    formData.append('language', 'fr');

    try {
      const response = await api.postFormData<MenuImportBatch>('/api/v1/ai/ocr/menu/', formData);
      setImportBatch(response);
      setActiveTab('import'); // Switch to import tab to review
    } catch (err) {
      console.error('OCR error:', err);
      setError(t('ocrError'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleGenerateDescription = async () => {
    if (!generateForm.item_name || !generateForm.category) return;

    setIsLoading(true);
    setError(null);
    setGeneratedDescription(null);

    try {
      const response = await api.post<{ description: string }>('/api/v1/ai/generate/description/', {
        ...generateForm,
        cuisine_type: 'West African',
      });
      setGeneratedDescription(response.description);
    } catch (err) {
      console.error('Generate error:', err);
      setError(t('generateError'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleSuggestPrice = async () => {
    if (!priceForm.item_name || !priceForm.category) return;

    setIsLoading(true);
    setError(null);
    setPriceSuggestion(null);

    try {
      const response = await api.post<AIPriceSuggestion>('/api/v1/ai/generate/price/', {
        ...priceForm,
        location: 'Abidjan, Côte d\'Ivoire',
        currency: 'XOF',
      });
      setPriceSuggestion(response);
    } catch (err) {
      console.error('Price suggestion error:', err);
      setError(t('priceError'));
    } finally {
      setIsLoading(false);
    }
  };

  const handleTranslate = async () => {
    if (!translateForm.name) return;

    setIsLoading(true);
    setError(null);
    setTranslatedItem(null);

    try {
      const response = await api.post<{ name: string; description: string | null }>('/api/v1/ai/translate/item/', translateForm);
      setTranslatedItem(response);
    } catch (err) {
      console.error('Translate error:', err);
      setError(t('translateError'));
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{t('title')}</h1>
        <p className="text-gray-500 mt-1">{t('subtitle')}</p>
      </div>

      {/* Alerts */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
          {error}
        </div>
      )}
      {success && (
        <div className="mb-4 p-4 bg-green-50 border border-green-200 rounded-lg text-green-700">
          {success}
        </div>
      )}

      {/* Tabs */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
        <div className="flex border-b border-gray-200 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-shrink-0 px-4 py-3 text-sm font-medium transition-colors ${
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

        <div className="p-6">
          {/* Import Tab */}
          {activeTab === 'import' && (
            <div className="space-y-6">
              {!importBatch ? (
                <div className="text-center py-12 border-2 border-dashed border-gray-300 rounded-lg">
                  <div className="text-4xl mb-4">📁</div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">{t('importUpload')}</h3>
                  <p className="text-gray-500 mb-4">{t('importFormats')}</p>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept=".csv,.xlsx,.xls"
                    onChange={handleFileUpload}
                    className="hidden"
                  />
                  <button
                    onClick={() => fileInputRef.current?.click()}
                    disabled={isLoading}
                    className="px-6 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50"
                  >
                    {isLoading ? t('uploading') : t('selectFile')}
                  </button>
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <h3 className="font-medium text-gray-900">
                        {t('reviewImport', { count: importBatch.valid_items })}
                      </h3>
                      <p className="text-sm text-gray-500">{importBatch.original_filename}</p>
                    </div>
                    <div className="flex gap-2">
                      <button
                        onClick={() => setImportBatch(null)}
                        className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                      >
                        {tCommon('cancel')}
                      </button>
                      <button
                        onClick={handleConfirmImport}
                        disabled={isLoading}
                        className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50"
                      >
                        {isLoading ? t('importing') : t('confirmImport')}
                      </button>
                    </div>
                  </div>

                  {/* Preview items */}
                  <div className="max-h-96 overflow-y-auto border border-gray-200 rounded-lg">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50 sticky top-0">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            {t('columnName')}
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            {t('columnPrice')}
                          </th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">
                            {t('columnCategory')}
                          </th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {importBatch.items.map((item, idx) => (
                          <tr key={idx}>
                            <td className="px-4 py-3 text-sm text-gray-900">{item.name}</td>
                            <td className="px-4 py-3 text-sm text-gray-500">
                              {item.price?.toLocaleString()} XOF
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-500">
                              {item.category || '-'}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  {importBatch.errors.length > 0 && (
                    <div className="p-4 bg-yellow-50 rounded-lg">
                      <h4 className="font-medium text-yellow-800 mb-2">{t('importWarningsTitle')}</h4>
                      <ul className="text-sm text-yellow-700 space-y-1">
                        {importBatch.errors.slice(0, 5).map((err, idx) => (
                          <li key={idx}>• {err}</li>
                        ))}
                        {importBatch.errors.length > 5 && (
                          <li>• {t('moreErrors', { count: importBatch.errors.length - 5 })}</li>
                        )}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}

          {/* OCR Tab */}
          {activeTab === 'ocr' && (
            <div className="space-y-6">
              <div className="text-center py-8 border-2 border-dashed border-gray-300 rounded-lg">
                {ocrPreview ? (
                  <div className="space-y-4">
                    <img
                      src={ocrPreview}
                      alt="Menu preview"
                      className="max-h-64 mx-auto rounded-lg shadow-md"
                    />
                    <div className="flex justify-center gap-2">
                      <button
                        onClick={() => {
                          setOcrImage(null);
                          setOcrPreview(null);
                        }}
                        className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
                      >
                        {t('changeImage')}
                      </button>
                      <button
                        onClick={handleOCRExtract}
                        disabled={isLoading}
                        className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50"
                      >
                        {isLoading ? t('extracting') : t('extractMenu')}
                      </button>
                    </div>
                  </div>
                ) : (
                  <>
                    <div className="text-4xl mb-4">📷</div>
                    <h3 className="text-lg font-medium text-gray-900 mb-2">{t('ocrUpload')}</h3>
                    <p className="text-gray-500 mb-4">{t('ocrDescription')}</p>
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleOCRUpload}
                      className="hidden"
                      id="ocr-upload"
                    />
                    <label
                      htmlFor="ocr-upload"
                      className="inline-block px-6 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 cursor-pointer"
                    >
                      {t('uploadPhoto')}
                    </label>
                  </>
                )}
              </div>
            </div>
          )}

          {/* Generate Tab */}
          {activeTab === 'generate' && (
            <div className="space-y-6">
              <div className="grid md:grid-cols-2 gap-6">
                {/* Description Generator */}
                <div className="space-y-4">
                  <h3 className="font-medium text-gray-900">{t('generateDescription')}</h3>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {t('itemName')}
                    </label>
                    <input
                      type="text"
                      value={generateForm.item_name}
                      onChange={(e) => setGenerateForm({ ...generateForm, item_name: e.target.value })}
                      placeholder={t('itemNamePlaceholder')}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {t('category')}
                    </label>
                    <input
                      type="text"
                      value={generateForm.category}
                      onChange={(e) => setGenerateForm({ ...generateForm, category: e.target.value })}
                      placeholder={t('categoryPlaceholder')}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {t('ingredients')}
                    </label>
                    <input
                      type="text"
                      value={generateForm.ingredients}
                      onChange={(e) => setGenerateForm({ ...generateForm, ingredients: e.target.value })}
                      placeholder={t('ingredientsPlaceholder')}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {t('language')}
                    </label>
                    <select
                      value={generateForm.language}
                      onChange={(e) => setGenerateForm({ ...generateForm, language: e.target.value as 'en' | 'fr' })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    >
                      <option value="en">English</option>
                      <option value="fr">Francais</option>
                    </select>
                  </div>
                  <button
                    onClick={handleGenerateDescription}
                    disabled={isLoading || !generateForm.item_name || !generateForm.category}
                    className="w-full px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50"
                  >
                    {isLoading ? t('generating') : t('generateBtn')}
                  </button>

                  {generatedDescription && (
                    <div className="p-4 bg-emerald-50 rounded-lg">
                      <p className="text-gray-900">{generatedDescription}</p>
                      <button
                        onClick={() => navigator.clipboard.writeText(generatedDescription)}
                        className="mt-2 text-sm text-emerald-600 hover:text-emerald-700"
                      >
                        {t('copyToClipboard')}
                      </button>
                    </div>
                  )}
                </div>

                {/* Price Suggester */}
                <div className="space-y-4">
                  <h3 className="font-medium text-gray-900">{t('suggestPrice')}</h3>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {t('itemName')}
                    </label>
                    <input
                      type="text"
                      value={priceForm.item_name}
                      onChange={(e) => setPriceForm({ ...priceForm, item_name: e.target.value })}
                      placeholder={t('itemNamePlaceholder')}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {t('category')}
                    </label>
                    <input
                      type="text"
                      value={priceForm.category}
                      onChange={(e) => setPriceForm({ ...priceForm, category: e.target.value })}
                      placeholder={t('categoryPlaceholder')}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      {t('descriptionOptional')}
                    </label>
                    <textarea
                      value={priceForm.description}
                      onChange={(e) => setPriceForm({ ...priceForm, description: e.target.value })}
                      placeholder={t('descriptionPlaceholder')}
                      rows={2}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                    />
                  </div>
                  <button
                    onClick={handleSuggestPrice}
                    disabled={isLoading || !priceForm.item_name || !priceForm.category}
                    className="w-full px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50"
                  >
                    {isLoading ? t('suggesting') : t('suggestBtn')}
                  </button>

                  {priceSuggestion && (
                    <div className="p-4 bg-emerald-50 rounded-lg space-y-2">
                      <div className="text-2xl font-bold text-emerald-700">
                        {priceSuggestion.suggested_price.toLocaleString()} XOF
                      </div>
                      <div className="text-sm text-gray-600">
                        {t('priceRange')}: {priceSuggestion.price_range_low.toLocaleString()} - {priceSuggestion.price_range_high.toLocaleString()} XOF
                      </div>
                      <p className="text-sm text-gray-700">{priceSuggestion.reasoning}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* Translate Tab */}
          {activeTab === 'translate' && (
            <div className="space-y-6 max-w-lg mx-auto">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('itemName')}
                </label>
                <input
                  type="text"
                  value={translateForm.name}
                  onChange={(e) => setTranslateForm({ ...translateForm, name: e.target.value })}
                  placeholder={t('itemNamePlaceholder')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('descriptionOptional')}
                </label>
                <textarea
                  value={translateForm.description}
                  onChange={(e) => setTranslateForm({ ...translateForm, description: e.target.value })}
                  placeholder={t('descriptionPlaceholder')}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {t('fromLanguage')}
                  </label>
                  <select
                    value={translateForm.source_lang}
                    onChange={(e) => setTranslateForm({ ...translateForm, source_lang: e.target.value as 'en' | 'fr' })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  >
                    <option value="fr">Francais</option>
                    <option value="en">English</option>
                  </select>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {t('toLanguage')}
                  </label>
                  <select
                    value={translateForm.target_lang}
                    onChange={(e) => setTranslateForm({ ...translateForm, target_lang: e.target.value as 'en' | 'fr' })}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  >
                    <option value="en">English</option>
                    <option value="fr">Francais</option>
                  </select>
                </div>
              </div>
              <button
                onClick={handleTranslate}
                disabled={isLoading || !translateForm.name}
                className="w-full px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50"
              >
                {isLoading ? t('translating') : t('translateBtn')}
              </button>

              {translatedItem && (
                <div className="p-4 bg-emerald-50 rounded-lg space-y-2">
                  <div>
                    <span className="text-sm text-gray-500">{t('translatedName')}:</span>
                    <p className="font-medium text-gray-900">{translatedItem.name}</p>
                  </div>
                  {translatedItem.description && (
                    <div>
                      <span className="text-sm text-gray-500">{t('translatedDescription')}:</span>
                      <p className="text-gray-900">{translatedItem.description}</p>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
