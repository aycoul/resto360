'use client';

import { useState, useEffect, ReactNode } from 'react';
import { useTranslations } from 'next-intl';

type Tab = 'invoices' | 'configuration' | 'reports';
type InvoiceStatus = 'draft' | 'pending_validation' | 'validated' | 'rejected' | 'cancelled';

interface Invoice {
  id: string;
  invoice_number: string;
  order_id: string;
  invoice_date: string;
  customer_name: string;
  customer_ncc: string;
  subtotal_ht: number;
  tva_amount: number;
  total_ttc: number;
  status: InvoiceStatus;
  dgi_uid: string;
  dgi_submitted_at: string | null;
}

interface DGIConfig {
  taxpayer_id: string;
  establishment_id: string;
  is_production: boolean;
  is_active: boolean;
  last_sync_at: string | null;
}

interface MonthlyReport {
  month: string;
  year: number;
  total_invoices: number;
  validated_invoices: number;
  total_ht: number;
  total_tva: number;
  total_ttc: number;
}

const TAB_ICONS: Record<Tab, ReactNode> = {
  invoices: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  ),
  configuration: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
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

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

function formatDateTime(dateString: string): string {
  return new Date(dateString).toLocaleString('fr-FR', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

function getStatusColor(status: InvoiceStatus): string {
  switch (status) {
    case 'validated':
      return 'bg-emerald-100 text-emerald-700';
    case 'pending_validation':
      return 'bg-yellow-100 text-yellow-700';
    case 'draft':
      return 'bg-gray-100 text-gray-700';
    case 'rejected':
      return 'bg-red-100 text-red-700';
    case 'cancelled':
      return 'bg-gray-100 text-gray-500';
    default:
      return 'bg-gray-100 text-gray-700';
  }
}

export default function InvoicingPage() {
  const t = useTranslations('lite.invoicing');
  const [activeTab, setActiveTab] = useState<Tab>('invoices');
  const [loading, setLoading] = useState(true);

  // Data state
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [config, setConfig] = useState<DGIConfig | null>(null);
  const [monthlyReports, setMonthlyReports] = useState<MonthlyReport[]>([]);

  // Filter state
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Config form state
  const [configForm, setConfigForm] = useState({
    taxpayer_id: '',
    establishment_id: '',
    api_key: '',
    api_secret: '',
    is_production: false,
  });
  const [savingConfig, setSavingConfig] = useState(false);

  const tabs: Tab[] = ['invoices', 'configuration', 'reports'];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 500));

      // Mock invoices
      const mockInvoices: Invoice[] = [
        {
          id: '1',
          invoice_number: 'BIZ-001-2026-000045',
          order_id: 'ORD-2026-0045',
          invoice_date: '2026-02-04T14:30:00Z',
          customer_name: 'Entreprise ABC SARL',
          customer_ncc: 'CI1234567890',
          subtotal_ht: 84750,
          tva_amount: 15255,
          total_ttc: 100005,
          status: 'validated',
          dgi_uid: 'DGI-2026-ABC123',
          dgi_submitted_at: '2026-02-04T14:31:00Z',
        },
        {
          id: '2',
          invoice_number: 'BIZ-001-2026-000044',
          order_id: 'ORD-2026-0044',
          invoice_date: '2026-02-04T12:15:00Z',
          customer_name: 'Restaurant Le Gourmet',
          customer_ncc: '',
          subtotal_ht: 42500,
          tva_amount: 7650,
          total_ttc: 50150,
          status: 'pending_validation',
          dgi_uid: '',
          dgi_submitted_at: '2026-02-04T12:16:00Z',
        },
        {
          id: '3',
          invoice_number: 'BIZ-001-2026-000043',
          order_id: 'ORD-2026-0043',
          invoice_date: '2026-02-03T18:45:00Z',
          customer_name: 'Client Particulier',
          customer_ncc: '',
          subtotal_ht: 15000,
          tva_amount: 2700,
          total_ttc: 17700,
          status: 'validated',
          dgi_uid: 'DGI-2026-DEF456',
          dgi_submitted_at: '2026-02-03T18:46:00Z',
        },
        {
          id: '4',
          invoice_number: 'BIZ-001-2026-000042',
          order_id: 'ORD-2026-0042',
          invoice_date: '2026-02-03T15:20:00Z',
          customer_name: 'Hotel Ivoire',
          customer_ncc: 'CI9876543210',
          subtotal_ht: 250000,
          tva_amount: 45000,
          total_ttc: 295000,
          status: 'validated',
          dgi_uid: 'DGI-2026-GHI789',
          dgi_submitted_at: '2026-02-03T15:21:00Z',
        },
        {
          id: '5',
          invoice_number: 'BIZ-001-2026-000041',
          order_id: 'ORD-2026-0041',
          invoice_date: '2026-02-02T10:00:00Z',
          customer_name: 'Test Client',
          customer_ncc: '',
          subtotal_ht: 8500,
          tva_amount: 1530,
          total_ttc: 10030,
          status: 'rejected',
          dgi_uid: '',
          dgi_submitted_at: '2026-02-02T10:01:00Z',
        },
      ];
      setInvoices(mockInvoices);

      // Mock config
      setConfig({
        taxpayer_id: 'CI1234567890',
        establishment_id: 'ETB001',
        is_production: false,
        is_active: true,
        last_sync_at: '2026-02-04T10:00:00Z',
      });

      setConfigForm({
        taxpayer_id: 'CI1234567890',
        establishment_id: 'ETB001',
        api_key: '••••••••••••••••',
        api_secret: '••••••••••••••••',
        is_production: false,
      });

      // Mock monthly reports
      setMonthlyReports([
        {
          month: 'Fevrier',
          year: 2026,
          total_invoices: 45,
          validated_invoices: 42,
          total_ht: 2850000,
          total_tva: 513000,
          total_ttc: 3363000,
        },
        {
          month: 'Janvier',
          year: 2026,
          total_invoices: 312,
          validated_invoices: 310,
          total_ht: 18500000,
          total_tva: 3330000,
          total_ttc: 21830000,
        },
        {
          month: 'Decembre',
          year: 2025,
          total_invoices: 287,
          validated_invoices: 287,
          total_ht: 16200000,
          total_tva: 2916000,
          total_ttc: 19116000,
        },
      ]);

    } catch (error) {
      console.error('Failed to load invoicing data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveConfig = async () => {
    setSavingConfig(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      // In real app, save to API
      alert(t('config.saved'));
    } catch (error) {
      console.error('Failed to save config:', error);
    } finally {
      setSavingConfig(false);
    }
  };

  const handleRetrySubmission = async (invoiceId: string) => {
    // Mock retry submission
    setInvoices(prev => prev.map(inv =>
      inv.id === invoiceId ? { ...inv, status: 'pending_validation' as InvoiceStatus } : inv
    ));
  };

  const filteredInvoices = invoices.filter(inv => {
    if (statusFilter !== 'all' && inv.status !== statusFilter) return false;
    if (searchQuery && !inv.invoice_number.toLowerCase().includes(searchQuery.toLowerCase()) &&
        !inv.customer_name.toLowerCase().includes(searchQuery.toLowerCase())) return false;
    return true;
  });

  const renderInvoices = () => (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <div className="text-sm text-gray-500">{t('invoices.totalInvoices')}</div>
          <div className="text-2xl font-bold text-gray-900 mt-1">{invoices.length}</div>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <div className="text-sm text-gray-500">{t('invoices.validated')}</div>
          <div className="text-2xl font-bold text-emerald-600 mt-1">
            {invoices.filter(i => i.status === 'validated').length}
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <div className="text-sm text-gray-500">{t('invoices.pending')}</div>
          <div className="text-2xl font-bold text-yellow-600 mt-1">
            {invoices.filter(i => i.status === 'pending_validation').length}
          </div>
        </div>
        <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
          <div className="text-sm text-gray-500">{t('invoices.rejected')}</div>
          <div className="text-2xl font-bold text-red-600 mt-1">
            {invoices.filter(i => i.status === 'rejected').length}
          </div>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={t('invoices.searchPlaceholder')}
              className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            />
          </div>
          <div>
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            >
              <option value="all">{t('invoices.allStatuses')}</option>
              <option value="validated">{t('invoices.statusValidated')}</option>
              <option value="pending_validation">{t('invoices.statusPending')}</option>
              <option value="draft">{t('invoices.statusDraft')}</option>
              <option value="rejected">{t('invoices.statusRejected')}</option>
              <option value="cancelled">{t('invoices.statusCancelled')}</option>
            </select>
          </div>
        </div>
      </div>

      {/* Invoices Table */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('invoices.number')}</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('invoices.date')}</th>
                <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">{t('invoices.customer')}</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('invoices.amountHT')}</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('invoices.tva')}</th>
                <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">{t('invoices.amountTTC')}</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">{t('invoices.status')}</th>
                <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">{t('invoices.actions')}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-100">
              {filteredInvoices.map((invoice) => (
                <tr key={invoice.id} className="hover:bg-gray-50">
                  <td className="px-4 py-3">
                    <div className="font-medium text-gray-900">{invoice.invoice_number}</div>
                    {invoice.dgi_uid && (
                      <div className="text-xs text-gray-500">{invoice.dgi_uid}</div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-500">{formatDateTime(invoice.invoice_date)}</td>
                  <td className="px-4 py-3">
                    <div className="text-sm text-gray-900">{invoice.customer_name}</div>
                    {invoice.customer_ncc && (
                      <div className="text-xs text-gray-500">NCC: {invoice.customer_ncc}</div>
                    )}
                  </td>
                  <td className="px-4 py-3 text-sm text-gray-900 text-right">{formatCurrency(invoice.subtotal_ht)}</td>
                  <td className="px-4 py-3 text-sm text-gray-500 text-right">{formatCurrency(invoice.tva_amount)}</td>
                  <td className="px-4 py-3 text-sm font-medium text-gray-900 text-right">{formatCurrency(invoice.total_ttc)}</td>
                  <td className="px-4 py-3 text-center">
                    <span className={`inline-flex px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(invoice.status)}`}>
                      {t(`invoices.status${invoice.status.charAt(0).toUpperCase() + invoice.status.slice(1).replace('_', '')}`)}
                    </span>
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex items-center justify-center gap-2">
                      <button
                        className="p-1 text-gray-400 hover:text-emerald-600 transition-colors"
                        title={t('invoices.download')}
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                      </button>
                      {invoice.status === 'rejected' && (
                        <button
                          onClick={() => handleRetrySubmission(invoice.id)}
                          className="p-1 text-gray-400 hover:text-yellow-600 transition-colors"
                          title={t('invoices.retry')}
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                          </svg>
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {filteredInvoices.length === 0 && (
          <div className="p-8 text-center text-gray-500">
            {t('invoices.noInvoices')}
          </div>
        )}
      </div>
    </div>
  );

  const renderConfiguration = () => (
    <div className="space-y-6">
      {/* Current Status */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900">{t('config.dgiStatus')}</h3>
          {config?.is_active ? (
            <span className="flex items-center gap-2 px-3 py-1 bg-emerald-100 text-emerald-700 rounded-full text-sm">
              <span className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
              {t('config.connected')}
            </span>
          ) : (
            <span className="flex items-center gap-2 px-3 py-1 bg-red-100 text-red-700 rounded-full text-sm">
              <span className="w-2 h-2 bg-red-500 rounded-full" />
              {t('config.disconnected')}
            </span>
          )}
        </div>

        {config && (
          <div className="grid md:grid-cols-3 gap-4">
            <div>
              <div className="text-sm text-gray-500">{t('config.taxpayerId')}</div>
              <div className="font-medium text-gray-900">{config.taxpayer_id}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">{t('config.establishmentId')}</div>
              <div className="font-medium text-gray-900">{config.establishment_id}</div>
            </div>
            <div>
              <div className="text-sm text-gray-500">{t('config.environment')}</div>
              <div className="font-medium text-gray-900">
                {config.is_production ? t('config.production') : t('config.sandbox')}
              </div>
            </div>
          </div>
        )}

        {config?.last_sync_at && (
          <div className="mt-4 pt-4 border-t border-gray-100 text-sm text-gray-500">
            {t('config.lastSync')}: {formatDateTime(config.last_sync_at)}
          </div>
        )}
      </div>

      {/* Configuration Form */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="font-semibold text-gray-900 mb-6">{t('config.dgiConfiguration')}</h3>

        <div className="space-y-4">
          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('config.taxpayerId')} (NCC)
              </label>
              <input
                type="text"
                value={configForm.taxpayer_id}
                onChange={(e) => setConfigForm(prev => ({ ...prev, taxpayer_id: e.target.value }))}
                className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                placeholder="CI1234567890"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('config.establishmentId')}
              </label>
              <input
                type="text"
                value={configForm.establishment_id}
                onChange={(e) => setConfigForm(prev => ({ ...prev, establishment_id: e.target.value }))}
                className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                placeholder="ETB001"
              />
            </div>
          </div>

          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('config.apiKey')}
              </label>
              <input
                type="password"
                value={configForm.api_key}
                onChange={(e) => setConfigForm(prev => ({ ...prev, api_key: e.target.value }))}
                className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                placeholder="••••••••••••••••"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {t('config.apiSecret')}
              </label>
              <input
                type="password"
                value={configForm.api_secret}
                onChange={(e) => setConfigForm(prev => ({ ...prev, api_secret: e.target.value }))}
                className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                placeholder="••••••••••••••••"
              />
            </div>
          </div>

          <div className="flex items-center gap-3">
            <input
              type="checkbox"
              id="is_production"
              checked={configForm.is_production}
              onChange={(e) => setConfigForm(prev => ({ ...prev, is_production: e.target.checked }))}
              className="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
            />
            <label htmlFor="is_production" className="text-sm text-gray-700">
              {t('config.useProduction')}
            </label>
          </div>

          {configForm.is_production && (
            <div className="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
              <div className="flex items-start gap-3">
                <svg className="w-5 h-5 text-yellow-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
                <div>
                  <div className="font-medium text-yellow-800">{t('config.productionWarning')}</div>
                  <div className="text-sm text-yellow-700 mt-1">{t('config.productionWarningDesc')}</div>
                </div>
              </div>
            </div>
          )}

          <div className="flex justify-end gap-3 pt-4">
            <button
              onClick={() => loadData()}
              className="px-4 py-2 border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              {t('config.testConnection')}
            </button>
            <button
              onClick={handleSaveConfig}
              disabled={savingConfig}
              className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors"
            >
              {savingConfig ? t('config.saving') : t('config.save')}
            </button>
          </div>
        </div>
      </div>

      {/* DGI Info */}
      <div className="bg-blue-50 border border-blue-200 rounded-xl p-6">
        <h3 className="font-semibold text-blue-900 mb-2">{t('config.aboutDGI')}</h3>
        <p className="text-sm text-blue-800 mb-4">{t('config.aboutDGIDesc')}</p>
        <div className="space-y-2 text-sm text-blue-700">
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            {t('config.feature1')}
          </div>
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            {t('config.feature2')}
          </div>
          <div className="flex items-center gap-2">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
            {t('config.feature3')}
          </div>
        </div>
      </div>
    </div>
  );

  const renderReports = () => (
    <div className="space-y-6">
      {/* Monthly Summary Cards */}
      <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h3 className="font-semibold text-gray-900 mb-4">{t('reports.monthlyOverview')}</h3>
        <div className="space-y-4">
          {monthlyReports.map((report, idx) => (
            <div key={idx} className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <div className="font-medium text-gray-900">{report.month} {report.year}</div>
                <div className="text-sm text-gray-500">
                  {report.validated_invoices}/{report.total_invoices} {t('reports.invoicesValidated')}
                </div>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-500">{t('reports.totalTTC')}</div>
                <div className="font-bold text-gray-900">{formatCurrency(report.total_ttc)}</div>
              </div>
              <div className="text-right">
                <div className="text-sm text-gray-500">{t('reports.tvaCollected')}</div>
                <div className="font-medium text-emerald-600">{formatCurrency(report.total_tva)}</div>
              </div>
              <button className="px-4 py-2 text-emerald-600 hover:bg-emerald-50 rounded-lg transition-colors">
                {t('reports.download')}
              </button>
            </div>
          ))}
        </div>
      </div>

      {/* Tax Summary */}
      <div className="grid lg:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-900 mb-4">{t('reports.taxSummary')}</h3>
          <div className="space-y-4">
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">{t('reports.totalHT')}</span>
              <span className="font-medium text-gray-900">
                {formatCurrency(monthlyReports.reduce((sum, r) => sum + r.total_ht, 0))}
              </span>
            </div>
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-gray-600">{t('reports.totalTVA')} (18%)</span>
              <span className="font-medium text-emerald-600">
                {formatCurrency(monthlyReports.reduce((sum, r) => sum + r.total_tva, 0))}
              </span>
            </div>
            <div className="flex justify-between items-center py-2">
              <span className="text-gray-900 font-medium">{t('reports.totalTTC')}</span>
              <span className="font-bold text-gray-900 text-lg">
                {formatCurrency(monthlyReports.reduce((sum, r) => sum + r.total_ttc, 0))}
              </span>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-900 mb-4">{t('reports.exportReports')}</h3>
          <div className="space-y-3">
            <button className="w-full flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-red-100 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-red-600" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z" />
                  </svg>
                </div>
                <div className="text-left">
                  <div className="font-medium text-gray-900">{t('reports.dgiReport')}</div>
                  <div className="text-sm text-gray-500">{t('reports.dgiReportDesc')}</div>
                </div>
              </div>
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
            <button className="w-full flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8l-6-6z" />
                  </svg>
                </div>
                <div className="text-left">
                  <div className="font-medium text-gray-900">{t('reports.excelExport')}</div>
                  <div className="text-sm text-gray-500">{t('reports.excelExportDesc')}</div>
                </div>
              </div>
              <svg className="w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
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
      case 'invoices':
        return renderInvoices();
      case 'configuration':
        return renderConfiguration();
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
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center">
              <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
            </div>
            <div>
              <h1 className="text-2xl font-bold text-gray-900">{t('title')}</h1>
              <p className="text-gray-500">{t('subtitle')}</p>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          {tabs.map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
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
