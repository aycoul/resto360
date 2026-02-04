'use client';

import { useState, useEffect, ReactNode } from 'react';
import { useTranslations } from 'next-intl';

type Tab = 'overview' | 'daily' | 'weekly' | 'events' | 'weather';

interface DailyForecast {
  date: string;
  predicted_revenue: number;
  predicted_orders: number;
  confidence: number;
  weather_factor: number;
  event_factor: number;
  day_factor: number;
  actual_revenue?: number;
  actual_orders?: number;
}

interface WeeklyForecast {
  week_start: string;
  week_end: string;
  predicted_revenue: number;
  predicted_orders: number;
  confidence: number;
  key_events: string[];
}

interface BusinessEvent {
  id: string;
  name: string;
  date: string;
  event_type: string;
  expected_impact: string;
  is_recurring: boolean;
}

interface WeatherData {
  date: string;
  temperature_high: number;
  temperature_low: number;
  condition: string;
  precipitation_mm: number;
  impact_factor: number;
}

interface ForecastSummary {
  next_7_days_revenue: number;
  next_7_days_orders: number;
  next_30_days_revenue: number;
  next_30_days_orders: number;
  best_day_predicted: { date: string; revenue: number };
  slowest_day_predicted: { date: string; revenue: number };
  accuracy_last_30: number;
  upcoming_events: number;
}

const TAB_ICONS: Record<Tab, ReactNode> = {
  overview: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
    </svg>
  ),
  daily: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
    </svg>
  ),
  weekly: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
    </svg>
  ),
  events: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11.049 2.927c.3-.921 1.603-.921 1.902 0l1.519 4.674a1 1 0 00.95.69h4.915c.969 0 1.371 1.24.588 1.81l-3.976 2.888a1 1 0 00-.363 1.118l1.518 4.674c.3.922-.755 1.688-1.538 1.118l-3.976-2.888a1 1 0 00-1.176 0l-3.976 2.888c-.783.57-1.838-.197-1.538-1.118l1.518-4.674a1 1 0 00-.363-1.118l-3.976-2.888c-.784-.57-.38-1.81.588-1.81h4.914a1 1 0 00.951-.69l1.519-4.674z" />
    </svg>
  ),
  weather: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 15a4 4 0 004 4h9a5 5 0 10-.1-9.999 5.002 5.002 0 10-9.78 2.096A4.001 4.001 0 003 15z" />
    </svg>
  ),
};

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('fr-FR', { style: 'decimal' }).format(value) + ' XOF';
}

function formatPercent(value: number): string {
  return `${value.toFixed(0)}%`;
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('fr-FR', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  });
}

function formatShortDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'short',
  });
}

function getWeatherIcon(condition: string): ReactNode {
  switch (condition.toLowerCase()) {
    case 'sunny':
    case 'clear':
      return (
        <svg className="w-6 h-6 text-yellow-500" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 2.25a.75.75 0 01.75.75v2.25a.75.75 0 01-1.5 0V3a.75.75 0 01.75-.75zM7.5 12a4.5 4.5 0 119 0 4.5 4.5 0 01-9 0zM18.894 6.166a.75.75 0 00-1.06-1.06l-1.591 1.59a.75.75 0 101.06 1.061l1.591-1.59zM21.75 12a.75.75 0 01-.75.75h-2.25a.75.75 0 010-1.5H21a.75.75 0 01.75.75zM17.834 18.894a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 10-1.061 1.06l1.59 1.591zM12 18a.75.75 0 01.75.75V21a.75.75 0 01-1.5 0v-2.25A.75.75 0 0112 18zM7.758 17.303a.75.75 0 00-1.061-1.06l-1.591 1.59a.75.75 0 001.06 1.061l1.591-1.59zM6 12a.75.75 0 01-.75.75H3a.75.75 0 010-1.5h2.25A.75.75 0 016 12zM6.697 7.757a.75.75 0 001.06-1.06l-1.59-1.591a.75.75 0 00-1.061 1.06l1.59 1.591z" />
        </svg>
      );
    case 'cloudy':
    case 'overcast':
      return (
        <svg className="w-6 h-6 text-gray-500" fill="currentColor" viewBox="0 0 24 24">
          <path fillRule="evenodd" d="M4.5 9.75a6 6 0 0111.573-2.226 3.75 3.75 0 014.133 4.303A4.5 4.5 0 0118 20.25H6.75a5.25 5.25 0 01-2.23-10.004 6.072 6.072 0 01-.02-.496z" clipRule="evenodd" />
        </svg>
      );
    case 'rainy':
    case 'rain':
      return (
        <svg className="w-6 h-6 text-blue-500" fill="currentColor" viewBox="0 0 24 24">
          <path fillRule="evenodd" d="M4.5 9.75a6 6 0 0111.573-2.226 3.75 3.75 0 014.133 4.303A4.5 4.5 0 0118 20.25H6.75a5.25 5.25 0 01-2.23-10.004 6.072 6.072 0 01-.02-.496zM8.25 12a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5a.75.75 0 01.75-.75zm3 0a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5a.75.75 0 01.75-.75zm3 0a.75.75 0 01.75.75v4.5a.75.75 0 01-1.5 0v-4.5a.75.75 0 01.75-.75z" clipRule="evenodd" />
        </svg>
      );
    default:
      return (
        <svg className="w-6 h-6 text-gray-400" fill="currentColor" viewBox="0 0 24 24">
          <path fillRule="evenodd" d="M4.5 9.75a6 6 0 0111.573-2.226 3.75 3.75 0 014.133 4.303A4.5 4.5 0 0118 20.25H6.75a5.25 5.25 0 01-2.23-10.004 6.072 6.072 0 01-.02-.496z" clipRule="evenodd" />
        </svg>
      );
  }
}

function getImpactColor(impact: string): string {
  switch (impact) {
    case 'very_positive':
      return 'bg-emerald-100 text-emerald-700';
    case 'positive':
      return 'bg-green-100 text-green-700';
    case 'neutral':
      return 'bg-gray-100 text-gray-700';
    case 'negative':
      return 'bg-orange-100 text-orange-700';
    case 'very_negative':
      return 'bg-red-100 text-red-700';
    default:
      return 'bg-gray-100 text-gray-700';
  }
}

function getImpactLabel(impact: string, t: (key: string) => string): string {
  switch (impact) {
    case 'very_positive':
      return t('events.impactVeryPositive');
    case 'positive':
      return t('events.impactPositive');
    case 'neutral':
      return t('events.impactNeutral');
    case 'negative':
      return t('events.impactNegative');
    case 'very_negative':
      return t('events.impactVeryNegative');
    default:
      return impact;
  }
}

export default function ForecastingPage() {
  const t = useTranslations('lite.forecasting');
  const [activeTab, setActiveTab] = useState<Tab>('overview');
  const [loading, setLoading] = useState(true);

  // Forecast data
  const [summary, setSummary] = useState<ForecastSummary | null>(null);
  const [dailyForecasts, setDailyForecasts] = useState<DailyForecast[]>([]);
  const [weeklyForecasts, setWeeklyForecasts] = useState<WeeklyForecast[]>([]);
  const [events, setEvents] = useState<BusinessEvent[]>([]);
  const [weatherData, setWeatherData] = useState<WeatherData[]>([]);

  // Event form
  const [showEventForm, setShowEventForm] = useState(false);
  const [newEvent, setNewEvent] = useState({
    name: '',
    date: '',
    event_type: 'local_event',
    expected_impact: 'positive',
  });

  const tabs: Tab[] = ['overview', 'daily', 'weekly', 'events', 'weather'];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      // Simulate API call with mock data
      await new Promise(resolve => setTimeout(resolve, 500));

      // Generate dates for next 14 days
      const today = new Date();
      const dailyData: DailyForecast[] = [];

      for (let i = 0; i < 14; i++) {
        const date = new Date(today);
        date.setDate(date.getDate() + i);
        const dayOfWeek = date.getDay();

        // Weekend has higher sales
        const dayFactor = dayOfWeek === 0 || dayOfWeek === 6 ? 1.3 :
                         dayOfWeek === 5 ? 1.2 : 1.0;

        // Random weather factor
        const weatherFactor = 0.85 + Math.random() * 0.3;

        // Random event factor (occasional event)
        const eventFactor = Math.random() > 0.8 ? 1.2 + Math.random() * 0.3 : 1.0;

        const baseRevenue = 350000;
        const predictedRevenue = Math.round(baseRevenue * dayFactor * weatherFactor * eventFactor);
        const predictedOrders = Math.round(predictedRevenue / 7000);

        // Add actual data for past days (mock)
        const isPast = i < 3;

        dailyData.push({
          date: date.toISOString().split('T')[0],
          predicted_revenue: predictedRevenue,
          predicted_orders: predictedOrders,
          confidence: 0.75 + Math.random() * 0.2,
          weather_factor: weatherFactor,
          event_factor: eventFactor,
          day_factor: dayFactor,
          actual_revenue: isPast ? Math.round(predictedRevenue * (0.9 + Math.random() * 0.2)) : undefined,
          actual_orders: isPast ? Math.round(predictedOrders * (0.9 + Math.random() * 0.2)) : undefined,
        });
      }

      setDailyForecasts(dailyData);

      // Weekly forecasts
      const weeklyData: WeeklyForecast[] = [];
      for (let i = 0; i < 4; i++) {
        const weekStart = new Date(today);
        weekStart.setDate(weekStart.getDate() + (i * 7));
        const weekEnd = new Date(weekStart);
        weekEnd.setDate(weekEnd.getDate() + 6);

        const weekRevenue = dailyData
          .filter(d => {
            const dDate = new Date(d.date);
            return dDate >= weekStart && dDate <= weekEnd;
          })
          .reduce((sum, d) => sum + d.predicted_revenue, 0) || 2450000 + Math.random() * 500000;

        weeklyData.push({
          week_start: weekStart.toISOString().split('T')[0],
          week_end: weekEnd.toISOString().split('T')[0],
          predicted_revenue: Math.round(weekRevenue),
          predicted_orders: Math.round(weekRevenue / 7000),
          confidence: 0.7 + Math.random() * 0.15,
          key_events: i === 0 ? ['Weekend'] : i === 1 ? ['Jour ferie prevu'] : [],
        });
      }
      setWeeklyForecasts(weeklyData);

      // Summary
      const next7Days = dailyData.slice(0, 7);
      const sortedByRevenue = [...next7Days].sort((a, b) => b.predicted_revenue - a.predicted_revenue);

      setSummary({
        next_7_days_revenue: next7Days.reduce((sum, d) => sum + d.predicted_revenue, 0),
        next_7_days_orders: next7Days.reduce((sum, d) => sum + d.predicted_orders, 0),
        next_30_days_revenue: Math.round(next7Days.reduce((sum, d) => sum + d.predicted_revenue, 0) * 4.3),
        next_30_days_orders: Math.round(next7Days.reduce((sum, d) => sum + d.predicted_orders, 0) * 4.3),
        best_day_predicted: { date: sortedByRevenue[0].date, revenue: sortedByRevenue[0].predicted_revenue },
        slowest_day_predicted: { date: sortedByRevenue[sortedByRevenue.length - 1].date, revenue: sortedByRevenue[sortedByRevenue.length - 1].predicted_revenue },
        accuracy_last_30: 87.5,
        upcoming_events: 3,
      });

      // Events
      setEvents([
        { id: '1', name: 'Fete de l\'Independance', date: '2026-08-07', event_type: 'national_holiday', expected_impact: 'very_positive', is_recurring: true },
        { id: '2', name: 'Week-end Promo', date: '2026-02-08', event_type: 'promotion', expected_impact: 'positive', is_recurring: false },
        { id: '3', name: 'Match CAN', date: '2026-02-15', event_type: 'local_event', expected_impact: 'very_positive', is_recurring: false },
        { id: '4', name: 'Eid al-Fitr', date: '2026-03-30', event_type: 'religious_holiday', expected_impact: 'very_positive', is_recurring: true },
      ]);

      // Weather data
      const weatherDataArr: WeatherData[] = [];
      const conditions = ['sunny', 'cloudy', 'rainy', 'sunny', 'sunny', 'cloudy', 'rainy'];
      for (let i = 0; i < 7; i++) {
        const date = new Date(today);
        date.setDate(date.getDate() + i);
        const condition = conditions[i % conditions.length];

        weatherDataArr.push({
          date: date.toISOString().split('T')[0],
          temperature_high: 30 + Math.round(Math.random() * 5),
          temperature_low: 22 + Math.round(Math.random() * 3),
          condition,
          precipitation_mm: condition === 'rainy' ? 5 + Math.round(Math.random() * 15) : 0,
          impact_factor: condition === 'rainy' ? 0.85 : condition === 'cloudy' ? 0.95 : 1.0,
        });
      }
      setWeatherData(weatherDataArr);

    } catch (error) {
      console.error('Failed to load forecasting data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleAddEvent = async () => {
    if (!newEvent.name || !newEvent.date) return;

    // Mock add event
    const event: BusinessEvent = {
      id: String(Date.now()),
      name: newEvent.name,
      date: newEvent.date,
      event_type: newEvent.event_type,
      expected_impact: newEvent.expected_impact,
      is_recurring: false,
    };

    setEvents(prev => [...prev, event].sort((a, b) => a.date.localeCompare(b.date)));
    setNewEvent({ name: '', date: '', event_type: 'local_event', expected_impact: 'positive' });
    setShowEventForm(false);
  };

  const renderOverview = () => {
    if (!summary) return null;

    const maxRevenue = Math.max(...dailyForecasts.slice(0, 7).map(d => d.predicted_revenue));

    return (
      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <div className="text-sm text-gray-500">{t('overview.next7DaysRevenue')}</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">{formatCurrency(summary.next_7_days_revenue)}</div>
            <div className="text-sm text-emerald-600 mt-1">{summary.next_7_days_orders} {t('overview.orders')}</div>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <div className="text-sm text-gray-500">{t('overview.next30DaysRevenue')}</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">{formatCurrency(summary.next_30_days_revenue)}</div>
            <div className="text-sm text-emerald-600 mt-1">{summary.next_30_days_orders} {t('overview.orders')}</div>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <div className="text-sm text-gray-500">{t('overview.accuracy')}</div>
            <div className="text-2xl font-bold text-emerald-600 mt-1">{summary.accuracy_last_30}%</div>
            <div className="text-sm text-gray-500 mt-1">{t('overview.last30Days')}</div>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <div className="text-sm text-gray-500">{t('overview.upcomingEvents')}</div>
            <div className="text-2xl font-bold text-purple-600 mt-1">{summary.upcoming_events}</div>
            <div className="text-sm text-gray-500 mt-1">{t('overview.eventsThisMonth')}</div>
          </div>
        </div>

        {/* Best & Slowest Days */}
        <div className="grid lg:grid-cols-2 gap-4">
          <div className="bg-gradient-to-r from-emerald-500 to-emerald-600 rounded-xl p-6 text-white">
            <div className="text-emerald-100 text-sm">{t('overview.bestDayPredicted')}</div>
            <div className="text-2xl font-bold mt-1">{formatDate(summary.best_day_predicted.date)}</div>
            <div className="text-emerald-100 mt-2">{t('overview.expectedRevenue')}: {formatCurrency(summary.best_day_predicted.revenue)}</div>
          </div>
          <div className="bg-gradient-to-r from-orange-500 to-orange-600 rounded-xl p-6 text-white">
            <div className="text-orange-100 text-sm">{t('overview.slowestDayPredicted')}</div>
            <div className="text-2xl font-bold mt-1">{formatDate(summary.slowest_day_predicted.date)}</div>
            <div className="text-orange-100 mt-2">{t('overview.expectedRevenue')}: {formatCurrency(summary.slowest_day_predicted.revenue)}</div>
          </div>
        </div>

        {/* 7-Day Forecast Chart */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-900 mb-4">{t('overview.next7DaysForecast')}</h3>
          <div className="flex items-end justify-between h-48 gap-2">
            {dailyForecasts.slice(0, 7).map((day, idx) => (
              <div key={idx} className="flex-1 flex flex-col items-center gap-2">
                <div
                  className="w-full bg-emerald-500 rounded-t transition-all hover:bg-emerald-600 relative group"
                  style={{ height: `${(day.predicted_revenue / maxRevenue) * 100}%` }}
                >
                  <div className="absolute -top-8 left-1/2 transform -translate-x-1/2 bg-gray-800 text-white text-xs px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap">
                    {formatCurrency(day.predicted_revenue)}
                  </div>
                </div>
                <span className="text-xs text-gray-500">{formatShortDate(day.date)}</span>
                <div className="flex items-center gap-1">
                  {day.event_factor > 1 && (
                    <span className="w-2 h-2 bg-purple-500 rounded-full" title={t('overview.eventImpact')} />
                  )}
                  {day.weather_factor < 0.95 && (
                    <span className="w-2 h-2 bg-blue-500 rounded-full" title={t('overview.weatherImpact')} />
                  )}
                </div>
              </div>
            ))}
          </div>
          <div className="flex justify-center gap-6 mt-4 text-sm">
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-purple-500 rounded-full" />
              <span className="text-gray-600">{t('overview.eventImpact')}</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-2 h-2 bg-blue-500 rounded-full" />
              <span className="text-gray-600">{t('overview.weatherImpact')}</span>
            </div>
          </div>
        </div>

        {/* Factors Breakdown */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-900 mb-4">{t('overview.forecastFactors')}</h3>
          <p className="text-sm text-gray-500 mb-4">{t('overview.factorsDescription')}</p>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-3xl mb-2">📅</div>
              <div className="font-medium text-gray-900">{t('overview.factorDayOfWeek')}</div>
              <div className="text-sm text-gray-500">{t('overview.factorDayDesc')}</div>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <div className="text-3xl mb-2">🌤️</div>
              <div className="font-medium text-gray-900">{t('overview.factorWeather')}</div>
              <div className="text-sm text-gray-500">{t('overview.factorWeatherDesc')}</div>
            </div>
            <div className="text-center p-4 bg-purple-50 rounded-lg">
              <div className="text-3xl mb-2">🎉</div>
              <div className="font-medium text-gray-900">{t('overview.factorEvents')}</div>
              <div className="text-sm text-gray-500">{t('overview.factorEventsDesc')}</div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderDaily = () => (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="p-4 border-b border-gray-100">
        <h3 className="font-semibold text-gray-900">{t('daily.title')}</h3>
        <p className="text-sm text-gray-500 mt-1">{t('daily.subtitle')}</p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('daily.date')}</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('daily.predictedRevenue')}</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('daily.predictedOrders')}</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">{t('daily.confidence')}</th>
              <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">{t('daily.factors')}</th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('daily.actual')}</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {dailyForecasts.map((forecast) => (
              <tr key={forecast.date} className="hover:bg-gray-50">
                <td className="px-4 py-3 text-sm font-medium text-gray-900">{formatDate(forecast.date)}</td>
                <td className="px-4 py-3 text-sm text-gray-900 text-right">{formatCurrency(forecast.predicted_revenue)}</td>
                <td className="px-4 py-3 text-sm text-gray-900 text-right">{forecast.predicted_orders}</td>
                <td className="px-4 py-3 text-center">
                  <div className="flex items-center justify-center gap-1">
                    <div className="w-16 h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${forecast.confidence >= 0.85 ? 'bg-emerald-500' : forecast.confidence >= 0.7 ? 'bg-yellow-500' : 'bg-orange-500'}`}
                        style={{ width: `${forecast.confidence * 100}%` }}
                      />
                    </div>
                    <span className="text-xs text-gray-500">{formatPercent(forecast.confidence * 100)}</span>
                  </div>
                </td>
                <td className="px-4 py-3 text-center">
                  <div className="flex items-center justify-center gap-2">
                    {forecast.day_factor > 1.1 && (
                      <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded-full">+{t('daily.weekend')}</span>
                    )}
                    {forecast.event_factor > 1 && (
                      <span className="px-2 py-0.5 text-xs bg-purple-100 text-purple-700 rounded-full">+{t('daily.event')}</span>
                    )}
                    {forecast.weather_factor < 0.9 && (
                      <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded-full">-{t('daily.rain')}</span>
                    )}
                  </div>
                </td>
                <td className="px-4 py-3 text-sm text-right">
                  {forecast.actual_revenue !== undefined ? (
                    <div>
                      <div className="font-medium text-gray-900">{formatCurrency(forecast.actual_revenue)}</div>
                      <div className={`text-xs ${forecast.actual_revenue >= forecast.predicted_revenue ? 'text-emerald-600' : 'text-orange-600'}`}>
                        {forecast.actual_revenue >= forecast.predicted_revenue ? '+' : ''}{formatPercent(((forecast.actual_revenue - forecast.predicted_revenue) / forecast.predicted_revenue) * 100)}
                      </div>
                    </div>
                  ) : (
                    <span className="text-gray-400">-</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );

  const renderWeekly = () => (
    <div className="space-y-6">
      {weeklyForecasts.map((week) => (
        <div key={week.week_start} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="font-semibold text-gray-900">
                {formatShortDate(week.week_start)} - {formatShortDate(week.week_end)}
              </h3>
              <div className="flex items-center gap-1 mt-1">
                <div className="w-20 h-2 bg-gray-100 rounded-full overflow-hidden">
                  <div
                    className={`h-full rounded-full ${week.confidence >= 0.8 ? 'bg-emerald-500' : week.confidence >= 0.65 ? 'bg-yellow-500' : 'bg-orange-500'}`}
                    style={{ width: `${week.confidence * 100}%` }}
                  />
                </div>
                <span className="text-xs text-gray-500">{formatPercent(week.confidence * 100)} {t('weekly.confidence')}</span>
              </div>
            </div>
            <div className="text-right">
              <div className="text-2xl font-bold text-gray-900">{formatCurrency(week.predicted_revenue)}</div>
              <div className="text-sm text-gray-500">{week.predicted_orders} {t('weekly.orders')}</div>
            </div>
          </div>
          {week.key_events.length > 0 && (
            <div className="mt-4 pt-4 border-t border-gray-100">
              <div className="text-sm text-gray-500 mb-2">{t('weekly.keyEvents')}:</div>
              <div className="flex flex-wrap gap-2">
                {week.key_events.map((event, idx) => (
                  <span key={idx} className="px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-sm">
                    {event}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}
    </div>
  );

  const renderEvents = () => (
    <div className="space-y-6">
      {/* Add Event Button */}
      <div className="flex justify-between items-center">
        <div>
          <h3 className="font-semibold text-gray-900">{t('events.title')}</h3>
          <p className="text-sm text-gray-500">{t('events.subtitle')}</p>
        </div>
        <button
          onClick={() => setShowEventForm(!showEventForm)}
          className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
        >
          {showEventForm ? t('events.cancel') : t('events.addEvent')}
        </button>
      </div>

      {/* Add Event Form */}
      {showEventForm && (
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h4 className="font-medium text-gray-900 mb-4">{t('events.newEvent')}</h4>
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('events.eventName')}</label>
              <input
                type="text"
                value={newEvent.name}
                onChange={(e) => setNewEvent(prev => ({ ...prev, name: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                placeholder={t('events.eventNamePlaceholder')}
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('events.eventDate')}</label>
              <input
                type="date"
                value={newEvent.date}
                onChange={(e) => setNewEvent(prev => ({ ...prev, date: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('events.eventType')}</label>
              <select
                value={newEvent.event_type}
                onChange={(e) => setNewEvent(prev => ({ ...prev, event_type: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              >
                <option value="local_event">{t('events.typeLocal')}</option>
                <option value="promotion">{t('events.typePromotion')}</option>
                <option value="national_holiday">{t('events.typeNational')}</option>
                <option value="religious_holiday">{t('events.typeReligious')}</option>
                <option value="competition">{t('events.typeCompetition')}</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('events.expectedImpact')}</label>
              <select
                value={newEvent.expected_impact}
                onChange={(e) => setNewEvent(prev => ({ ...prev, expected_impact: e.target.value }))}
                className="w-full px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
              >
                <option value="very_positive">{t('events.impactVeryPositive')}</option>
                <option value="positive">{t('events.impactPositive')}</option>
                <option value="neutral">{t('events.impactNeutral')}</option>
                <option value="negative">{t('events.impactNegative')}</option>
                <option value="very_negative">{t('events.impactVeryNegative')}</option>
              </select>
            </div>
          </div>
          <button
            onClick={handleAddEvent}
            disabled={!newEvent.name || !newEvent.date}
            className="mt-4 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {t('events.save')}
          </button>
        </div>
      )}

      {/* Events List */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="divide-y divide-gray-100">
          {events.map((event) => (
            <div key={event.id} className="p-4 hover:bg-gray-50 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 rounded-lg bg-purple-100 flex items-center justify-center">
                  <span className="text-2xl">
                    {event.event_type === 'national_holiday' ? '🇨🇮' :
                     event.event_type === 'religious_holiday' ? '🕌' :
                     event.event_type === 'promotion' ? '🏷️' :
                     event.event_type === 'competition' ? '⚽' : '📅'}
                  </span>
                </div>
                <div>
                  <div className="font-medium text-gray-900">{event.name}</div>
                  <div className="text-sm text-gray-500">{formatDate(event.date)}</div>
                </div>
              </div>
              <div className="flex items-center gap-3">
                <span className={`px-3 py-1 text-sm rounded-full ${getImpactColor(event.expected_impact)}`}>
                  {getImpactLabel(event.expected_impact, t)}
                </span>
                {event.is_recurring && (
                  <span className="text-xs text-gray-400">{t('events.recurring')}</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );

  const renderWeather = () => (
    <div className="space-y-6">
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="font-semibold text-gray-900 mb-2">{t('weather.title')}</h3>
        <p className="text-sm text-gray-500 mb-6">{t('weather.subtitle')}</p>

        <div className="grid grid-cols-7 gap-3">
          {weatherData.map((day) => (
            <div key={day.date} className="text-center p-4 bg-gray-50 rounded-xl">
              <div className="text-sm font-medium text-gray-900 mb-2">{formatShortDate(day.date)}</div>
              <div className="flex justify-center mb-2">
                {getWeatherIcon(day.condition)}
              </div>
              <div className="text-sm text-gray-600 capitalize mb-2">{day.condition}</div>
              <div className="text-lg font-bold text-gray-900">{day.temperature_high}°</div>
              <div className="text-sm text-gray-500">{day.temperature_low}°</div>
              {day.precipitation_mm > 0 && (
                <div className="text-xs text-blue-600 mt-1">{day.precipitation_mm}mm</div>
              )}
              <div className={`mt-2 text-xs font-medium ${day.impact_factor >= 1 ? 'text-emerald-600' : 'text-orange-600'}`}>
                {day.impact_factor >= 1 ? t('weather.noImpact') : `${Math.round((1 - day.impact_factor) * 100)}% ${t('weather.reduction')}`}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Weather Impact Explanation */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="font-semibold text-gray-900 mb-4">{t('weather.howItWorks')}</h3>
        <div className="space-y-4">
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-full bg-yellow-100 flex items-center justify-center flex-shrink-0">
              {getWeatherIcon('sunny')}
            </div>
            <div>
              <div className="font-medium text-gray-900">{t('weather.sunny')}</div>
              <div className="text-sm text-gray-500">{t('weather.sunnyDesc')}</div>
            </div>
          </div>
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-full bg-gray-100 flex items-center justify-center flex-shrink-0">
              {getWeatherIcon('cloudy')}
            </div>
            <div>
              <div className="font-medium text-gray-900">{t('weather.cloudy')}</div>
              <div className="text-sm text-gray-500">{t('weather.cloudyDesc')}</div>
            </div>
          </div>
          <div className="flex items-start gap-4">
            <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
              {getWeatherIcon('rainy')}
            </div>
            <div>
              <div className="font-medium text-gray-900">{t('weather.rainy')}</div>
              <div className="text-sm text-gray-500">{t('weather.rainyDesc')}</div>
            </div>
          </div>
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
      case 'daily':
        return renderDaily();
      case 'weekly':
        return renderWeekly();
      case 'events':
        return renderEvents();
      case 'weather':
        return renderWeather();
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
        {/* Tabs */}
        <div className="flex gap-2 mb-6 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors whitespace-nowrap ${
                activeTab === tab
                  ? 'bg-emerald-100 text-emerald-700'
                  : 'text-gray-600 hover:bg-gray-100'
              }`}
            >
              {TAB_ICONS[tab]}
              {t(`tabs.${tab}`)}
            </button>
          ))}
        </div>

        {/* Content */}
        {renderContent()}
      </div>
    </div>
  );
}
