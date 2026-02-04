'use client';

import { useState, useEffect, ReactNode } from 'react';
import { useTranslations } from 'next-intl';

interface SocialAccount {
  id: string;
  platform: string;
  platform_display: string;
  account_name: string;
  profile_picture_url: string;
  is_active: boolean;
  is_token_expired: boolean;
  connected_at: string;
  last_sync_at: string | null;
}

interface SocialPost {
  id: string;
  caption: string;
  hashtags: string;
  post_type: string;
  post_type_display: string;
  status: string;
  status_display: string;
  scheduled_at: string | null;
  published_at: string | null;
  menu_item_name: string | null;
  is_ai_generated: boolean;
  media_count: number;
  platforms: string[];
  created_at: string;
}

interface PostTemplate {
  id: string;
  name: string;
  description: string;
  post_type: string;
  caption_template: string;
  hashtags: string;
  background_color: string;
  text_color: string;
  accent_color: string;
  is_default: boolean;
}

interface DashboardStats {
  total_posts: number;
  scheduled_posts: number;
  published_this_month: number;
  total_engagement: number;
  accounts: SocialAccount[];
  recent_posts: SocialPost[];
}

type TabType = 'overview' | 'posts' | 'calendar' | 'templates' | 'accounts' | 'analytics';

const PLATFORM_ICONS: Record<string, ReactNode> = {
  instagram: (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
      <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zm0-2.163c-3.259 0-3.667.014-4.947.072-4.358.2-6.78 2.618-6.98 6.98-.059 1.281-.073 1.689-.073 4.948 0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98 1.281.058 1.689.072 4.948.072 3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98-1.281-.059-1.69-.073-4.949-.073zm0 5.838c-3.403 0-6.162 2.759-6.162 6.162s2.759 6.163 6.162 6.163 6.162-2.759 6.162-6.163c0-3.403-2.759-6.162-6.162-6.162zm0 10.162c-2.209 0-4-1.79-4-4 0-2.209 1.791-4 4-4s4 1.791 4 4c0 2.21-1.791 4-4 4zm6.406-11.845c-.796 0-1.441.645-1.441 1.44s.645 1.44 1.441 1.44c.795 0 1.439-.645 1.439-1.44s-.644-1.44-1.439-1.44z"/>
    </svg>
  ),
  facebook: (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
      <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z"/>
    </svg>
  ),
  tiktok: (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
      <path d="M12.525.02c1.31-.02 2.61-.01 3.91-.02.08 1.53.63 3.09 1.75 4.17 1.12 1.11 2.7 1.62 4.24 1.79v4.03c-1.44-.05-2.89-.35-4.2-.97-.57-.26-1.1-.59-1.62-.93-.01 2.92.01 5.84-.02 8.75-.08 1.4-.54 2.79-1.35 3.94-1.31 1.92-3.58 3.17-5.91 3.21-1.43.08-2.86-.31-4.08-1.03-2.02-1.19-3.44-3.37-3.65-5.71-.02-.5-.03-1-.01-1.49.18-1.9 1.12-3.72 2.58-4.96 1.66-1.44 3.98-2.13 6.15-1.72.02 1.48-.04 2.96-.04 4.44-.99-.32-2.15-.23-3.02.37-.63.41-1.11 1.04-1.36 1.75-.21.51-.15 1.07-.14 1.61.24 1.64 1.82 3.02 3.5 2.87 1.12-.01 2.19-.66 2.77-1.61.19-.33.4-.67.41-1.06.1-1.79.06-3.57.07-5.36.01-4.03-.01-8.05.02-12.07z"/>
    </svg>
  ),
  twitter: (
    <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
      <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
    </svg>
  ),
};

const PLATFORM_COLORS: Record<string, string> = {
  instagram: 'bg-gradient-to-br from-purple-500 to-pink-500',
  facebook: 'bg-blue-600',
  tiktok: 'bg-black',
  twitter: 'bg-black',
};

export default function SocialPage() {
  const t = useTranslations('lite.social');
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [loading, setLoading] = useState(true);
  const [dashboard, setDashboard] = useState<DashboardStats | null>(null);
  const [posts, setPosts] = useState<SocialPost[]>([]);
  const [templates, setTemplates] = useState<PostTemplate[]>([]);
  const [accounts, setAccounts] = useState<SocialAccount[]>([]);
  const [postFilter, setPostFilter] = useState<string>('all');
  const [showConnectModal, setShowConnectModal] = useState(false);
  const [showPostModal, setShowPostModal] = useState(false);

  useEffect(() => {
    // Simulate API calls
    const loadData = async () => {
      setLoading(true);
      // In production, this would fetch from API
      setTimeout(() => {
        setDashboard({
          total_posts: 24,
          scheduled_posts: 5,
          published_this_month: 12,
          total_engagement: 1250,
          accounts: [
            {
              id: '1',
              platform: 'instagram',
              platform_display: 'Instagram',
              account_name: '@myrestaurant',
              profile_picture_url: '',
              is_active: true,
              is_token_expired: false,
              connected_at: '2024-01-15T10:00:00Z',
              last_sync_at: '2024-02-01T14:30:00Z',
            },
            {
              id: '2',
              platform: 'facebook',
              platform_display: 'Facebook',
              account_name: 'My Restaurant Page',
              profile_picture_url: '',
              is_active: true,
              is_token_expired: false,
              connected_at: '2024-01-20T11:00:00Z',
              last_sync_at: '2024-02-01T14:30:00Z',
            },
          ],
          recent_posts: [
            {
              id: '1',
              caption: 'Try our new special dish of the day!',
              hashtags: '#restaurant #food #delicious',
              post_type: 'image',
              post_type_display: 'Image Post',
              status: 'published',
              status_display: 'Published',
              scheduled_at: null,
              published_at: '2024-02-01T12:00:00Z',
              menu_item_name: 'Poulet Braise',
              is_ai_generated: true,
              media_count: 1,
              platforms: ['instagram', 'facebook'],
              created_at: '2024-02-01T10:00:00Z',
            },
          ],
        });
        setAccounts([
          {
            id: '1',
            platform: 'instagram',
            platform_display: 'Instagram',
            account_name: '@myrestaurant',
            profile_picture_url: '',
            is_active: true,
            is_token_expired: false,
            connected_at: '2024-01-15T10:00:00Z',
            last_sync_at: '2024-02-01T14:30:00Z',
          },
          {
            id: '2',
            platform: 'facebook',
            platform_display: 'Facebook',
            account_name: 'My Restaurant Page',
            profile_picture_url: '',
            is_active: true,
            is_token_expired: false,
            connected_at: '2024-01-20T11:00:00Z',
            last_sync_at: '2024-02-01T14:30:00Z',
          },
        ]);
        setPosts([
          {
            id: '1',
            caption: 'Try our new special dish of the day!',
            hashtags: '#restaurant #food #delicious',
            post_type: 'image',
            post_type_display: 'Image Post',
            status: 'published',
            status_display: 'Published',
            scheduled_at: null,
            published_at: '2024-02-01T12:00:00Z',
            menu_item_name: 'Poulet Braise',
            is_ai_generated: true,
            media_count: 1,
            platforms: ['instagram', 'facebook'],
            created_at: '2024-02-01T10:00:00Z',
          },
          {
            id: '2',
            caption: 'Weekend special coming up!',
            hashtags: '#weekend #special',
            post_type: 'image',
            post_type_display: 'Image Post',
            status: 'scheduled',
            status_display: 'Scheduled',
            scheduled_at: '2024-02-03T18:00:00Z',
            published_at: null,
            menu_item_name: null,
            is_ai_generated: false,
            media_count: 2,
            platforms: ['instagram'],
            created_at: '2024-02-01T14:00:00Z',
          },
          {
            id: '3',
            caption: 'Draft post for Valentine\'s Day',
            hashtags: '#valentines #love #food',
            post_type: 'carousel',
            post_type_display: 'Carousel',
            status: 'draft',
            status_display: 'Draft',
            scheduled_at: null,
            published_at: null,
            menu_item_name: null,
            is_ai_generated: false,
            media_count: 0,
            platforms: [],
            created_at: '2024-02-01T16:00:00Z',
          },
        ]);
        setTemplates([
          {
            id: '1',
            name: 'Menu Item Promo',
            description: 'Template for promoting menu items',
            post_type: 'image',
            caption_template: 'Introducing {item_name}! Only {price} XOF. {description}',
            hashtags: '#restaurant #food #delicious',
            background_color: '#10B981',
            text_color: '#FFFFFF',
            accent_color: '#059669',
            is_default: true,
          },
          {
            id: '2',
            name: 'Special Offer',
            description: 'Template for special offers and discounts',
            post_type: 'image',
            caption_template: 'LIMITED TIME: {item_name} at a special price!',
            hashtags: '#offer #discount #restaurant',
            background_color: '#EF4444',
            text_color: '#FFFFFF',
            accent_color: '#DC2626',
            is_default: false,
          },
        ]);
        setLoading(false);
      }, 500);
    };

    loadData();
  }, []);

  const filteredPosts = posts.filter(post => {
    if (postFilter === 'all') return true;
    return post.status === postFilter;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft': return 'bg-gray-100 text-gray-700';
      case 'scheduled': return 'bg-blue-100 text-blue-700';
      case 'publishing': return 'bg-yellow-100 text-yellow-700';
      case 'published': return 'bg-green-100 text-green-700';
      case 'failed': return 'bg-red-100 text-red-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const tabs: { id: TabType; label: string }[] = [
    { id: 'overview', label: t('tabs.overview') },
    { id: 'posts', label: t('tabs.posts') },
    { id: 'calendar', label: t('tabs.calendar') },
    { id: 'templates', label: t('tabs.templates') },
    { id: 'accounts', label: t('tabs.accounts') },
    { id: 'analytics', label: t('tabs.analytics') },
  ];

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600" />
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{t('title')}</h1>
        <p className="text-gray-600 mt-1">{t('subtitle')}</p>
      </div>

      {/* Tabs */}
      <div className="mb-6 border-b border-gray-200">
        <nav className="-mb-px flex gap-6 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`py-3 border-b-2 font-medium text-sm whitespace-nowrap transition-colors ${
                activeTab === tab.id
                  ? 'border-emerald-500 text-emerald-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === 'overview' && dashboard && (
        <div className="space-y-6">
          {/* Stats Grid */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <div className="text-sm text-gray-500 mb-1">{t('dashboard.totalPosts')}</div>
              <div className="text-2xl font-bold text-gray-900">{dashboard.total_posts}</div>
            </div>
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <div className="text-sm text-gray-500 mb-1">{t('dashboard.scheduledPosts')}</div>
              <div className="text-2xl font-bold text-blue-600">{dashboard.scheduled_posts}</div>
            </div>
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <div className="text-sm text-gray-500 mb-1">{t('dashboard.publishedThisMonth')}</div>
              <div className="text-2xl font-bold text-emerald-600">{dashboard.published_this_month}</div>
            </div>
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <div className="text-sm text-gray-500 mb-1">{t('dashboard.totalEngagement')}</div>
              <div className="text-2xl font-bold text-purple-600">{dashboard.total_engagement.toLocaleString()}</div>
            </div>
          </div>

          {/* Connected Accounts */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">{t('accounts.title')}</h2>
              <button
                onClick={() => setShowConnectModal(true)}
                className="text-sm text-emerald-600 hover:text-emerald-700 font-medium"
              >
                + {t('accounts.connect')}
              </button>
            </div>
            <div className="flex flex-wrap gap-3">
              {dashboard.accounts.map((account) => (
                <div
                  key={account.id}
                  className="flex items-center gap-3 px-4 py-2 bg-gray-50 rounded-lg"
                >
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-white ${PLATFORM_COLORS[account.platform]}`}>
                    {PLATFORM_ICONS[account.platform]}
                  </div>
                  <div>
                    <div className="text-sm font-medium text-gray-900">{account.account_name}</div>
                    <div className="text-xs text-gray-500">{account.platform_display}</div>
                  </div>
                  {account.is_token_expired && (
                    <span className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded-full">
                      {t('accounts.tokenExpired')}
                    </span>
                  )}
                </div>
              ))}
              {dashboard.accounts.length === 0 && (
                <p className="text-gray-500 text-sm">{t('accounts.noAccounts')}</p>
              )}
            </div>
          </div>

          {/* Recent Posts */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">{t('posts.title')}</h2>
              <button
                onClick={() => setShowPostModal(true)}
                className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors text-sm font-medium"
              >
                + {t('posts.newPost')}
              </button>
            </div>
            <div className="space-y-3">
              {dashboard.recent_posts.map((post) => (
                <div
                  key={post.id}
                  className="flex items-center gap-4 p-3 bg-gray-50 rounded-lg"
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-gray-900 truncate">{post.caption}</p>
                    <div className="flex items-center gap-2 mt-1">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${getStatusColor(post.status)}`}>
                        {t(`status.${post.status}`)}
                      </span>
                      {post.is_ai_generated && (
                        <span className="text-xs text-purple-600 flex items-center gap-1">
                          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                          </svg>
                          AI
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-1">
                    {post.platforms.map((platform) => (
                      <div
                        key={platform}
                        className={`w-6 h-6 rounded-full flex items-center justify-center text-white text-xs ${PLATFORM_COLORS[platform]}`}
                      >
                        {PLATFORM_ICONS[platform]}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Posts Tab */}
      {activeTab === 'posts' && (
        <div className="space-y-4">
          {/* Filter and Action Bar */}
          <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
            <div className="flex gap-2">
              {['all', 'draft', 'scheduled', 'published', 'failed'].map((filter) => (
                <button
                  key={filter}
                  onClick={() => setPostFilter(filter)}
                  className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                    postFilter === filter
                      ? 'bg-emerald-100 text-emerald-700'
                      : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                  }`}
                >
                  {t(`posts.${filter}`)}
                </button>
              ))}
            </div>
            <button
              onClick={() => setShowPostModal(true)}
              className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors text-sm font-medium"
            >
              + {t('posts.newPost')}
            </button>
          </div>

          {/* Posts List */}
          {filteredPosts.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-1">{t('posts.noPosts')}</h3>
              <p className="text-gray-500 mb-4">{t('posts.noPostsDesc')}</p>
              <button
                onClick={() => setShowPostModal(true)}
                className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
              >
                {t('posts.createPost')}
              </button>
            </div>
          ) : (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
              <div className="divide-y divide-gray-100">
                {filteredPosts.map((post) => (
                  <div key={post.id} className="p-4 hover:bg-gray-50 transition-colors">
                    <div className="flex items-start gap-4">
                      <div className="w-16 h-16 bg-gray-200 rounded-lg flex items-center justify-center text-gray-400 flex-shrink-0">
                        {post.media_count > 0 ? (
                          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                          </svg>
                        ) : (
                          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" />
                          </svg>
                        )}
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900">{post.caption}</p>
                        <p className="text-xs text-gray-500 mt-1">{post.hashtags}</p>
                        <div className="flex items-center gap-2 mt-2">
                          <span className={`text-xs px-2 py-0.5 rounded-full ${getStatusColor(post.status)}`}>
                            {t(`status.${post.status}`)}
                          </span>
                          <span className="text-xs text-gray-500">{post.post_type_display}</span>
                          {post.menu_item_name && (
                            <span className="text-xs text-gray-500">
                              • {post.menu_item_name}
                            </span>
                          )}
                          {post.is_ai_generated && (
                            <span className="text-xs text-purple-600">• AI Generated</span>
                          )}
                        </div>
                      </div>
                      <div className="flex flex-col items-end gap-2">
                        <div className="flex items-center gap-1">
                          {post.platforms.map((platform) => (
                            <div
                              key={platform}
                              className={`w-6 h-6 rounded-full flex items-center justify-center text-white text-xs ${PLATFORM_COLORS[platform]}`}
                            >
                              {PLATFORM_ICONS[platform]}
                            </div>
                          ))}
                        </div>
                        {post.scheduled_at && (
                          <span className="text-xs text-gray-500">
                            {new Date(post.scheduled_at).toLocaleDateString()}
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Templates Tab */}
      {activeTab === 'templates' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors text-sm font-medium">
              + {t('templates.newTemplate')}
            </button>
          </div>

          {templates.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-1">{t('templates.noTemplates')}</h3>
              <p className="text-gray-500">{t('templates.noTemplatesDesc')}</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {templates.map((template) => (
                <div key={template.id} className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
                  <div
                    className="h-24 p-4"
                    style={{ backgroundColor: template.background_color }}
                  >
                    <div className="flex items-center gap-2 mb-2">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{ backgroundColor: template.accent_color }}
                      />
                      <span className="text-xs" style={{ color: template.text_color }}>
                        {template.post_type.toUpperCase()}
                      </span>
                    </div>
                    <p className="text-sm font-medium truncate" style={{ color: template.text_color }}>
                      {template.caption_template.substring(0, 50)}...
                    </p>
                  </div>
                  <div className="p-4">
                    <div className="flex items-center justify-between mb-2">
                      <h3 className="font-medium text-gray-900">{template.name}</h3>
                      {template.is_default && (
                        <span className="text-xs px-2 py-0.5 bg-emerald-100 text-emerald-700 rounded-full">
                          Default
                        </span>
                      )}
                    </div>
                    <p className="text-sm text-gray-500">{template.description}</p>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Accounts Tab */}
      {activeTab === 'accounts' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button
              onClick={() => setShowConnectModal(true)}
              className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors text-sm font-medium"
            >
              + {t('accounts.connectNew')}
            </button>
          </div>

          {accounts.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-1">{t('accounts.noAccounts')}</h3>
              <p className="text-gray-500">{t('accounts.noAccountsDesc')}</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {accounts.map((account) => (
                <div key={account.id} className="bg-white rounded-xl shadow-sm border border-gray-100 p-4">
                  <div className="flex items-center gap-4">
                    <div className={`w-12 h-12 rounded-full flex items-center justify-center text-white ${PLATFORM_COLORS[account.platform]}`}>
                      {PLATFORM_ICONS[account.platform]}
                    </div>
                    <div className="flex-1">
                      <h3 className="font-medium text-gray-900">{account.account_name}</h3>
                      <p className="text-sm text-gray-500">{account.platform_display}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      {account.is_token_expired ? (
                        <button className="px-3 py-1.5 text-sm font-medium text-amber-700 bg-amber-100 rounded-lg hover:bg-amber-200 transition-colors">
                          {t('accounts.refreshToken')}
                        </button>
                      ) : (
                        <span className="px-3 py-1.5 text-sm font-medium text-emerald-700 bg-emerald-100 rounded-lg">
                          {t('accounts.connected')}
                        </span>
                      )}
                    </div>
                  </div>
                  <div className="mt-4 pt-4 border-t border-gray-100 flex items-center justify-between">
                    <span className="text-xs text-gray-500">
                      {t('accounts.lastSync')}: {account.last_sync_at ? new Date(account.last_sync_at).toLocaleString() : '-'}
                    </span>
                    <button className="text-sm text-red-600 hover:text-red-700 font-medium">
                      {t('accounts.disconnect')}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Calendar Tab */}
      {activeTab === 'calendar' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-lg font-semibold text-gray-900">{t('calendar.title')}</h2>
            <button className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors text-sm font-medium">
              + {t('calendar.addEntry')}
            </button>
          </div>

          {/* Simple Calendar Grid */}
          <div className="text-center py-12 text-gray-500">
            <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <p>{t('calendar.noEntries')}</p>
          </div>
        </div>
      )}

      {/* Analytics Tab */}
      {activeTab === 'analytics' && (
        <div className="space-y-6">
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <div className="text-sm text-gray-500 mb-1">{t('analytics.followers')}</div>
              <div className="text-2xl font-bold text-gray-900">2,450</div>
              <div className="text-xs text-emerald-600">+125 this month</div>
            </div>
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <div className="text-sm text-gray-500 mb-1">{t('analytics.engagement')}</div>
              <div className="text-2xl font-bold text-gray-900">4.8%</div>
              <div className="text-xs text-emerald-600">+0.5% vs last month</div>
            </div>
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <div className="text-sm text-gray-500 mb-1">{t('analytics.reach')}</div>
              <div className="text-2xl font-bold text-gray-900">12.3K</div>
              <div className="text-xs text-emerald-600">+2.1K this month</div>
            </div>
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <div className="text-sm text-gray-500 mb-1">{t('analytics.impressions')}</div>
              <div className="text-2xl font-bold text-gray-900">45.2K</div>
              <div className="text-xs text-emerald-600">+8K this month</div>
            </div>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('analytics.title')}</h3>
            <div className="h-64 flex items-center justify-center text-gray-400">
              <div className="text-center">
                <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <p>Analytics chart coming soon</p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Connect Account Modal */}
      {showConnectModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-md w-full p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">{t('accounts.selectPlatform')}</h2>
              <button
                onClick={() => setShowConnectModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="grid grid-cols-2 gap-3">
              {['instagram', 'facebook', 'tiktok', 'twitter'].map((platform) => (
                <button
                  key={platform}
                  className="flex items-center gap-3 p-4 border border-gray-200 rounded-lg hover:border-emerald-500 hover:bg-emerald-50 transition-colors"
                >
                  <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white ${PLATFORM_COLORS[platform]}`}>
                    {PLATFORM_ICONS[platform]}
                  </div>
                  <span className="font-medium text-gray-900 capitalize">{platform}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Create Post Modal */}
      {showPostModal && (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b border-gray-100 p-4 flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">{t('postForm.title')}</h2>
              <button
                onClick={() => setShowPostModal(false)}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="p-6 space-y-4">
              {/* Caption */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('postForm.caption')}</label>
                <textarea
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  placeholder={t('postForm.captionPlaceholder')}
                />
                <div className="flex justify-end mt-1">
                  <button className="text-sm text-purple-600 hover:text-purple-700 flex items-center gap-1">
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                    {t('postForm.generateCaption')}
                  </button>
                </div>
              </div>

              {/* Hashtags */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('postForm.hashtags')}</label>
                <input
                  type="text"
                  className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  placeholder={t('postForm.hashtagsPlaceholder')}
                />
              </div>

              {/* Post Type */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('postForm.postType')}</label>
                <div className="flex flex-wrap gap-2">
                  {['image', 'carousel', 'video', 'story', 'reel'].map((type) => (
                    <button
                      key={type}
                      className="px-3 py-1.5 border border-gray-200 rounded-lg text-sm hover:border-emerald-500 hover:bg-emerald-50 transition-colors"
                    >
                      {t(`postForm.${type}`)}
                    </button>
                  ))}
                </div>
              </div>

              {/* Select Accounts */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('postForm.selectAccounts')}</label>
                <div className="flex flex-wrap gap-2">
                  {accounts.map((account) => (
                    <label key={account.id} className="flex items-center gap-2 px-3 py-2 border border-gray-200 rounded-lg cursor-pointer hover:border-emerald-500 transition-colors">
                      <input type="checkbox" className="rounded text-emerald-600" />
                      <div className={`w-5 h-5 rounded-full flex items-center justify-center text-white text-xs ${PLATFORM_COLORS[account.platform]}`}>
                        {PLATFORM_ICONS[account.platform]}
                      </div>
                      <span className="text-sm">{account.account_name}</span>
                    </label>
                  ))}
                </div>
              </div>

              {/* Media Upload */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('postForm.media')}</label>
                <div className="border-2 border-dashed border-gray-200 rounded-lg p-8 text-center">
                  <svg className="w-10 h-10 mx-auto text-gray-400 mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                  <button className="text-emerald-600 hover:text-emerald-700 font-medium">
                    {t('postForm.uploadMedia')}
                  </button>
                </div>
              </div>
            </div>
            <div className="sticky bottom-0 bg-gray-50 border-t border-gray-100 p-4 flex gap-3 justify-end">
              <button
                onClick={() => setShowPostModal(false)}
                className="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
              >
                {t('postForm.saveDraft')}
              </button>
              <button className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors">
                {t('postForm.schedule')}
              </button>
              <button className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors">
                {t('postForm.publishNow')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
