'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';

interface Brand {
  id: string;
  name: string;
  slug: string;
  description: string;
  logo: string | null;
  primary_color: string;
  secondary_color: string;
  location_count: number;
}

interface Location {
  id: string;
  name: string;
  slug: string;
  address: string;
  phone: string;
  location_code: string;
  location_group: string | null;
  is_flagship: boolean;
  is_active: boolean;
}

interface LocationGroup {
  id: string;
  name: string;
  description: string;
  location_count: number;
}

interface SharedMenu {
  id: string;
  name: string;
  description: string;
  is_default: boolean;
  category_count: number;
  synced_locations: number;
}

interface Announcement {
  id: string;
  title: string;
  content: string;
  priority: string;
  publish_at: string;
  expires_at: string | null;
  is_published: boolean;
}

type TabType = 'overview' | 'locations' | 'sharedMenu' | 'groups' | 'announcements' | 'reports';

export default function LocationsPage() {
  const t = useTranslations('lite.locations');
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [loading, setLoading] = useState(true);
  const [hasBrand, setHasBrand] = useState(true);
  const [brand, setBrand] = useState<Brand | null>(null);
  const [locations, setLocations] = useState<Location[]>([]);
  const [groups, setGroups] = useState<LocationGroup[]>([]);
  const [sharedMenus, setSharedMenus] = useState<SharedMenu[]>([]);
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);

  useEffect(() => {
    // Simulate API call
    const loadData = async () => {
      setLoading(true);
      setTimeout(() => {
        // Demo: Restaurant is part of a brand
        setHasBrand(true);
        setBrand({
          id: '1',
          name: 'Maquis Express',
          slug: 'maquis-express',
          description: 'The best West African fast food chain',
          logo: null,
          primary_color: '#10B981',
          secondary_color: '#059669',
          location_count: 5,
        });
        setLocations([
          {
            id: '1',
            name: 'Maquis Express - Plateau',
            slug: 'maquis-express-plateau',
            address: 'Rue du Commerce, Plateau, Abidjan',
            phone: '+225 07 00 00 01',
            location_code: 'ABJ-PLT',
            location_group: 'Abidjan',
            is_flagship: true,
            is_active: true,
          },
          {
            id: '2',
            name: 'Maquis Express - Cocody',
            slug: 'maquis-express-cocody',
            address: 'Boulevard de France, Cocody, Abidjan',
            phone: '+225 07 00 00 02',
            location_code: 'ABJ-COC',
            location_group: 'Abidjan',
            is_flagship: false,
            is_active: true,
          },
          {
            id: '3',
            name: 'Maquis Express - Marcory',
            slug: 'maquis-express-marcory',
            address: 'Boulevard du Gabon, Marcory, Abidjan',
            phone: '+225 07 00 00 04',
            location_code: 'ABJ-MRC',
            location_group: 'Abidjan',
            is_flagship: false,
            is_active: true,
          },
          {
            id: '4',
            name: 'Maquis Express - Yopougon',
            slug: 'maquis-express-yopougon',
            address: 'Carrefour Wassakara, Yopougon, Abidjan',
            phone: '+225 07 00 00 03',
            location_code: 'ABJ-YOP',
            location_group: 'Abidjan',
            is_flagship: false,
            is_active: false,
          },
        ]);
        setGroups([
          {
            id: '1',
            name: 'Abidjan',
            description: 'Toutes les locations à Abidjan, Côte d\'Ivoire',
            location_count: 4,
          },
          {
            id: '2',
            name: 'Bouaké',
            description: 'Locations à Bouaké, Côte d\'Ivoire',
            location_count: 0,
          },
        ]);
        setSharedMenus([
          {
            id: '1',
            name: 'Standard Menu',
            description: 'Main menu shared across all locations',
            is_default: true,
            category_count: 6,
            synced_locations: 4,
          },
          {
            id: '2',
            name: 'Breakfast Menu',
            description: 'Morning menu for selected locations',
            is_default: false,
            category_count: 3,
            synced_locations: 2,
          },
        ]);
        setAnnouncements([
          {
            id: '1',
            title: 'New Pricing Update',
            content: 'Prices will be updated across all locations starting next Monday.',
            priority: 'high',
            publish_at: '2024-02-01T10:00:00Z',
            expires_at: '2024-02-15T23:59:59Z',
            is_published: true,
          },
          {
            id: '2',
            title: 'Holiday Hours',
            content: 'All locations will have modified hours during the upcoming holidays.',
            priority: 'normal',
            publish_at: '2024-02-10T08:00:00Z',
            expires_at: null,
            is_published: false,
          },
        ]);
        setLoading(false);
      }, 500);
    };

    loadData();
  }, []);

  const tabs: { id: TabType; label: string }[] = [
    { id: 'overview', label: t('tabs.overview') },
    { id: 'locations', label: t('tabs.locations') },
    { id: 'sharedMenu', label: t('tabs.sharedMenu') },
    { id: 'groups', label: t('tabs.groups') },
    { id: 'announcements', label: t('tabs.announcements') },
    { id: 'reports', label: t('tabs.reports') },
  ];

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'low': return 'bg-gray-100 text-gray-700';
      case 'normal': return 'bg-blue-100 text-blue-700';
      case 'high': return 'bg-orange-100 text-orange-700';
      case 'urgent': return 'bg-red-100 text-red-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  if (loading) {
    return (
      <div className="p-6 flex items-center justify-center min-h-[400px]">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600" />
      </div>
    );
  }

  // Show message if restaurant is not part of a brand
  if (!hasBrand || !brand) {
    return (
      <div className="p-6 max-w-2xl mx-auto">
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
          <div className="w-20 h-20 mx-auto mb-6 bg-gray-100 rounded-full flex items-center justify-center">
            <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">{t('noBrand.title')}</h2>
          <p className="text-gray-500 mb-6">{t('noBrand.description')}</p>
          <button className="px-6 py-3 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors font-medium">
            {t('noBrand.contact')}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header with Brand Info */}
      <div className="mb-6 flex items-start gap-4">
        {brand.logo ? (
          <img src={brand.logo} alt={brand.name} className="w-16 h-16 rounded-xl object-cover" />
        ) : (
          <div
            className="w-16 h-16 rounded-xl flex items-center justify-center text-white text-2xl font-bold"
            style={{ backgroundColor: brand.primary_color }}
          >
            {brand.name.charAt(0)}
          </div>
        )}
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{brand.name}</h1>
          <p className="text-gray-600">{t('subtitle')}</p>
        </div>
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
      {activeTab === 'overview' && (
        <div className="space-y-6">
          {/* Stats Grid */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <div className="text-sm text-gray-500 mb-1">{t('dashboard.totalLocations')}</div>
              <div className="text-2xl font-bold text-gray-900">{locations.length}</div>
            </div>
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <div className="text-sm text-gray-500 mb-1">{t('dashboard.activeLocations')}</div>
              <div className="text-2xl font-bold text-emerald-600">
                {locations.filter(l => l.is_active).length}
              </div>
            </div>
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <div className="text-sm text-gray-500 mb-1">{t('dashboard.ordersToday')}</div>
              <div className="text-2xl font-bold text-gray-900">127</div>
            </div>
            <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <div className="text-sm text-gray-500 mb-1">{t('dashboard.revenueToday')}</div>
              <div className="text-2xl font-bold text-purple-600">485,000 XOF</div>
            </div>
          </div>

          {/* Recent Activity Cards */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top Locations */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('reports.topLocations')}</h3>
              <div className="space-y-3">
                {locations.filter(l => l.is_active).slice(0, 3).map((location, index) => (
                  <div key={location.id} className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-600 flex items-center justify-center font-bold text-sm">
                      {index + 1}
                    </div>
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">{location.name}</div>
                      <div className="text-xs text-gray-500">{location.location_code}</div>
                    </div>
                    <div className="text-right">
                      <div className="font-medium text-gray-900">{(150000 - index * 25000).toLocaleString()} XOF</div>
                      <div className="text-xs text-emerald-600">+{12 - index}%</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Announcements */}
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">{t('announcements.title')}</h3>
              <div className="space-y-3">
                {announcements.slice(0, 3).map((announcement) => (
                  <div key={announcement.id} className="p-3 bg-gray-50 rounded-lg">
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-medium text-gray-900">{announcement.title}</span>
                      <span className={`text-xs px-2 py-0.5 rounded-full ${getPriorityColor(announcement.priority)}`}>
                        {t(`announcements.priorities.${announcement.priority}`)}
                      </span>
                    </div>
                    <p className="text-sm text-gray-500 line-clamp-1">{announcement.content}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Locations Tab */}
      {activeTab === 'locations' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors text-sm font-medium">
              + {t('locationsList.addLocation')}
            </button>
          </div>

          <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
            <div className="divide-y divide-gray-100">
              {locations.map((location) => (
                <div key={location.id} className="p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-center gap-4">
                    <div
                      className="w-12 h-12 rounded-lg flex items-center justify-center text-white font-bold"
                      style={{ backgroundColor: brand.primary_color }}
                    >
                      {location.location_code.substring(0, 2)}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <span className="font-medium text-gray-900">{location.name}</span>
                        {location.is_flagship && (
                          <span className="text-xs px-2 py-0.5 bg-amber-100 text-amber-700 rounded-full">
                            {t('locationsList.flagship')}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-500 truncate">{location.address}</p>
                      <div className="flex items-center gap-3 mt-1 text-xs text-gray-500">
                        <span>{t('locationsList.locationCode')}: {location.location_code}</span>
                        {location.location_group && (
                          <span>• {t('locationsList.group')}: {location.location_group}</span>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <span className={`text-sm px-3 py-1 rounded-full ${
                        location.is_active
                          ? 'bg-emerald-100 text-emerald-700'
                          : 'bg-gray-100 text-gray-500'
                      }`}>
                        {location.is_active ? t('locationsList.active') : t('locationsList.inactive')}
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Shared Menu Tab */}
      {activeTab === 'sharedMenu' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors text-sm font-medium">
              + {t('sharedMenu.addMenu')}
            </button>
          </div>

          {sharedMenus.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-1">{t('sharedMenu.noMenus')}</h3>
              <p className="text-gray-500">{t('sharedMenu.noMenusDesc')}</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {sharedMenus.map((menu) => (
                <div key={menu.id} className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                  <div className="flex items-center justify-between mb-3">
                    <h3 className="font-semibold text-gray-900">{menu.name}</h3>
                    {menu.is_default && (
                      <span className="text-xs px-2 py-0.5 bg-emerald-100 text-emerald-700 rounded-full">
                        {t('sharedMenu.default')}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500 mb-4">{menu.description}</p>
                  <div className="flex items-center justify-between text-sm">
                    <div className="flex items-center gap-4 text-gray-500">
                      <span>{menu.category_count} {t('sharedMenu.categories')}</span>
                      <span>{t('sharedMenu.syncedLocations', { count: menu.synced_locations })}</span>
                    </div>
                    <button className="text-emerald-600 hover:text-emerald-700 font-medium">
                      {t('sharedMenu.syncToLocation')}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Groups Tab */}
      {activeTab === 'groups' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors text-sm font-medium">
              + {t('groups.addGroup')}
            </button>
          </div>

          {groups.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-1">{t('groups.noGroups')}</h3>
              <p className="text-gray-500">{t('groups.noGroupsDesc')}</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {groups.map((group) => (
                <div key={group.id} className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                  <h3 className="font-semibold text-gray-900 mb-2">{group.name}</h3>
                  <p className="text-sm text-gray-500 mb-4">{group.description}</p>
                  <div className="text-sm text-emerald-600 font-medium">
                    {t('groups.locationCount', { count: group.location_count })}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Announcements Tab */}
      {activeTab === 'announcements' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors text-sm font-medium">
              + {t('announcements.addAnnouncement')}
            </button>
          </div>

          {announcements.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
              <div className="w-16 h-16 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5.882V19.24a1.76 1.76 0 01-3.417.592l-2.147-6.15M18 13a3 3 0 100-6M5.436 13.683A4.001 4.001 0 017 6h1.832c4.1 0 7.625-1.234 9.168-3v14c-1.543-1.766-5.067-3-9.168-3H7a3.988 3.988 0 01-1.564-.317z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-1">{t('announcements.noAnnouncements')}</h3>
            </div>
          ) : (
            <div className="space-y-4">
              {announcements.map((announcement) => (
                <div key={announcement.id} className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                  <div className="flex items-start justify-between mb-3">
                    <div>
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold text-gray-900">{announcement.title}</h3>
                        <span className={`text-xs px-2 py-0.5 rounded-full ${getPriorityColor(announcement.priority)}`}>
                          {t(`announcements.priorities.${announcement.priority}`)}
                        </span>
                      </div>
                      <div className="text-xs text-gray-500">
                        {t('announcements.publishAt')}: {new Date(announcement.publish_at).toLocaleDateString()}
                        {announcement.expires_at && (
                          <> • {t('announcements.expiresAt')}: {new Date(announcement.expires_at).toLocaleDateString()}</>
                        )}
                      </div>
                    </div>
                    <span className={`text-sm px-3 py-1 rounded-full ${
                      announcement.is_published
                        ? 'bg-emerald-100 text-emerald-700'
                        : 'bg-gray-100 text-gray-500'
                    }`}>
                      {announcement.is_published ? 'Published' : 'Scheduled'}
                    </span>
                  </div>
                  <p className="text-gray-600">{announcement.content}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Reports Tab */}
      {activeTab === 'reports' && (
        <div className="space-y-6">
          {/* Period Selector */}
          <div className="flex gap-2">
            <button className="px-4 py-2 bg-emerald-100 text-emerald-700 rounded-lg font-medium text-sm">
              {t('reports.daily')}
            </button>
            <button className="px-4 py-2 bg-gray-100 text-gray-600 rounded-lg font-medium text-sm hover:bg-gray-200 transition-colors">
              {t('reports.weekly')}
            </button>
            <button className="px-4 py-2 bg-gray-100 text-gray-600 rounded-lg font-medium text-sm hover:bg-gray-200 transition-colors">
              {t('reports.monthly')}
            </button>
          </div>

          {/* Report Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <div className="text-sm text-gray-500 mb-1">{t('reports.totalOrders')}</div>
              <div className="text-3xl font-bold text-gray-900">1,247</div>
              <div className="text-sm text-emerald-600 mt-1">+15% vs last period</div>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <div className="text-sm text-gray-500 mb-1">{t('reports.totalRevenue')}</div>
              <div className="text-3xl font-bold text-gray-900">4.85M XOF</div>
              <div className="text-sm text-emerald-600 mt-1">+22% vs last period</div>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <div className="text-sm text-gray-500 mb-1">{t('reports.avgOrderValue')}</div>
              <div className="text-3xl font-bold text-gray-900">3,890 XOF</div>
              <div className="text-sm text-emerald-600 mt-1">+5% vs last period</div>
            </div>
          </div>

          {/* Chart Placeholder */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Revenue by Location</h3>
            <div className="h-64 flex items-center justify-center text-gray-400">
              <div className="text-center">
                <svg className="w-16 h-16 mx-auto mb-4 text-gray-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <p>Chart visualization coming soon</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
