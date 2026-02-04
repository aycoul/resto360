'use client';

import { useState, useEffect, ReactNode } from 'react';
import { useTranslations } from 'next-intl';
import { useLocale } from 'next-intl';

type Tab = 'qrcodes' | 'orders' | 'analytics';

interface ReorderQRCode {
  id: string;
  product_id: string;
  product_name: string;
  product_price: number;
  code: string;
  default_quantity: number;
  is_active: boolean;
  scan_count: number;
  order_count: number;
  created_at: string;
}

interface ReorderOrder {
  id: string;
  qr_code_id: string;
  product_name: string;
  quantity: number;
  total_amount: number;
  customer_name: string;
  customer_phone: string;
  status: 'pending' | 'confirmed' | 'preparing' | 'ready' | 'completed' | 'cancelled';
  created_at: string;
}

interface ReorderStats {
  total_qr_codes: number;
  total_scans: number;
  total_orders: number;
  conversion_rate: number;
  top_products: Array<{ name: string; orders: number }>;
  orders_by_day: Array<{ date: string; orders: number }>;
}

const TAB_ICONS: Record<Tab, ReactNode> = {
  qrcodes: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
    </svg>
  ),
  orders: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
    </svg>
  ),
  analytics: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
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
    hour: '2-digit',
    minute: '2-digit',
  });
}

function getStatusColor(status: ReorderOrder['status']): string {
  switch (status) {
    case 'completed':
      return 'bg-emerald-100 text-emerald-700';
    case 'ready':
      return 'bg-blue-100 text-blue-700';
    case 'preparing':
      return 'bg-yellow-100 text-yellow-700';
    case 'confirmed':
      return 'bg-purple-100 text-purple-700';
    case 'pending':
      return 'bg-gray-100 text-gray-700';
    case 'cancelled':
      return 'bg-red-100 text-red-700';
    default:
      return 'bg-gray-100 text-gray-700';
  }
}

export default function ReorderPage() {
  const t = useTranslations('lite.reorder');
  const locale = useLocale();
  const [activeTab, setActiveTab] = useState<Tab>('qrcodes');
  const [loading, setLoading] = useState(true);

  // Data state
  const [qrCodes, setQRCodes] = useState<ReorderQRCode[]>([]);
  const [orders, setOrders] = useState<ReorderOrder[]>([]);
  const [stats, setStats] = useState<ReorderStats | null>(null);

  // Create QR modal
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedProductId, setSelectedProductId] = useState('');
  const [defaultQuantity, setDefaultQuantity] = useState(1);
  const [creating, setCreating] = useState(false);

  // Mock products for selection
  const [products] = useState([
    { id: '1', name: 'Kédjenou de Poulet', price: 5000 },
    { id: '2', name: 'Poulet Braisé', price: 6000 },
    { id: '3', name: 'Garba', price: 2500 },
    { id: '4', name: 'Sauce Graine', price: 4500 },
    { id: '5', name: 'Alloco (portion)', price: 1500 },
  ]);

  const tabs: Tab[] = ['qrcodes', 'orders', 'analytics'];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 500));

      // Mock QR codes
      setQRCodes([
        {
          id: '1',
          product_id: '1',
          product_name: 'Kédjenou de Poulet',
          product_price: 5000,
          code: 'abc123-def456',
          default_quantity: 1,
          is_active: true,
          scan_count: 145,
          order_count: 42,
          created_at: '2026-01-15T10:00:00Z',
        },
        {
          id: '2',
          product_id: '2',
          product_name: 'Poulet Braisé',
          product_price: 6000,
          code: 'ghi789-jkl012',
          default_quantity: 2,
          is_active: true,
          scan_count: 89,
          order_count: 28,
          created_at: '2026-01-20T14:30:00Z',
        },
        {
          id: '3',
          product_id: '5',
          product_name: 'Alloco (portion)',
          product_price: 1500,
          code: 'mno345-pqr678',
          default_quantity: 1,
          is_active: false,
          scan_count: 23,
          order_count: 8,
          created_at: '2026-01-25T09:00:00Z',
        },
      ]);

      // Mock orders
      setOrders([
        {
          id: '1',
          qr_code_id: '1',
          product_name: 'Kédjenou de Poulet',
          quantity: 2,
          total_amount: 10000,
          customer_name: 'Kouadio Yao',
          customer_phone: '+225 07 12 34 56',
          status: 'completed',
          created_at: '2026-02-04T14:30:00Z',
        },
        {
          id: '2',
          qr_code_id: '1',
          product_name: 'Kédjenou de Poulet',
          quantity: 1,
          total_amount: 5000,
          customer_name: 'Aya Konan',
          customer_phone: '+225 05 98 76 54',
          status: 'ready',
          created_at: '2026-02-04T13:15:00Z',
        },
        {
          id: '3',
          qr_code_id: '2',
          product_name: 'Poulet Braisé',
          quantity: 3,
          total_amount: 18000,
          customer_name: 'Jean-Pierre Kouassi',
          customer_phone: '+225 01 23 45 67',
          status: 'preparing',
          created_at: '2026-02-04T12:45:00Z',
        },
        {
          id: '4',
          qr_code_id: '2',
          product_name: 'Poulet Braisé',
          quantity: 2,
          total_amount: 12000,
          customer_name: 'Adjoua Tra',
          customer_phone: '+225 07 65 43 21',
          status: 'pending',
          created_at: '2026-02-04T12:00:00Z',
        },
      ]);

      // Mock stats
      setStats({
        total_qr_codes: 3,
        total_scans: 257,
        total_orders: 78,
        conversion_rate: 30.4,
        top_products: [
          { name: 'Kédjenou de Poulet', orders: 42 },
          { name: 'Poulet Braisé', orders: 28 },
          { name: 'Alloco (portion)', orders: 8 },
        ],
        orders_by_day: [
          { date: '2026-01-29', orders: 8 },
          { date: '2026-01-30', orders: 12 },
          { date: '2026-01-31', orders: 15 },
          { date: '2026-02-01', orders: 10 },
          { date: '2026-02-02', orders: 18 },
          { date: '2026-02-03', orders: 11 },
          { date: '2026-02-04', orders: 4 },
        ],
      });

    } catch (error) {
      console.error('Failed to load reorder data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateQR = async () => {
    if (!selectedProductId) return;

    setCreating(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));

      const product = products.find(p => p.id === selectedProductId);
      if (!product) return;

      const newQR: ReorderQRCode = {
        id: String(Date.now()),
        product_id: selectedProductId,
        product_name: product.name,
        product_price: product.price,
        code: `${Math.random().toString(36).substring(2, 8)}-${Math.random().toString(36).substring(2, 8)}`,
        default_quantity: defaultQuantity,
        is_active: true,
        scan_count: 0,
        order_count: 0,
        created_at: new Date().toISOString(),
      };

      setQRCodes(prev => [newQR, ...prev]);
      setShowCreateModal(false);
      setSelectedProductId('');
      setDefaultQuantity(1);
    } catch (error) {
      console.error('Failed to create QR code:', error);
    } finally {
      setCreating(false);
    }
  };

  const handleToggleQR = (qrId: string) => {
    setQRCodes(prev => prev.map(qr =>
      qr.id === qrId ? { ...qr, is_active: !qr.is_active } : qr
    ));
  };

  const handleUpdateOrderStatus = (orderId: string, newStatus: ReorderOrder['status']) => {
    setOrders(prev => prev.map(order =>
      order.id === orderId ? { ...order, status: newStatus } : order
    ));
  };

  const getReorderUrl = (code: string) => {
    return `${typeof window !== 'undefined' ? window.location.origin : ''}/${locale}/reorder/${code}`;
  };

  const handleCopyUrl = (code: string) => {
    navigator.clipboard.writeText(getReorderUrl(code));
    // You could add a toast notification here
  };

  const handlePrintQR = (qr: ReorderQRCode) => {
    // In a real app, this would open a print dialog with QR code
    alert(`${t('qrcodes.printQR')}: ${qr.product_name}`);
  };

  const renderQRCodes = () => (
    <div className="space-y-6">
      {/* Create QR Button */}
      <div className="flex justify-between items-center">
        <div>
          <h3 className="font-semibold text-gray-900">{t('qrcodes.title')}</h3>
          <p className="text-sm text-gray-500">{t('qrcodes.subtitle')}</p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          {t('qrcodes.createNew')}
        </button>
      </div>

      {/* QR Codes Grid */}
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {qrCodes.map((qr) => (
          <div key={qr.id} className={`bg-white rounded-xl p-6 shadow-sm border ${qr.is_active ? 'border-gray-100' : 'border-gray-200 opacity-60'}`}>
            <div className="flex items-start justify-between mb-4">
              <div>
                <h4 className="font-medium text-gray-900">{qr.product_name}</h4>
                <p className="text-sm text-gray-500">{formatCurrency(qr.product_price)}</p>
              </div>
              <button
                onClick={() => handleToggleQR(qr.id)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${qr.is_active ? 'bg-emerald-600' : 'bg-gray-200'}`}
              >
                <span className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${qr.is_active ? 'translate-x-6' : 'translate-x-1'}`} />
              </button>
            </div>

            {/* Mock QR Code Visual */}
            <div className="bg-gray-100 rounded-lg p-4 mb-4 flex items-center justify-center">
              <div className="w-24 h-24 bg-white p-2 rounded">
                <div className="w-full h-full grid grid-cols-5 gap-0.5">
                  {Array.from({ length: 25 }).map((_, i) => (
                    <div
                      key={i}
                      className={`aspect-square ${Math.random() > 0.5 ? 'bg-gray-900' : 'bg-white'}`}
                    />
                  ))}
                </div>
              </div>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-gray-900">{qr.scan_count}</div>
                <div className="text-xs text-gray-500">{t('qrcodes.scans')}</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-emerald-600">{qr.order_count}</div>
                <div className="text-xs text-gray-500">{t('qrcodes.orders')}</div>
              </div>
            </div>

            {/* Conversion Rate */}
            <div className="mb-4">
              <div className="flex justify-between text-sm mb-1">
                <span className="text-gray-500">{t('qrcodes.conversionRate')}</span>
                <span className="font-medium text-gray-900">
                  {qr.scan_count > 0 ? ((qr.order_count / qr.scan_count) * 100).toFixed(1) : 0}%
                </span>
              </div>
              <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-emerald-500 rounded-full"
                  style={{ width: `${qr.scan_count > 0 ? (qr.order_count / qr.scan_count) * 100 : 0}%` }}
                />
              </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2">
              <button
                onClick={() => handleCopyUrl(qr.code)}
                className="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                title={t('qrcodes.copyUrl')}
              >
                <svg className="w-4 h-4 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3" />
                </svg>
              </button>
              <button
                onClick={() => handlePrintQR(qr)}
                className="flex-1 px-3 py-2 text-sm border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                title={t('qrcodes.printQR')}
              >
                <svg className="w-4 h-4 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
                </svg>
              </button>
              <button
                className="flex-1 px-3 py-2 text-sm bg-emerald-50 text-emerald-700 rounded-lg hover:bg-emerald-100 transition-colors"
              >
                {t('qrcodes.download')}
              </button>
            </div>

            <div className="mt-3 text-xs text-gray-400 text-center">
              {t('qrcodes.created')}: {formatDate(qr.created_at)}
            </div>
          </div>
        ))}
      </div>

      {qrCodes.length === 0 && (
        <div className="bg-white rounded-xl p-12 text-center shadow-sm border border-gray-100">
          <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v1m6 11h2m-6 0h-2v4m0-11v3m0 0h.01M12 12h4.01M16 20h4M4 12h4m12 0h.01M5 8h2a1 1 0 001-1V5a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1zm12 0h2a1 1 0 001-1V5a1 1 0 00-1-1h-2a1 1 0 00-1 1v2a1 1 0 001 1zM5 20h2a1 1 0 001-1v-2a1 1 0 00-1-1H5a1 1 0 00-1 1v2a1 1 0 001 1z" />
            </svg>
          </div>
          <h3 className="font-medium text-gray-900 mb-2">{t('qrcodes.noQRCodes')}</h3>
          <p className="text-gray-500 mb-4">{t('qrcodes.noQRCodesDesc')}</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 transition-colors"
          >
            {t('qrcodes.createFirst')}
          </button>
        </div>
      )}

      {/* Create Modal */}
      {showCreateModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl p-6 max-w-md w-full">
            <h3 className="font-semibold text-gray-900 mb-4">{t('qrcodes.createTitle')}</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('qrcodes.selectProduct')}
                </label>
                <select
                  value={selectedProductId}
                  onChange={(e) => setSelectedProductId(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                >
                  <option value="">{t('qrcodes.selectProductPlaceholder')}</option>
                  {products.map((product) => (
                    <option key={product.id} value={product.id}>
                      {product.name} - {formatCurrency(product.price)}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('qrcodes.defaultQuantity')}
                </label>
                <input
                  type="number"
                  min="1"
                  max="100"
                  value={defaultQuantity}
                  onChange={(e) => setDefaultQuantity(parseInt(e.target.value) || 1)}
                  className="w-full px-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                />
              </div>
            </div>

            <div className="flex gap-3 mt-6">
              <button
                onClick={() => {
                  setShowCreateModal(false);
                  setSelectedProductId('');
                  setDefaultQuantity(1);
                }}
                className="flex-1 px-4 py-2 border border-gray-200 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
              >
                {t('qrcodes.cancel')}
              </button>
              <button
                onClick={handleCreateQR}
                disabled={!selectedProductId || creating}
                className="flex-1 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50 transition-colors"
              >
                {creating ? t('qrcodes.creating') : t('qrcodes.create')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );

  const renderOrders = () => (
    <div className="space-y-6">
      <div>
        <h3 className="font-semibold text-gray-900">{t('orders.title')}</h3>
        <p className="text-sm text-gray-500">{t('orders.subtitle')}</p>
      </div>

      {/* Orders List */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
        {orders.length > 0 ? (
          <div className="divide-y divide-gray-100">
            {orders.map((order) => (
              <div key={order.id} className="p-4 hover:bg-gray-50">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h4 className="font-medium text-gray-900">{order.product_name}</h4>
                      <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${getStatusColor(order.status)}`}>
                        {t(`orders.status${order.status.charAt(0).toUpperCase() + order.status.slice(1)}`)}
                      </span>
                    </div>
                    <div className="text-sm text-gray-500 space-y-1">
                      <div>{t('orders.quantity')}: {order.quantity} x {formatCurrency(order.total_amount / order.quantity)}</div>
                      <div>{t('orders.customer')}: {order.customer_name}</div>
                      <div>{t('orders.phone')}: {order.customer_phone}</div>
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-bold text-gray-900">{formatCurrency(order.total_amount)}</div>
                    <div className="text-xs text-gray-500 mt-1">{formatDateTime(order.created_at)}</div>
                  </div>
                </div>

                {/* Status Actions */}
                {order.status !== 'completed' && order.status !== 'cancelled' && (
                  <div className="mt-4 flex gap-2">
                    {order.status === 'pending' && (
                      <>
                        <button
                          onClick={() => handleUpdateOrderStatus(order.id, 'confirmed')}
                          className="px-3 py-1.5 text-sm bg-purple-100 text-purple-700 rounded-lg hover:bg-purple-200 transition-colors"
                        >
                          {t('orders.confirm')}
                        </button>
                        <button
                          onClick={() => handleUpdateOrderStatus(order.id, 'cancelled')}
                          className="px-3 py-1.5 text-sm text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                        >
                          {t('orders.cancel')}
                        </button>
                      </>
                    )}
                    {order.status === 'confirmed' && (
                      <button
                        onClick={() => handleUpdateOrderStatus(order.id, 'preparing')}
                        className="px-3 py-1.5 text-sm bg-yellow-100 text-yellow-700 rounded-lg hover:bg-yellow-200 transition-colors"
                      >
                        {t('orders.startPreparing')}
                      </button>
                    )}
                    {order.status === 'preparing' && (
                      <button
                        onClick={() => handleUpdateOrderStatus(order.id, 'ready')}
                        className="px-3 py-1.5 text-sm bg-blue-100 text-blue-700 rounded-lg hover:bg-blue-200 transition-colors"
                      >
                        {t('orders.markReady')}
                      </button>
                    )}
                    {order.status === 'ready' && (
                      <button
                        onClick={() => handleUpdateOrderStatus(order.id, 'completed')}
                        className="px-3 py-1.5 text-sm bg-emerald-100 text-emerald-700 rounded-lg hover:bg-emerald-200 transition-colors"
                      >
                        {t('orders.markCompleted')}
                      </button>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        ) : (
          <div className="p-12 text-center">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
            </div>
            <h3 className="font-medium text-gray-900 mb-2">{t('orders.noOrders')}</h3>
            <p className="text-gray-500">{t('orders.noOrdersDesc')}</p>
          </div>
        )}
      </div>
    </div>
  );

  const renderAnalytics = () => {
    if (!stats) return null;

    const maxOrders = Math.max(...stats.orders_by_day.map(d => d.orders));

    return (
      <div className="space-y-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <div className="text-sm text-gray-500">{t('analytics.totalQRCodes')}</div>
            <div className="text-2xl font-bold text-gray-900 mt-1">{stats.total_qr_codes}</div>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <div className="text-sm text-gray-500">{t('analytics.totalScans')}</div>
            <div className="text-2xl font-bold text-blue-600 mt-1">{stats.total_scans}</div>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <div className="text-sm text-gray-500">{t('analytics.totalOrders')}</div>
            <div className="text-2xl font-bold text-emerald-600 mt-1">{stats.total_orders}</div>
          </div>
          <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
            <div className="text-sm text-gray-500">{t('analytics.conversionRate')}</div>
            <div className="text-2xl font-bold text-purple-600 mt-1">{stats.conversion_rate}%</div>
          </div>
        </div>

        {/* Orders by Day Chart */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-900 mb-4">{t('analytics.ordersLast7Days')}</h3>
          <div className="flex items-end justify-between h-48 gap-2">
            {stats.orders_by_day.map((day, idx) => (
              <div key={idx} className="flex-1 flex flex-col items-center gap-2">
                <div className="text-sm font-medium text-gray-900">{day.orders}</div>
                <div
                  className="w-full bg-emerald-500 rounded-t transition-all hover:bg-emerald-600"
                  style={{ height: `${maxOrders > 0 ? (day.orders / maxOrders) * 100 : 0}%`, minHeight: '4px' }}
                />
                <span className="text-xs text-gray-500">
                  {new Date(day.date).toLocaleDateString('fr-FR', { weekday: 'short' })}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Top Products */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h3 className="font-semibold text-gray-900 mb-4">{t('analytics.topProducts')}</h3>
          <div className="space-y-4">
            {stats.top_products.map((product, idx) => (
              <div key={idx} className="flex items-center gap-4">
                <div className="w-8 h-8 rounded-full bg-emerald-100 text-emerald-700 flex items-center justify-center text-sm font-medium">
                  {idx + 1}
                </div>
                <div className="flex-1">
                  <div className="font-medium text-gray-900">{product.name}</div>
                  <div className="text-sm text-gray-500">{product.orders} {t('analytics.orders')}</div>
                </div>
                <div className="w-32">
                  <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-emerald-500 rounded-full"
                      style={{ width: `${(product.orders / stats.top_products[0].orders) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* How It Works */}
        <div className="bg-emerald-50 border border-emerald-200 rounded-xl p-6">
          <h3 className="font-semibold text-emerald-900 mb-4">{t('analytics.howItWorks')}</h3>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl">📦</span>
              </div>
              <h4 className="font-medium text-emerald-900">{t('analytics.step1Title')}</h4>
              <p className="text-sm text-emerald-700 mt-1">{t('analytics.step1Desc')}</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl">📱</span>
              </div>
              <h4 className="font-medium text-emerald-900">{t('analytics.step2Title')}</h4>
              <p className="text-sm text-emerald-700 mt-1">{t('analytics.step2Desc')}</p>
            </div>
            <div className="text-center">
              <div className="w-12 h-12 bg-white rounded-full flex items-center justify-center mx-auto mb-3">
                <span className="text-2xl">🎉</span>
              </div>
              <h4 className="font-medium text-emerald-900">{t('analytics.step3Title')}</h4>
              <p className="text-sm text-emerald-700 mt-1">{t('analytics.step3Desc')}</p>
            </div>
          </div>
        </div>
      </div>
    );
  };

  const renderContent = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600" />
        </div>
      );
    }

    switch (activeTab) {
      case 'qrcodes':
        return renderQRCodes();
      case 'orders':
        return renderOrders();
      case 'analytics':
        return renderAnalytics();
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
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
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
