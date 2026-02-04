'use client';

import { useState, useEffect, ReactNode } from 'react';
import { useTranslations } from 'next-intl';

type Period = 'last7' | 'last30' | 'last90' | 'custom';
type Tab = 'overview' | 'sales' | 'items' | 'categories' | 'peakHours' | 'customers' | 'reports';
type ExportType = 'sales' | 'items' | 'categories' | 'customers' | 'hourly' | 'full';
type ExportFormat = 'csv' | 'pdf' | 'xlsx';

interface DailyStats {
  date: string;
  total_orders: number;
  completed_orders: number;
  cancelled_orders: number;
  dine_in_orders: number;
  takeaway_orders: number;
  delivery_orders: number;
  total_revenue: number;
  average_order_value: number;
  total_items_sold: number;
}

interface ItemPerformance {
  id: string;
  name: string;
  category: string;
  quantity_sold: number;
  revenue: number;
  rank_by_quantity: number | null;
  rank_by_revenue: number | null;
}

interface CategoryPerformance {
  id: string;
  name: string;
  items_sold: number;
  revenue: number;
  order_count: number;
  revenue_percentage: number;
}

interface HourlyStats {
  hour: number;
  order_count: number;
  revenue: number;
  items_sold: number;
}

interface CustomerStats {
  date: string;
  new_customers: number;
  returning_customers: number;
  total_customers: number;
  menu_views: number;
  orders_placed: number;
  conversion_rate: number;
}

interface WeeklyReport {
  id: string;
  week_start: string;
  week_end: string;
  total_orders: number;
  total_revenue: number;
  average_daily_revenue: number;
  average_order_value: number;
  orders_change_percent: number;
  revenue_change_percent: number;
  top_items: Array<{ name: string; quantity: number }>;
  sent_at: string | null;
}

interface DashboardData {
  total_revenue: number;
  total_orders: number;
  average_order_value: number;
  total_items_sold: number;
  revenue_change_percent: number;
  orders_change_percent: number;
  revenue_by_day: Array<{ date: string; revenue: number }>;
  orders_by_type: { dine_in: number; takeaway: number; delivery: number };
  top_items: Array<{ name: string; quantity: number; revenue: number }>;
  top_categories: Array<{ name: string; revenue: number; percentage: number }>;
  peak_hours: Array<{ hour: number; orders: number }>;
  conversion_rate: number;
  new_vs_returning: { new: number; returning: number };
}

interface Benchmark {
  metric: string;
  your_value: number;
  industry_average: number;
  percentile: number;
  status: 'above' | 'average' | 'below';
}

const TAB_ICONS: Record<Tab, ReactNode> = {
  overview: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
    </svg>
  ),
  sales: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  items: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
    </svg>
  ),
  categories: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
    </svg>
  ),
  peakHours: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
    </svg>
  ),
  customers: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
    </svg>
  ),
  reports: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  ),
};

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('fr-FR', { style: 'decimal' }).format(value) + ' XOF';
}

function formatPercent(value: number): string {
  const sign = value >= 0 ? '+' : '';
  return `${sign}${value.toFixed(1)}%`;
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'short',
  });
}

function formatHour(hour: number): string {
  return `${hour.toString().padStart(2, '0')}:00`;
}

export default function AnalyticsPage() {
  const t = useTranslations('lite.analytics');
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [period, setPeriod] = useState<Period>('last30');
  const [loading, setLoading] = useState(true);

  // Dashboard data
  const [dashboard, setDashboard] = useState<DashboardData | null>(null);
  const [salesStats, setSalesStats] = useState<DailyStats[]>([]);
  const [itemPerformance, setItemPerformance] = useState<ItemPerformance[]>([]);
  const [categoryPerformance, setCategoryPerformance] = useState<CategoryPerformance[]>([]);
  const [hourlyStats, setHourlyStats] = useState<HourlyStats[]>([]);
  const [customerStats, setCustomerStats] = useState<CustomerStats[]>([]);
  const [weeklyReports, setWeeklyReports] = useState<WeeklyReport[]>([]);
  const [benchmarks, setBenchmarks] = useState<Benchmark[]>([]);

  // Export form state
  const [exportType, setExportType] = useState<ExportType>('sales');
  const [exportFormat, setExportFormat] = useState<ExportFormat>('csv');
  const [exportFrom, setExportFrom] = useState('');
  const [exportTo, setExportTo] = useState('');
  const [exporting, setExporting] = useState(false);

  const tabs: Tab[] = ['overview', 'sales', 'items', 'categories', 'peakHours', 'customers', 'reports'];

  useEffect(() => {
    loadData();
  }, [period]);

  const loadData = async () => {
    setLoading(true);
    try {
      // In a real app, these would be actual API calls
      // For now, simulate with mock data
      await new Promise(resolve => setTimeout(resolve, 500));

      // Mock dashboard data
      setDashboard({
        total_revenue: 2450000,
        total_orders: 342,
        average_order_value: 7164,
        total_items_sold: 1024,
        revenue_change_percent: 12.5,
        orders_change_percent: 8.3,
        revenue_by_day: [
          { date: '2025-01-25', revenue: 320000 },
          { date: '2025-01-26', revenue: 285000 },
          { date: '2025-01-27', revenue: 410000 },
          { date: '2025-01-28', revenue: 375000 },
          { date: '2025-01-29', revenue: 298000 },
          { date: '2025-01-30', revenue: 442000 },
          { date: '2025-01-31', revenue: 320000 },
        ],
        orders_by_type: { dine_in: 145, takeaway: 112, delivery: 85 },
        top_items: [
          { name: 'Kédjenou de Poulet', quantity: 89, revenue: 445000 },
          { name: 'Poulet Braisé', quantity: 76, revenue: 380000 },
          { name: 'Garba', quantity: 64, revenue: 96000 },
          { name: 'Sauce Graine', quantity: 52, revenue: 260000 },
          { name: 'Alloco Poisson', quantity: 48, revenue: 168000 },
        ],
        top_categories: [
          { name: 'Plats Principaux', revenue: 1405000, percentage: 57.3 },
          { name: 'Boissons', revenue: 490000, percentage: 20.0 },
          { name: 'Entrees', revenue: 367500, percentage: 15.0 },
          { name: 'Desserts', revenue: 187500, percentage: 7.7 },
        ],
        peak_hours: [
          { hour: 12, orders: 45 },
          { hour: 13, orders: 52 },
          { hour: 19, orders: 68 },
          { hour: 20, orders: 71 },
          { hour: 21, orders: 48 },
        ],
        conversion_rate: 23.5,
        new_vs_returning: { new: 142, returning: 200 },
      });

      // Mock sales stats
      setSalesStats([
        { date: '2025-01-31', total_orders: 52, completed_orders: 48, cancelled_orders: 4, dine_in_orders: 22, takeaway_orders: 18, delivery_orders: 12, total_revenue: 372800, average_order_value: 7169, total_items_sold: 156 },
        { date: '2025-01-30', total_orders: 63, completed_orders: 61, cancelled_orders: 2, dine_in_orders: 28, takeaway_orders: 20, delivery_orders: 15, total_revenue: 442000, average_order_value: 7016, total_items_sold: 189 },
        { date: '2025-01-29', total_orders: 42, completed_orders: 40, cancelled_orders: 2, dine_in_orders: 18, takeaway_orders: 14, delivery_orders: 10, total_revenue: 298000, average_order_value: 7095, total_items_sold: 126 },
      ]);

      // Mock item performance
      setItemPerformance([
        { id: '1', name: 'Kédjenou de Poulet', category: 'Plats Principaux', quantity_sold: 89, revenue: 445000, rank_by_quantity: 1, rank_by_revenue: 1 },
        { id: '2', name: 'Poulet Braisé', category: 'Plats Principaux', quantity_sold: 76, revenue: 380000, rank_by_quantity: 2, rank_by_revenue: 2 },
        { id: '3', name: 'Garba', category: 'Plats Principaux', quantity_sold: 64, revenue: 96000, rank_by_quantity: 3, rank_by_revenue: 5 },
        { id: '4', name: 'Sauce Graine', category: 'Plats Principaux', quantity_sold: 52, revenue: 260000, rank_by_quantity: 4, rank_by_revenue: 3 },
        { id: '5', name: 'Alloco Poisson', category: 'Grillades', quantity_sold: 48, revenue: 168000, rank_by_quantity: 5, rank_by_revenue: 4 },
      ]);

      // Mock category performance
      setCategoryPerformance([
        { id: '1', name: 'Plats Principaux', items_sold: 281, revenue: 1405000, order_count: 281, revenue_percentage: 57.3 },
        { id: '2', name: 'Boissons', items_sold: 420, revenue: 490000, order_count: 280, revenue_percentage: 20.0 },
        { id: '3', name: 'Entrees', items_sold: 245, revenue: 367500, order_count: 163, revenue_percentage: 15.0 },
        { id: '4', name: 'Desserts', items_sold: 78, revenue: 187500, order_count: 78, revenue_percentage: 7.7 },
      ]);

      // Mock hourly stats
      setHourlyStats(
        Array.from({ length: 24 }, (_, i) => ({
          hour: i,
          order_count: i >= 11 && i <= 14 ? Math.floor(Math.random() * 30) + 20 :
                       i >= 18 && i <= 21 ? Math.floor(Math.random() * 40) + 30 :
                       Math.floor(Math.random() * 10),
          revenue: 0,
          items_sold: 0,
        })).map(h => ({
          ...h,
          revenue: h.order_count * 7000,
          items_sold: h.order_count * 3,
        }))
      );

      // Mock customer stats
      setCustomerStats([
        { date: '2025-01-31', new_customers: 18, returning_customers: 34, total_customers: 52, menu_views: 245, orders_placed: 52, conversion_rate: 21.2 },
        { date: '2025-01-30', new_customers: 22, returning_customers: 41, total_customers: 63, menu_views: 298, orders_placed: 63, conversion_rate: 21.1 },
        { date: '2025-01-29', new_customers: 12, returning_customers: 30, total_customers: 42, menu_views: 178, orders_placed: 42, conversion_rate: 23.6 },
      ]);

      // Mock weekly reports
      setWeeklyReports([
        { id: '1', week_start: '2025-01-27', week_end: '2025-02-02', total_orders: 342, total_revenue: 2450000, average_daily_revenue: 350000, average_order_value: 7164, orders_change_percent: 8.3, revenue_change_percent: 12.5, top_items: [{ name: 'Kédjenou', quantity: 89 }], sent_at: null },
        { id: '2', week_start: '2025-01-20', week_end: '2025-01-26', total_orders: 316, total_revenue: 2178000, average_daily_revenue: 311143, average_order_value: 6892, orders_change_percent: -2.1, revenue_change_percent: 5.2, top_items: [{ name: 'Poulet Braisé', quantity: 82 }], sent_at: '2025-01-27T10:00:00Z' },
      ]);

      // Mock benchmarks
      setBenchmarks([
        { metric: 'Average Order Value', your_value: 7164, industry_average: 6500, percentile: 72, status: 'above' },
        { metric: 'Conversion Rate', your_value: 23.5, industry_average: 18.0, percentile: 85, status: 'above' },
        { metric: 'Orders per Day', your_value: 48.9, industry_average: 52.0, percentile: 45, status: 'average' },
        { metric: 'Customer Retention', your_value: 58.5, industry_average: 42.0, percentile: 78, status: 'above' },
      ]);

    } catch (error) {
      console.error('Failed to load analytics data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleExport = async () => {
    if (!exportFrom || !exportTo) return;

    setExporting(true);
    try {
      // In a real app, this would call the API
      await new Promise(resolve => setTimeout(resolve, 1500));
      alert('Export generated! (Mock)');
    } catch (error) {
      console.error('Export failed:', error);
    } finally {
      setExporting(false);
    }
  };

  const renderOverview = () => {
    if (!dashboard) return null;

    const maxRevenue = Math.max(...dashboard.revenue_by_day.map(d => d.revenue));
    const totalOrders = dashboard.orders_by_type.dine_in + dashboard.orders_by_type.takeaway + dashboard.orders_by_type.delivery;

    return (
      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <div className="text-sm text-gray-500">{t('overview.totalRevenue')}</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">{formatCurrency(dashboard.total_revenue)}</div>
            <div className={`text-sm mt-1 ${dashboard.revenue_change_percent >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
              {formatPercent(dashboard.revenue_change_percent)} {t('overview.vsLastPeriod')}
            </div>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <div className="text-sm text-gray-500">{t('overview.totalOrders')}</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">{dashboard.total_orders}</div>
            <div className={`text-sm mt-1 ${dashboard.orders_change_percent >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
              {formatPercent(dashboard.orders_change_percent)} {t('overview.vsLastPeriod')}
            </div>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <div className="text-sm text-gray-500">{t('overview.avgOrderValue')}</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">{formatCurrency(dashboard.average_order_value)}</div>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <div className="text-sm text-gray-500">{t('overview.itemsSold')}</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">{dashboard.total_items_sold}</div>
          </div>
        </div>

        {/* Revenue Chart */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-900 mb-4">{t('overview.revenueByDay')}</h3>
          <div className="flex items-end justify-between h-48 gap-2">
            {dashboard.revenue_by_day.map((day, idx) => (
              <div key={idx} className="flex-1 flex flex-col items-center gap-2">
                <div
                  className="w-full bg-emerald-500 rounded-t transition-all hover:bg-emerald-600"
                  style={{ height: `${(day.revenue / maxRevenue) * 100}%` }}
                  title={formatCurrency(day.revenue)}
                />
                <span className="text-xs text-gray-500">{formatDate(day.date)}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Orders by Type & Top Items */}
        <div className="grid lg:grid-cols-2 gap-6">
          {/* Orders by Type */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <h3 className="font-semibold text-gray-900 mb-4">{t('overview.ordersByType')}</h3>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>{t('overview.dineIn')}</span>
                  <span className="font-medium">{dashboard.orders_by_type.dine_in} ({((dashboard.orders_by_type.dine_in / totalOrders) * 100).toFixed(1)}%)</span>
                </div>
                <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-emerald-500 rounded-full"
                    style={{ width: `${(dashboard.orders_by_type.dine_in / totalOrders) * 100}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>{t('overview.takeaway')}</span>
                  <span className="font-medium">{dashboard.orders_by_type.takeaway} ({((dashboard.orders_by_type.takeaway / totalOrders) * 100).toFixed(1)}%)</span>
                </div>
                <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 rounded-full"
                    style={{ width: `${(dashboard.orders_by_type.takeaway / totalOrders) * 100}%` }}
                  />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-1">
                  <span>{t('overview.delivery')}</span>
                  <span className="font-medium">{dashboard.orders_by_type.delivery} ({((dashboard.orders_by_type.delivery / totalOrders) * 100).toFixed(1)}%)</span>
                </div>
                <div className="h-3 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-orange-500 rounded-full"
                    style={{ width: `${(dashboard.orders_by_type.delivery / totalOrders) * 100}%` }}
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Top Items */}
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <h3 className="font-semibold text-gray-900 mb-4">{t('items.topSelling')}</h3>
            <div className="space-y-3">
              {dashboard.top_items.slice(0, 5).map((item, idx) => (
                <div key={idx} className="flex items-center gap-3">
                  <div className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center text-sm font-medium">
                    {idx + 1}
                  </div>
                  <div className="flex-1">
                    <div className="font-medium text-gray-900">{item.name}</div>
                    <div className="text-sm text-gray-500">{item.quantity} vendus</div>
                  </div>
                  <div className="text-right">
                    <div className="font-medium text-gray-900">{formatCurrency(item.revenue)}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderSales = () => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="p-4 border-b border-gray-100">
        <h3 className="font-semibold text-gray-900">{t('sales.title')}</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('sales.date')}</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('sales.orders')}</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('sales.completed')}</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('sales.cancelled')}</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('sales.revenue')}</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('sales.avgValue')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {salesStats.map((stat, idx) => (
              <tr key={idx} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm text-gray-900">{formatDate(stat.date)}</td>
                <td className="px-4 py-3 text-sm text-gray-900 text-right">{stat.total_orders}</td>
                <td className="px-4 py-3 text-sm text-emerald-600 text-right">{stat.completed_orders}</td>
                <td className="px-4 py-3 text-sm text-red-600 text-right">{stat.cancelled_orders}</td>
                <td className="px-4 py-3 text-sm text-gray-900 text-right font-medium">{formatCurrency(stat.total_revenue)}</td>
                <td className="px-4 py-3 text-sm text-gray-500 text-right">{formatCurrency(stat.average_order_value)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const renderItems = () => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="p-4 border-b border-gray-100">
        <h3 className="font-semibold text-gray-900">{t('items.title')}</h3>
      </div>
      {itemPerformance.length === 0 ? (
        <div className="p-8 text-center text-gray-500">{t('items.noData')}</div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('items.rank')}</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('items.name')}</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('items.category')}</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('items.quantity')}</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('items.revenue')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {itemPerformance.map((item) => (
                <tr key={item.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="w-6 h-6 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center text-sm font-medium">
                      {item.rank_by_quantity}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">{item.name}</td>
                  <td className="px-4 py-3 text-sm text-gray-500">{item.category}</td>
                  <td className="px-4 py-3 text-sm text-gray-900 text-right">{item.quantity_sold}</td>
                  <td className="px-4 py-3 text-sm text-gray-900 text-right font-medium">{formatCurrency(item.revenue)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );

  const renderCategories = () => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="p-4 border-b border-gray-100">
        <h3 className="font-semibold text-gray-900">{t('categories.title')}</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('categories.name')}</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('categories.itemsSold')}</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('categories.orders')}</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('categories.revenue')}</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('categories.percentage')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {categoryPerformance.map((cat) => (
              <tr key={cat.id} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-medium text-gray-900">{cat.name}</td>
                <td className="px-4 py-3 text-sm text-gray-900 text-right">{cat.items_sold}</td>
                <td className="px-4 py-3 text-sm text-gray-900 text-right">{cat.order_count}</td>
                <td className="px-4 py-3 text-sm text-gray-900 text-right font-medium">{formatCurrency(cat.revenue)}</td>
                <td className="px-4 py-3 text-right">
                  <div className="flex items-center justify-end gap-2">
                    <div className="w-16 h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-emerald-500 rounded-full"
                        style={{ width: `${cat.revenue_percentage}%` }}
                      />
                    </div>
                    <span className="text-sm text-gray-500 w-12">{cat.revenue_percentage.toFixed(1)}%</span>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const renderPeakHours = () => {
    const maxOrders = Math.max(...hourlyStats.map(h => h.order_count));
    const busiestHour = hourlyStats.reduce((a, b) => a.order_count > b.order_count ? a : b);
    const quietestHour = hourlyStats.filter(h => h.order_count > 0).reduce((a, b) => a.order_count < b.order_count ? a : b, hourlyStats[0]);

    return (
      <div className="space-y-6">
        {/* Summary */}
        <div className="grid grid-cols-2 gap-4">
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <div className="text-sm text-gray-500">{t('peakHours.busiest')}</div>
            <div className="text-2xl font-bold text-emerald-600 mt-1">{formatHour(busiestHour.hour)}</div>
            <div className="text-sm text-gray-500">{busiestHour.order_count} {t('peakHours.orders').toLowerCase()}</div>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <div className="text-sm text-gray-500">{t('peakHours.quietest')}</div>
            <div className="text-2xl font-bold text-gray-600 mt-1">{formatHour(quietestHour.hour)}</div>
            <div className="text-sm text-gray-500">{quietestHour.order_count} {t('peakHours.orders').toLowerCase()}</div>
          </div>
        </div>

        {/* Hourly Chart */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-900 mb-4">{t('peakHours.title')}</h3>
          <p className="text-sm text-gray-500 mb-6">{t('peakHours.description')}</p>
          <div className="flex items-end justify-between h-40 gap-1">
            {hourlyStats.map((stat) => (
              <div key={stat.hour} className="flex-1 flex flex-col items-center gap-1">
                <div
                  className={`w-full rounded-t transition-all ${
                    stat.hour >= 11 && stat.hour <= 14 ? 'bg-orange-400 hover:bg-orange-500' :
                    stat.hour >= 18 && stat.hour <= 21 ? 'bg-emerald-500 hover:bg-emerald-600' :
                    'bg-gray-300 hover:bg-gray-400'
                  }`}
                  style={{ height: maxOrders > 0 ? `${(stat.order_count / maxOrders) * 100}%` : '2px', minHeight: '2px' }}
                  title={`${stat.order_count} commandes`}
                />
                <span className="text-[10px] text-gray-400">{stat.hour}</span>
              </div>
            ))}
          </div>
          <div className="flex justify-center gap-6 mt-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-orange-400 rounded" />
              <span className="text-gray-600">Dejeuner</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-emerald-500 rounded" />
              <span className="text-gray-600">Diner</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderCustomers = () => {
    const latestStats = customerStats[0];
    if (!latestStats || !dashboard) return null;

    return (
      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <div className="text-sm text-gray-500">{t('customers.conversionRate')}</div>
            <div className="text-2xl font-bold text-emerald-600 mt-1">{dashboard.conversion_rate}%</div>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <div className="text-sm text-gray-500">{t('customers.menuViews')}</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">{latestStats.menu_views}</div>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <div className="text-sm text-gray-500">{t('customers.newCustomers')}</div>
            <div className="text-2xl font-bold text-blue-600 mt-1">{dashboard.new_vs_returning.new}</div>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <div className="text-sm text-gray-500">{t('customers.returningCustomers')}</div>
            <div className="text-2xl font-bold text-purple-600 mt-1">{dashboard.new_vs_returning.returning}</div>
          </div>
        </div>

        {/* Conversion Funnel */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-900 mb-6">{t('customers.funnel')}</h3>
          <div className="space-y-4">
            <div className="relative">
              <div className="flex justify-between text-sm mb-1">
                <span>{t('customers.menuViews')}</span>
                <span className="font-medium">{latestStats.menu_views}</span>
              </div>
              <div className="h-8 bg-blue-100 rounded" />
            </div>
            <div className="relative">
              <div className="flex justify-between text-sm mb-1">
                <span>{t('customers.ordersPlaced')}</span>
                <span className="font-medium">{latestStats.orders_placed}</span>
              </div>
              <div
                className="h-8 bg-emerald-500 rounded"
                style={{ width: `${(latestStats.orders_placed / latestStats.menu_views) * 100}%` }}
              />
            </div>
          </div>
          <div className="mt-4 text-center text-sm text-gray-500">
            {t('customers.conversionRate')}: <span className="font-semibold text-emerald-600">{latestStats.conversion_rate}%</span>
          </div>
        </div>

        {/* New vs Returning */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-900 mb-4">{t('customers.newCustomers')} vs {t('customers.returningCustomers')}</h3>
          <div className="flex items-center gap-4">
            <div className="flex-1 h-8 bg-gray-100 rounded-full overflow-hidden flex">
              <div
                className="h-full bg-blue-500"
                style={{ width: `${(dashboard.new_vs_returning.new / (dashboard.new_vs_returning.new + dashboard.new_vs_returning.returning)) * 100}%` }}
              />
              <div
                className="h-full bg-purple-500"
                style={{ width: `${(dashboard.new_vs_returning.returning / (dashboard.new_vs_returning.new + dashboard.new_vs_returning.returning)) * 100}%` }}
              />
            </div>
          </div>
          <div className="flex justify-center gap-8 mt-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-blue-500 rounded-full" />
              <span className="text-gray-600">{t('customers.newCustomers')}: {dashboard.new_vs_returning.new}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-purple-500 rounded-full" />
              <span className="text-gray-600">{t('customers.returningCustomers')}: {dashboard.new_vs_returning.returning}</span>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderReports = () => (
    <div className="space-y-6">
      {/* Export Form */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="font-semibold text-gray-900 mb-4">{t('reports.exportData')}</h3>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('reports.selectType')}</label>
            <select
              value={exportType}
              onChange={(e) => setExportType(e.target.value as ExportType)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            >
              <option value="sales">{t('reports.types.sales')}</option>
              <option value="items">{t('reports.types.items')}</option>
              <option value="categories">{t('reports.types.categories')}</option>
              <option value="customers">{t('reports.types.customers')}</option>
              <option value="hourly">{t('reports.types.hourly')}</option>
              <option value="full">{t('reports.types.full')}</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('reports.selectFormat')}</label>
            <select
              value={exportFormat}
              onChange={(e) => setExportFormat(e.target.value as ExportFormat)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            >
              <option value="csv">{t('reports.formats.csv')}</option>
              <option value="pdf">{t('reports.formats.pdf')}</option>
              <option value="xlsx">{t('reports.formats.xlsx')}</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('reports.from')}</label>
            <input
              type="date"
              value={exportFrom}
              onChange={(e) => setExportFrom(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">{t('reports.to')}</label>
            <input
              type="date"
              value={exportTo}
              onChange={(e) => setExportTo(e.target.value)}
              className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            />
          </div>
        </div>
        <button
          onClick={handleExport}
          disabled={exporting || !exportFrom || !exportTo}
          className="mt-4 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {exporting ? t('reports.pending') : t('reports.generate')}
        </button>
      </div>

      {/* Weekly Reports */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-4 border-b border-gray-100">
          <h3 className="font-semibold text-gray-900">{t('reports.weeklyReports')}</h3>
        </div>
        <div className="divide-y divide-gray-100">
          {weeklyReports.map((report) => (
            <div key={report.id} className="p-4 hover:bg-gray-50">
              <div className="flex items-center justify-between">
                <div>
                  <div className="font-medium text-gray-900">
                    {formatDate(report.week_start)} - {formatDate(report.week_end)}
                  </div>
                  <div className="text-sm text-gray-500 mt-1">
                    {report.total_orders} commandes | {formatCurrency(report.total_revenue)}
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  <div className={`text-sm ${report.revenue_change_percent >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                    {formatPercent(report.revenue_change_percent)}
                  </div>
                  {report.sent_at ? (
                    <span className="text-xs text-gray-400">Envoye</span>
                  ) : (
                    <button className="text-sm text-emerald-600 hover:text-emerald-700">
                      {t('reports.download')}
                    </button>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Benchmarks */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="p-4 border-b border-gray-100">
          <h3 className="font-semibold text-gray-900">{t('benchmarks.title')}</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('benchmarks.metric')}</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('benchmarks.yourValue')}</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('benchmarks.industryAvg')}</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('benchmarks.percentile')}</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Status</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {benchmarks.map((bench, idx) => (
                <tr key={idx} className="hover:bg-gray-50">
                  <td className="px-4 py-3 text-sm font-medium text-gray-900">{bench.metric}</td>
                  <td className="px-4 py-3 text-sm text-gray-900 text-right">{bench.your_value.toLocaleString()}</td>
                  <td className="px-4 py-3 text-sm text-gray-500 text-right">{bench.industry_average.toLocaleString()}</td>
                  <td className="px-4 py-3 text-sm text-gray-900 text-right">{bench.percentile}%</td>
                  <td className="px-4 py-3 text-center">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${
                      bench.status === 'above' ? 'bg-emerald-100 text-emerald-700' :
                      bench.status === 'average' ? 'bg-yellow-100 text-yellow-700' :
                      'bg-red-100 text-red-700'
                    }`}>
                      {t(`benchmarks.${bench.status}`)}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );

  const renderContent = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600" />
        </div>
      );
    }

    switch (activeTab) {
      case 'overview':
        return renderOverview();
      case 'sales':
        return renderSales();
      case 'items':
        return renderItems();
      case 'categories':
        return renderCategories();
      case 'peakHours':
        return renderPeakHours();
      case 'customers':
        return renderCustomers();
      case 'reports':
        return renderReports();
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-8">
      {/* Header */}
      <div className="bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-2xl font-bold text-gray-900">{t('title')}</h1>
          <p className="text-gray-500 mt-1">{t('subtitle')}</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Period Selector */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex gap-2">
            {tabs.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  activeTab === tab
                    ? 'bg-emerald-100 text-emerald-700'
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                {TAB_ICONS[tab]}
                <span className="hidden sm:inline">{t(`tabs.${tab}`)}</span>
              </button>
            ))}
          </div>
          <select
            value={period}
            onChange={(e) => setPeriod(e.target.value as Period)}
            className="px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
          >
            <option value="last7">{t('period.last7')}</option>
            <option value="last30">{t('period.last30')}</option>
            <option value="last90">{t('period.last90')}</option>
          </select>
        </div>

        {/* Content */}
        {renderContent()}
      </div>
    </div>
  );
}
