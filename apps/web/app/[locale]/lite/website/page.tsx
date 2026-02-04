'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { api } from '@/lib/api/client';

interface Website {
  id: string;
  status: string;
  status_display: string;
  template: string;
  template_display: string;
  primary_color: string;
  secondary_color: string;
  background_color: string;
  text_color: string;
  logo_url: string | null;
  cover_image_url: string | null;
  hero_title: string;
  hero_subtitle: string;
  hero_cta_text: string;
  hero_cta_link: string;
  about_title: string;
  about_text: string;
  about_image_url: string | null;
  tagline: string;
  description: string;
  phone: string;
  email: string;
  address: string;
  facebook_url: string;
  instagram_url: string;
  twitter_url: string;
  tiktok_url: string;
  whatsapp_number: string;
  show_menu: boolean;
  show_reservations: boolean;
  show_reviews: boolean;
  show_about: boolean;
  show_contact: boolean;
  show_hours: boolean;
  show_gallery: boolean;
  show_map: boolean;
  subdomain: string | null;
  custom_domain: string;
  custom_domain_verified: boolean;
  meta_title: string;
  meta_description: string;
  public_url: string;
  published_at: string | null;
}

interface Template {
  value: string;
  label: string;
  description: string;
}

type TabType = 'design' | 'content' | 'sections' | 'domain' | 'seo';

export default function WebsitePage() {
  const t = useTranslations('lite.website');
  const [website, setWebsite] = useState<Website | null>(null);
  const [templates, setTemplates] = useState<Template[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<TabType>('design');
  const [subdomainInput, setSubdomainInput] = useState('');
  const [subdomainAvailable, setSubdomainAvailable] = useState<boolean | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [websiteData, templatesData] = await Promise.all([
        api.get<Website>('/api/v1/website/config/'),
        api.get<{ templates: Template[] }>('/api/v1/website/templates/'),
      ]);
      setWebsite(websiteData);
      setTemplates(templatesData.templates);
      setSubdomainInput(websiteData.subdomain || '');
    } catch (error) {
      console.error('Failed to load website data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const updateWebsite = async (updates: Partial<Website>) => {
    if (!website) return;
    setIsSaving(true);
    try {
      const updated = await api.patch<Website>('/api/v1/website/config/', updates);
      setWebsite(updated);
    } catch (error) {
      console.error('Failed to update website:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const publishWebsite = async () => {
    try {
      const updated = await api.post<Website>('/api/v1/website/publish/', {});
      setWebsite(updated);
    } catch (error) {
      console.error('Failed to publish website:', error);
    }
  };

  const unpublishWebsite = async () => {
    try {
      const updated = await api.delete<Website>('/api/v1/website/publish/');
      setWebsite(updated);
    } catch (error) {
      console.error('Failed to unpublish website:', error);
    }
  };

  const checkSubdomain = async () => {
    if (!subdomainInput.trim()) return;
    try {
      const result = await api.get<{ available: boolean }>(`/api/v1/website/check-subdomain/?subdomain=${subdomainInput}`);
      setSubdomainAvailable(result.available);
    } catch (error) {
      setSubdomainAvailable(false);
    }
  };

  const updateSubdomain = async () => {
    if (!subdomainInput.trim() || !subdomainAvailable) return;
    try {
      const updated = await api.post<Website>('/api/v1/website/update-subdomain/', { subdomain: subdomainInput });
      setWebsite(updated);
    } catch (error) {
      console.error('Failed to update subdomain:', error);
    }
  };

  const tabs = [
    { id: 'design' as TabType, label: t('tabs.design'), icon: '🎨' },
    { id: 'content' as TabType, label: t('tabs.content'), icon: '📝' },
    { id: 'sections' as TabType, label: t('tabs.sections'), icon: '📑' },
    { id: 'domain' as TabType, label: t('tabs.domain'), icon: '🌐' },
    { id: 'seo' as TabType, label: t('tabs.seo'), icon: '🔍' },
  ];

  if (isLoading || !website) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('title')}</h1>
          <p className="text-gray-500 mt-1">{t('subtitle')}</p>
        </div>
        <div className="flex gap-3">
          {website.status === 'published' ? (
            <>
              <a
                href={website.public_url}
                target="_blank"
                rel="noopener noreferrer"
                className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
              >
                {t('viewSite')}
              </a>
              <button
                onClick={unpublishWebsite}
                className="px-4 py-2 border border-red-300 text-red-600 rounded-lg hover:bg-red-50"
              >
                {t('unpublish')}
              </button>
            </>
          ) : (
            <button
              onClick={publishWebsite}
              className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700"
            >
              {t('publish')}
            </button>
          )}
        </div>
      </div>

      {/* Status Banner */}
      <div className={`mb-6 p-4 rounded-lg flex items-center gap-3 ${
        website.status === 'published'
          ? 'bg-green-50 border border-green-200'
          : 'bg-yellow-50 border border-yellow-200'
      }`}>
        <div className={`w-3 h-3 rounded-full ${
          website.status === 'published' ? 'bg-green-500' : 'bg-yellow-500'
        }`} />
        <span className={website.status === 'published' ? 'text-green-800' : 'text-yellow-800'}>
          {website.status === 'published'
            ? t('statusPublished')
            : t('statusDraft')
          }
        </span>
        {website.public_url && (
          <a
            href={website.public_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-emerald-600 hover:underline ml-auto"
          >
            {website.public_url}
          </a>
        )}
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 mb-6">
        <div className="flex border-b border-gray-200 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-shrink-0 px-4 py-3 text-sm font-medium transition-colors ${
                activeTab === tab.id
                  ? 'text-emerald-600 border-b-2 border-emerald-600 -mb-px'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              <span className="mr-2">{tab.icon}</span>
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Design Tab */}
      {activeTab === 'design' && (
        <div className="space-y-6">
          {/* Template Selection */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-4">{t('selectTemplate')}</h3>
            <div className="grid md:grid-cols-3 lg:grid-cols-5 gap-4">
              {templates.map((template) => (
                <button
                  key={template.value}
                  onClick={() => updateWebsite({ template: template.value })}
                  className={`p-4 border rounded-lg text-left transition-all ${
                    website.template === template.value
                      ? 'border-emerald-500 bg-emerald-50 ring-2 ring-emerald-500'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className="font-medium text-gray-900">{template.label}</div>
                  <div className="text-sm text-gray-500 mt-1">{template.description}</div>
                </button>
              ))}
            </div>
          </div>

          {/* Colors */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-4">{t('colors')}</h3>
            <div className="grid md:grid-cols-4 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('primaryColor')}
                </label>
                <div className="flex gap-2">
                  <input
                    type="color"
                    value={website.primary_color}
                    onChange={(e) => updateWebsite({ primary_color: e.target.value })}
                    className="w-12 h-10 rounded cursor-pointer"
                  />
                  <input
                    type="text"
                    value={website.primary_color}
                    onChange={(e) => updateWebsite({ primary_color: e.target.value })}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('secondaryColor')}
                </label>
                <div className="flex gap-2">
                  <input
                    type="color"
                    value={website.secondary_color}
                    onChange={(e) => updateWebsite({ secondary_color: e.target.value })}
                    className="w-12 h-10 rounded cursor-pointer"
                  />
                  <input
                    type="text"
                    value={website.secondary_color}
                    onChange={(e) => updateWebsite({ secondary_color: e.target.value })}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('backgroundColor')}
                </label>
                <div className="flex gap-2">
                  <input
                    type="color"
                    value={website.background_color}
                    onChange={(e) => updateWebsite({ background_color: e.target.value })}
                    className="w-12 h-10 rounded cursor-pointer"
                  />
                  <input
                    type="text"
                    value={website.background_color}
                    onChange={(e) => updateWebsite({ background_color: e.target.value })}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('textColor')}
                </label>
                <div className="flex gap-2">
                  <input
                    type="color"
                    value={website.text_color}
                    onChange={(e) => updateWebsite({ text_color: e.target.value })}
                    className="w-12 h-10 rounded cursor-pointer"
                  />
                  <input
                    type="text"
                    value={website.text_color}
                    onChange={(e) => updateWebsite({ text_color: e.target.value })}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Content Tab */}
      {activeTab === 'content' && (
        <div className="space-y-6">
          {/* Hero Section */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-4">{t('heroSection')}</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('heroTitle')}
                </label>
                <input
                  type="text"
                  value={website.hero_title}
                  onChange={(e) => updateWebsite({ hero_title: e.target.value })}
                  placeholder={t('heroTitlePlaceholder')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('heroSubtitle')}
                </label>
                <textarea
                  value={website.hero_subtitle}
                  onChange={(e) => updateWebsite({ hero_subtitle: e.target.value })}
                  placeholder={t('heroSubtitlePlaceholder')}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {t('ctaButtonText')}
                  </label>
                  <input
                    type="text"
                    value={website.hero_cta_text}
                    onChange={(e) => updateWebsite({ hero_cta_text: e.target.value })}
                    placeholder={t('ctaButtonPlaceholder')}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    {t('ctaButtonLink')}
                  </label>
                  <input
                    type="text"
                    value={website.hero_cta_link}
                    onChange={(e) => updateWebsite({ hero_cta_link: e.target.value })}
                    placeholder="#menu"
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* About Section */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-4">{t('aboutSection')}</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('aboutTitle')}
                </label>
                <input
                  type="text"
                  value={website.about_title}
                  onChange={(e) => updateWebsite({ about_title: e.target.value })}
                  placeholder={t('aboutTitlePlaceholder')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('aboutText')}
                </label>
                <textarea
                  value={website.about_text}
                  onChange={(e) => updateWebsite({ about_text: e.target.value })}
                  placeholder={t('aboutTextPlaceholder')}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
            </div>
          </div>

          {/* Contact Info */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-4">{t('contactInfo')}</h3>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('phone')}</label>
                <input
                  type="tel"
                  value={website.phone}
                  onChange={(e) => updateWebsite({ phone: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('email')}</label>
                <input
                  type="email"
                  value={website.email}
                  onChange={(e) => updateWebsite({ email: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('address')}</label>
                <textarea
                  value={website.address}
                  onChange={(e) => updateWebsite({ address: e.target.value })}
                  rows={2}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
            </div>
          </div>

          {/* Social Media */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-4">{t('socialMedia')}</h3>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Facebook</label>
                <input
                  type="url"
                  value={website.facebook_url}
                  onChange={(e) => updateWebsite({ facebook_url: e.target.value })}
                  placeholder="https://facebook.com/..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Instagram</label>
                <input
                  type="url"
                  value={website.instagram_url}
                  onChange={(e) => updateWebsite({ instagram_url: e.target.value })}
                  placeholder="https://instagram.com/..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">TikTok</label>
                <input
                  type="url"
                  value={website.tiktok_url}
                  onChange={(e) => updateWebsite({ tiktok_url: e.target.value })}
                  placeholder="https://tiktok.com/..."
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">WhatsApp</label>
                <input
                  type="tel"
                  value={website.whatsapp_number}
                  onChange={(e) => updateWebsite({ whatsapp_number: e.target.value })}
                  placeholder="+225 07 12 34 56 78"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Sections Tab */}
      {activeTab === 'sections' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="font-semibold text-gray-900 mb-4">{t('toggleSections')}</h3>
          <div className="space-y-4">
            <SectionToggle label={t('showMenu')} checked={website.show_menu} onChange={(v) => updateWebsite({ show_menu: v })} />
            <SectionToggle label={t('showAbout')} checked={website.show_about} onChange={(v) => updateWebsite({ show_about: v })} />
            <SectionToggle label={t('showGallery')} checked={website.show_gallery} onChange={(v) => updateWebsite({ show_gallery: v })} />
            <SectionToggle label={t('showHours')} checked={website.show_hours} onChange={(v) => updateWebsite({ show_hours: v })} />
            <SectionToggle label={t('showReservations')} checked={website.show_reservations} onChange={(v) => updateWebsite({ show_reservations: v })} />
            <SectionToggle label={t('showReviews')} checked={website.show_reviews} onChange={(v) => updateWebsite({ show_reviews: v })} />
            <SectionToggle label={t('showContact')} checked={website.show_contact} onChange={(v) => updateWebsite({ show_contact: v })} />
            <SectionToggle label={t('showMap')} checked={website.show_map} onChange={(v) => updateWebsite({ show_map: v })} />
          </div>
        </div>
      )}

      {/* Domain Tab */}
      {activeTab === 'domain' && (
        <div className="space-y-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-4">{t('subdomain')}</h3>
            <p className="text-sm text-gray-500 mb-4">{t('subdomainDesc')}</p>
            <div className="flex gap-3">
              <div className="flex-1 flex">
                <input
                  type="text"
                  value={subdomainInput}
                  onChange={(e) => {
                    setSubdomainInput(e.target.value.toLowerCase());
                    setSubdomainAvailable(null);
                  }}
                  placeholder="my-restaurant"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-l-lg"
                />
                <span className="px-3 py-2 bg-gray-100 border border-l-0 border-gray-300 rounded-r-lg text-gray-500">
                  .resto360.com
                </span>
              </div>
              <button
                onClick={checkSubdomain}
                className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
              >
                {t('check')}
              </button>
              <button
                onClick={updateSubdomain}
                disabled={!subdomainAvailable}
                className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {t('save')}
              </button>
            </div>
            {subdomainAvailable !== null && (
              <p className={`mt-2 text-sm ${subdomainAvailable ? 'text-green-600' : 'text-red-600'}`}>
                {subdomainAvailable ? t('subdomainAvailable') : t('subdomainTaken')}
              </p>
            )}
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-4">{t('customDomain')}</h3>
            <p className="text-sm text-gray-500 mb-4">{t('customDomainDesc')}</p>
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <p className="text-yellow-800 text-sm">{t('customDomainComingSoon')}</p>
            </div>
          </div>
        </div>
      )}

      {/* SEO Tab */}
      {activeTab === 'seo' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <h3 className="font-semibold text-gray-900 mb-4">{t('seoSettings')}</h3>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('metaTitle')}
              </label>
              <input
                type="text"
                value={website.meta_title}
                onChange={(e) => updateWebsite({ meta_title: e.target.value })}
                placeholder={t('metaTitlePlaceholder')}
                maxLength={70}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
              <p className="text-xs text-gray-500 mt-1">
                {website.meta_title.length}/70 {t('characters')}
              </p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('metaDescription')}
              </label>
              <textarea
                value={website.meta_description}
                onChange={(e) => updateWebsite({ meta_description: e.target.value })}
                placeholder={t('metaDescriptionPlaceholder')}
                maxLength={160}
                rows={3}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              />
              <p className="text-xs text-gray-500 mt-1">
                {website.meta_description.length}/160 {t('characters')}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Saving indicator */}
      {isSaving && (
        <div className="fixed bottom-4 right-4 bg-gray-800 text-white px-4 py-2 rounded-lg flex items-center gap-2">
          <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
          {t('saving')}
        </div>
      )}
    </div>
  );
}

function SectionToggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: (value: boolean) => void }) {
  return (
    <div className="flex items-center justify-between py-2 border-b border-gray-100 last:border-0">
      <span className="text-gray-700">{label}</span>
      <label className="relative inline-flex items-center cursor-pointer">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          className="sr-only peer"
        />
        <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600" />
      </label>
    </div>
  );
}
