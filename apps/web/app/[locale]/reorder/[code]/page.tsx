'use client';

import { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { useTranslations } from 'next-intl';
import Link from 'next/link';
import { useLocale } from 'next-intl';

interface ProductInfo {
  id: string;
  name: string;
  description: string;
  price: number;
  image_url: string;
  business_name: string;
  business_phone: string;
  business_address: string;
  min_quantity: number;
  max_quantity: number;
  default_quantity: number;
}

type OrderStep = 'product' | 'customer' | 'payment' | 'confirmation';
type PaymentMethod = 'wave' | 'orange_money' | 'mtn_momo' | 'cash';

interface CustomerInfo {
  name: string;
  phone: string;
  address: string;
  notes: string;
}

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('fr-FR', { style: 'decimal' }).format(value) + ' XOF';
}

export default function ReorderPage() {
  const params = useParams();
  const code = params.code as string;
  const t = useTranslations('reorder');
  const locale = useLocale();

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [product, setProduct] = useState<ProductInfo | null>(null);

  // Order state
  const [step, setStep] = useState<OrderStep>('product');
  const [quantity, setQuantity] = useState(1);
  const [customerInfo, setCustomerInfo] = useState<CustomerInfo>({
    name: '',
    phone: '',
    address: '',
    notes: '',
  });
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod>('wave');
  const [submitting, setSubmitting] = useState(false);
  const [orderNumber, setOrderNumber] = useState<string | null>(null);

  useEffect(() => {
    loadProduct();
  }, [code]);

  const loadProduct = async () => {
    setLoading(true);
    setError(null);
    try {
      await new Promise(resolve => setTimeout(resolve, 500));

      // Mock product data - in real app, fetch from API
      if (code === 'invalid') {
        throw new Error('Product not found');
      }

      setProduct({
        id: '1',
        name: 'Kédjenou de Poulet',
        description: 'Le plat traditionnel ivoirien - poulet mijoté aux légumes dans une canari',
        price: 5000,
        image_url: '/images/kedjenou.jpg',
        business_name: 'Chez Maman Adjoua',
        business_phone: '+225 07 12 34 56 78',
        business_address: 'Cocody, Abidjan',
        min_quantity: 1,
        max_quantity: 10,
        default_quantity: 1,
      });

      setQuantity(1);
    } catch (err) {
      setError(t('errors.productNotFound'));
    } finally {
      setLoading(false);
    }
  };

  const handleQuantityChange = (delta: number) => {
    if (!product) return;
    const newQuantity = quantity + delta;
    if (newQuantity >= product.min_quantity && newQuantity <= product.max_quantity) {
      setQuantity(newQuantity);
    }
  };

  const handleCustomerInfoChange = (field: keyof CustomerInfo, value: string) => {
    setCustomerInfo(prev => ({ ...prev, [field]: value }));
  };

  const validateCustomerInfo = (): boolean => {
    return customerInfo.name.trim().length >= 2 &&
           customerInfo.phone.trim().length >= 8 &&
           customerInfo.address.trim().length >= 5;
  };

  const handleSubmitOrder = async () => {
    if (!product) return;

    setSubmitting(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1500));

      // Mock order creation
      const mockOrderNumber = `ORD-${Date.now().toString().slice(-6)}`;
      setOrderNumber(mockOrderNumber);
      setStep('confirmation');
    } catch (err) {
      setError(t('errors.orderFailed'));
    } finally {
      setSubmitting(false);
    }
  };

  const totalAmount = product ? product.price * quantity : 0;

  // Loading state
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-teal-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-500">{t('loading')}</p>
        </div>
      </div>
    );
  }

  // Error state
  if (error || !product) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-teal-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
          <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <svg className="w-8 h-8 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-xl font-bold text-gray-900 mb-2">{t('errors.title')}</h2>
          <p className="text-gray-500 mb-6">{error || t('errors.productNotFound')}</p>
          <button
            onClick={loadProduct}
            className="px-6 py-3 bg-emerald-600 text-white rounded-xl font-medium hover:bg-emerald-700 transition-colors"
          >
            {t('errors.retry')}
          </button>
        </div>
      </div>
    );
  }

  // Confirmation step
  if (step === 'confirmation' && orderNumber) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-teal-50 flex items-center justify-center p-4">
        <div className="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full text-center">
          <div className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-10 h-10 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">{t('confirmation.title')}</h2>
          <p className="text-gray-500 mb-6">{t('confirmation.subtitle')}</p>

          <div className="bg-gray-50 rounded-xl p-4 mb-6">
            <div className="text-sm text-gray-500 mb-1">{t('confirmation.orderNumber')}</div>
            <div className="text-2xl font-bold text-emerald-600">{orderNumber}</div>
          </div>

          <div className="space-y-3 text-left mb-6">
            <div className="flex justify-between">
              <span className="text-gray-500">{t('confirmation.product')}</span>
              <span className="font-medium">{product.name} x{quantity}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">{t('confirmation.total')}</span>
              <span className="font-bold text-emerald-600">{formatCurrency(totalAmount)}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-gray-500">{t('confirmation.payment')}</span>
              <span className="font-medium">{t(`payment.methods.${paymentMethod}`)}</span>
            </div>
          </div>

          <div className="bg-blue-50 rounded-xl p-4 mb-6 text-left">
            <div className="flex items-start gap-3">
              <svg className="w-5 h-5 text-blue-600 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div className="text-sm text-blue-800">
                <p className="font-medium mb-1">{t('confirmation.nextSteps')}</p>
                <p>{t('confirmation.nextStepsDesc')}</p>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <a
              href={`tel:${product.business_phone}`}
              className="block w-full py-3 bg-emerald-600 text-white rounded-xl font-medium hover:bg-emerald-700 transition-colors"
            >
              {t('confirmation.callBusiness')}
            </a>
            <Link
              href={`/${locale}`}
              className="block w-full py-3 border border-gray-200 text-gray-700 rounded-xl font-medium hover:bg-gray-50 transition-colors"
            >
              {t('confirmation.backHome')}
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-teal-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-100">
        <div className="max-w-lg mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="font-bold text-emerald-600">BIZ360</h1>
              <p className="text-xs text-gray-500">{product.business_name}</p>
            </div>
            {step !== 'product' && (
              <button
                onClick={() => {
                  if (step === 'customer') setStep('product');
                  else if (step === 'payment') setStep('customer');
                }}
                className="text-gray-500 hover:text-gray-700"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Progress Steps */}
      <div className="max-w-lg mx-auto px-4 py-4">
        <div className="flex items-center justify-between">
          {['product', 'customer', 'payment'].map((s, idx) => (
            <div key={s} className="flex items-center">
              <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                step === s ? 'bg-emerald-600 text-white' :
                ['product', 'customer', 'payment'].indexOf(step) > idx ? 'bg-emerald-100 text-emerald-700' :
                'bg-gray-200 text-gray-500'
              }`}>
                {idx + 1}
              </div>
              {idx < 2 && (
                <div className={`w-16 sm:w-24 h-1 mx-2 ${
                  ['product', 'customer', 'payment'].indexOf(step) > idx ? 'bg-emerald-500' : 'bg-gray-200'
                }`} />
              )}
            </div>
          ))}
        </div>
        <div className="flex justify-between mt-2 text-xs text-gray-500">
          <span>{t('steps.product')}</span>
          <span>{t('steps.customer')}</span>
          <span>{t('steps.payment')}</span>
        </div>
      </div>

      <div className="max-w-lg mx-auto px-4 pb-8">
        {/* Product Step */}
        {step === 'product' && (
          <div className="bg-white rounded-2xl shadow-xl overflow-hidden">
            {/* Product Image Placeholder */}
            <div className="h-48 bg-gradient-to-br from-emerald-100 to-teal-100 flex items-center justify-center">
              <div className="text-6xl">🍽️</div>
            </div>

            <div className="p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-2">{product.name}</h2>
              <p className="text-gray-500 mb-4">{product.description}</p>
              <div className="text-3xl font-bold text-emerald-600 mb-6">{formatCurrency(product.price)}</div>

              {/* Quantity Selector */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">{t('product.quantity')}</label>
                <div className="flex items-center gap-4">
                  <button
                    onClick={() => handleQuantityChange(-1)}
                    disabled={quantity <= product.min_quantity}
                    className="w-12 h-12 rounded-xl border border-gray-200 flex items-center justify-center text-gray-600 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                    </svg>
                  </button>
                  <div className="flex-1 text-center">
                    <span className="text-3xl font-bold text-gray-900">{quantity}</span>
                  </div>
                  <button
                    onClick={() => handleQuantityChange(1)}
                    disabled={quantity >= product.max_quantity}
                    className="w-12 h-12 rounded-xl border border-gray-200 flex items-center justify-center text-gray-600 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Total */}
              <div className="flex justify-between items-center py-4 border-t border-gray-100 mb-6">
                <span className="text-gray-600">{t('product.total')}</span>
                <span className="text-2xl font-bold text-emerald-600">{formatCurrency(totalAmount)}</span>
              </div>

              <button
                onClick={() => setStep('customer')}
                className="w-full py-4 bg-emerald-600 text-white rounded-xl font-semibold hover:bg-emerald-700 transition-colors"
              >
                {t('product.continue')}
              </button>

              {/* Business Info */}
              <div className="mt-6 pt-6 border-t border-gray-100">
                <div className="text-sm text-gray-500 mb-2">{t('product.soldBy')}</div>
                <div className="font-medium text-gray-900">{product.business_name}</div>
                <div className="text-sm text-gray-500">{product.business_address}</div>
              </div>
            </div>
          </div>
        )}

        {/* Customer Step */}
        {step === 'customer' && (
          <div className="bg-white rounded-2xl shadow-xl p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-2">{t('customer.title')}</h2>
            <p className="text-gray-500 mb-6">{t('customer.subtitle')}</p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('customer.name')} *</label>
                <input
                  type="text"
                  value={customerInfo.name}
                  onChange={(e) => handleCustomerInfoChange('name', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  placeholder={t('customer.namePlaceholder')}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('customer.phone')} *</label>
                <input
                  type="tel"
                  value={customerInfo.phone}
                  onChange={(e) => handleCustomerInfoChange('phone', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  placeholder="+225 07 00 00 00 00"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('customer.address')} *</label>
                <input
                  type="text"
                  value={customerInfo.address}
                  onChange={(e) => handleCustomerInfoChange('address', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  placeholder={t('customer.addressPlaceholder')}
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">{t('customer.notes')}</label>
                <textarea
                  value={customerInfo.notes}
                  onChange={(e) => handleCustomerInfoChange('notes', e.target.value)}
                  rows={3}
                  className="w-full px-4 py-3 border border-gray-200 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  placeholder={t('customer.notesPlaceholder')}
                />
              </div>
            </div>

            {/* Order Summary */}
            <div className="mt-6 p-4 bg-gray-50 rounded-xl">
              <div className="flex justify-between text-sm mb-2">
                <span className="text-gray-500">{product.name} x{quantity}</span>
                <span className="font-medium">{formatCurrency(totalAmount)}</span>
              </div>
              <div className="flex justify-between font-bold text-lg">
                <span>{t('customer.total')}</span>
                <span className="text-emerald-600">{formatCurrency(totalAmount)}</span>
              </div>
            </div>

            <button
              onClick={() => setStep('payment')}
              disabled={!validateCustomerInfo()}
              className="w-full mt-6 py-4 bg-emerald-600 text-white rounded-xl font-semibold hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {t('customer.continue')}
            </button>
          </div>
        )}

        {/* Payment Step */}
        {step === 'payment' && (
          <div className="bg-white rounded-2xl shadow-xl p-6">
            <h2 className="text-xl font-bold text-gray-900 mb-2">{t('payment.title')}</h2>
            <p className="text-gray-500 mb-6">{t('payment.subtitle')}</p>

            <div className="space-y-3 mb-6">
              {(['wave', 'orange_money', 'mtn_momo', 'cash'] as PaymentMethod[]).map((method) => (
                <button
                  key={method}
                  onClick={() => setPaymentMethod(method)}
                  className={`w-full flex items-center gap-4 p-4 border-2 rounded-xl transition-colors ${
                    paymentMethod === method
                      ? 'border-emerald-500 bg-emerald-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${
                    method === 'wave' ? 'bg-blue-100' :
                    method === 'orange_money' ? 'bg-orange-100' :
                    method === 'mtn_momo' ? 'bg-yellow-100' :
                    'bg-gray-100'
                  }`}>
                    {method === 'wave' && <span className="text-2xl">🌊</span>}
                    {method === 'orange_money' && <span className="text-2xl">🟠</span>}
                    {method === 'mtn_momo' && <span className="text-2xl">🟡</span>}
                    {method === 'cash' && <span className="text-2xl">💵</span>}
                  </div>
                  <div className="flex-1 text-left">
                    <div className="font-medium text-gray-900">{t(`payment.methods.${method}`)}</div>
                    <div className="text-sm text-gray-500">{t(`payment.methodsDesc.${method}`)}</div>
                  </div>
                  {paymentMethod === method && (
                    <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  )}
                </button>
              ))}
            </div>

            {/* Order Summary */}
            <div className="p-4 bg-gray-50 rounded-xl mb-6">
              <h3 className="font-medium text-gray-900 mb-3">{t('payment.summary')}</h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-500">{product.name} x{quantity}</span>
                  <span>{formatCurrency(totalAmount)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-500">{t('payment.delivery')}</span>
                  <span className="text-emerald-600">{t('payment.free')}</span>
                </div>
              </div>
              <div className="flex justify-between font-bold text-lg mt-3 pt-3 border-t border-gray-200">
                <span>{t('payment.total')}</span>
                <span className="text-emerald-600">{formatCurrency(totalAmount)}</span>
              </div>
            </div>

            {/* Customer Info Summary */}
            <div className="p-4 bg-gray-50 rounded-xl mb-6">
              <h3 className="font-medium text-gray-900 mb-2">{t('payment.deliveryTo')}</h3>
              <p className="text-gray-700">{customerInfo.name}</p>
              <p className="text-gray-500 text-sm">{customerInfo.phone}</p>
              <p className="text-gray-500 text-sm">{customerInfo.address}</p>
            </div>

            <button
              onClick={handleSubmitOrder}
              disabled={submitting}
              className="w-full py-4 bg-emerald-600 text-white rounded-xl font-semibold hover:bg-emerald-700 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
            >
              {submitting ? (
                <>
                  <div className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  {t('payment.processing')}
                </>
              ) : (
                <>
                  {t('payment.placeOrder')} - {formatCurrency(totalAmount)}
                </>
              )}
            </button>

            <p className="mt-4 text-center text-xs text-gray-500">
              {t('payment.terms')}
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
