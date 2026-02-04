'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';

interface CreditScore {
  score: number;
  score_band: string;
  revenue_score: number;
  payment_score: number;
  order_score: number;
  tenure_score: number;
  activity_score: number;
  avg_monthly_revenue: number;
  revenue_growth_rate: number;
  avg_monthly_orders: number;
  platform_tenure_days: number;
  payment_success_rate: number;
  active_days_ratio: number;
  last_calculated: string;
}

interface FinancePartner {
  id: string;
  name: string;
  slug: string;
  partner_type: string;
  description: string;
  logo: string | null;
  min_loan_amount: number;
  max_loan_amount: number;
  min_interest_rate: number;
  max_interest_rate: number;
  min_term_months: number;
  max_term_months: number;
  min_credit_score: number;
  min_platform_tenure_days: number;
  min_monthly_revenue: number;
  is_featured: boolean;
}

interface LoanProduct {
  id: string;
  partner: string;
  partner_name: string;
  name: string;
  product_type: string;
  description: string;
  min_amount: number;
  max_amount: number;
  interest_rate: number;
  term_months: number;
  repayment_frequency: string;
  auto_deduct: boolean;
  auto_deduct_percentage: number;
  min_credit_score: number;
}

interface Loan {
  id: string;
  loan_number: string;
  partner_name: string;
  principal: number;
  outstanding_balance: number;
  amount_repaid: number;
  next_payment_date: string;
  next_payment_amount: number;
  status: string;
  progress_percentage: number;
  auto_deduct_enabled: boolean;
}

interface LoanApplication {
  id: string;
  application_number: string;
  partner_name: string;
  amount_requested: number;
  term_months: number;
  purpose: string;
  status: string;
  submitted_at: string | null;
  created_at: string;
}

export default function FinancingPage() {
  const t = useTranslations('lite.financing');
  const [activeTab, setActiveTab] = useState<'overview' | 'apply' | 'loans' | 'calculator' | 'settings'>('overview');

  // Mock data for demo
  const [creditScore] = useState<CreditScore>({
    score: 685,
    score_band: 'good',
    revenue_score: 72,
    payment_score: 85,
    order_score: 68,
    tenure_score: 60,
    activity_score: 75,
    avg_monthly_revenue: 1500000,
    revenue_growth_rate: 5.5,
    avg_monthly_orders: 450,
    platform_tenure_days: 180,
    payment_success_rate: 98.5,
    active_days_ratio: 92.0,
    last_calculated: new Date().toISOString(),
  });

  const [partners] = useState<FinancePartner[]>([
    {
      id: '1',
      name: 'Ivoire MicroFinance',
      slug: 'ivoire-microfinance',
      partner_type: 'microfinance',
      description: 'Premier partenaire de microfinance pour les entreprises en Côte d\'Ivoire',
      logo: null,
      min_loan_amount: 100000,
      max_loan_amount: 5000000,
      min_interest_rate: 8,
      max_interest_rate: 18,
      min_term_months: 3,
      max_term_months: 18,
      min_credit_score: 500,
      min_platform_tenure_days: 60,
      min_monthly_revenue: 500000,
      is_featured: true,
    },
    {
      id: '2',
      name: 'AfriBank Business',
      slug: 'afribank-business',
      partner_type: 'bank',
      description: 'Solutions de financement bancaire pour les PME',
      logo: null,
      min_loan_amount: 500000,
      max_loan_amount: 10000000,
      min_interest_rate: 10,
      max_interest_rate: 22,
      min_term_months: 6,
      max_term_months: 24,
      min_credit_score: 600,
      min_platform_tenure_days: 90,
      min_monthly_revenue: 1000000,
      is_featured: false,
    },
  ]);

  const [loans] = useState<Loan[]>([
    {
      id: '1',
      loan_number: 'LN-20260101-0001',
      partner_name: 'Ivoire MicroFinance',
      principal: 1000000,
      outstanding_balance: 650000,
      amount_repaid: 350000,
      next_payment_date: '2026-02-15',
      next_payment_amount: 95000,
      status: 'active',
      progress_percentage: 35,
      auto_deduct_enabled: true,
    },
  ]);

  const [applications] = useState<LoanApplication[]>([
    {
      id: '1',
      application_number: 'LA-20260125-0001',
      partner_name: 'AfriBank Business',
      amount_requested: 2000000,
      term_months: 12,
      purpose: 'equipment',
      status: 'under_review',
      submitted_at: '2026-01-25T10:30:00Z',
      created_at: '2026-01-25T10:00:00Z',
    },
  ]);

  // Calculator state
  const [calcAmount, setCalcAmount] = useState(1000000);
  const [calcRate, setCalcRate] = useState(15);
  const [calcTerm, setCalcTerm] = useState(12);
  const [calcResults, setCalcResults] = useState<{
    monthlyPayment: number;
    totalInterest: number;
    totalRepayment: number;
  } | null>(null);

  // Settings state
  const [financingEnabled, setFinancingEnabled] = useState(true);
  const [autoDeductConsent, setAutoDeductConsent] = useState(true);
  const [maxAutoDeduct, setMaxAutoDeduct] = useState(15);
  const [notifyPaymentDue, setNotifyPaymentDue] = useState(true);
  const [notifyPaymentProcessed, setNotifyPaymentProcessed] = useState(true);
  const [notifyNewOffers, setNotifyNewOffers] = useState(true);

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('fr-FR').format(amount) + ' XOF';
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('fr-FR', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    });
  };

  const calculateLoan = () => {
    const monthlyRate = calcRate / 100 / 12;
    const monthlyPayment = calcAmount * (monthlyRate * Math.pow(1 + monthlyRate, calcTerm)) / (Math.pow(1 + monthlyRate, calcTerm) - 1);
    const totalRepayment = monthlyPayment * calcTerm;
    const totalInterest = totalRepayment - calcAmount;

    setCalcResults({
      monthlyPayment: Math.round(monthlyPayment),
      totalInterest: Math.round(totalInterest),
      totalRepayment: Math.round(totalRepayment),
    });
  };

  const getScoreBandColor = (band: string) => {
    switch (band) {
      case 'excellent': return 'text-emerald-600 bg-emerald-50';
      case 'very_good': return 'text-green-600 bg-green-50';
      case 'good': return 'text-blue-600 bg-blue-50';
      case 'fair': return 'text-yellow-600 bg-yellow-50';
      case 'poor': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'paid_off': return 'bg-blue-100 text-blue-800';
      case 'defaulted': return 'bg-red-100 text-red-800';
      case 'draft': return 'bg-gray-100 text-gray-800';
      case 'submitted': return 'bg-blue-100 text-blue-800';
      case 'under_review': return 'bg-yellow-100 text-yellow-800';
      case 'approved': return 'bg-green-100 text-green-800';
      case 'rejected': return 'bg-red-100 text-red-800';
      case 'disbursed': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const tabs = [
    { id: 'overview', label: t('tabs.overview') },
    { id: 'apply', label: t('tabs.apply') },
    { id: 'loans', label: t('tabs.loans') },
    { id: 'calculator', label: t('tabs.calculator') },
    { id: 'settings', label: t('tabs.settings') },
  ] as const;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{t('title')}</h1>
        <p className="text-gray-500 mt-1">{t('subtitle')}</p>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8 overflow-x-auto">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`whitespace-nowrap py-3 px-1 border-b-2 font-medium text-sm transition-colors ${
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
          {/* Dashboard Stats */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* Credit Score Card */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">{t('dashboard.creditScore')}</p>
                  <p className="text-3xl font-bold text-gray-900 mt-1">{creditScore.score}</p>
                  <span className={`inline-block mt-2 px-2 py-1 text-xs font-medium rounded-full ${getScoreBandColor(creditScore.score_band)}`}>
                    {t(`creditScore.band.${creditScore.score_band}`)}
                  </span>
                </div>
                <div className="w-12 h-12 bg-emerald-100 rounded-full flex items-center justify-center">
                  <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
              </div>
            </div>

            {/* Available Credit */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">{t('dashboard.availableCredit')}</p>
                  <p className="text-2xl font-bold text-gray-900 mt-1">{formatCurrency(creditScore.avg_monthly_revenue * 3)}</p>
                </div>
                <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
                  <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
              </div>
            </div>

            {/* Active Loans */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">{t('dashboard.activeLoans')}</p>
                  <p className="text-3xl font-bold text-gray-900 mt-1">{loans.length}</p>
                  <p className="text-sm text-gray-500 mt-2">
                    {t('dashboard.totalOutstanding')}: {formatCurrency(loans.reduce((sum, l) => sum + l.outstanding_balance, 0))}
                  </p>
                </div>
                <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center">
                  <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                </div>
              </div>
            </div>

            {/* Next Payment */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">{t('dashboard.nextPayment')}</p>
                  {loans.length > 0 ? (
                    <>
                      <p className="text-2xl font-bold text-gray-900 mt-1">{formatCurrency(loans[0].next_payment_amount)}</p>
                      <p className="text-sm text-gray-500 mt-2">{formatDate(loans[0].next_payment_date)}</p>
                    </>
                  ) : (
                    <p className="text-lg text-gray-400 mt-1">-</p>
                  )}
                </div>
                <div className="w-12 h-12 bg-orange-100 rounded-full flex items-center justify-center">
                  <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                  </svg>
                </div>
              </div>
            </div>
          </div>

          {/* Credit Score Details */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('creditScore.title')}</h2>

            {/* Score Components */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
              {[
                { key: 'revenue', value: creditScore.revenue_score },
                { key: 'payment', value: creditScore.payment_score },
                { key: 'orders', value: creditScore.order_score },
                { key: 'tenure', value: creditScore.tenure_score },
                { key: 'activity', value: creditScore.activity_score },
              ].map(({ key, value }) => (
                <div key={key} className="text-center">
                  <div className="relative pt-1">
                    <div className="overflow-hidden h-2 text-xs flex rounded-full bg-gray-100">
                      <div
                        style={{ width: `${value}%` }}
                        className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-emerald-500"
                      ></div>
                    </div>
                  </div>
                  <p className="text-sm text-gray-500 mt-2">{t(`creditScore.components.${key}`)}</p>
                  <p className="text-lg font-semibold text-gray-900">{value}/100</p>
                </div>
              ))}
            </div>

            {/* Metrics */}
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4 pt-4 border-t border-gray-100">
              <div>
                <p className="text-sm text-gray-500">{t('creditScore.metrics.avgMonthlyRevenue')}</p>
                <p className="text-lg font-semibold text-gray-900">{formatCurrency(creditScore.avg_monthly_revenue)}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">{t('creditScore.metrics.platformTenure')}</p>
                <p className="text-lg font-semibold text-gray-900">{creditScore.platform_tenure_days} {t('creditScore.days')}</p>
              </div>
              <div>
                <p className="text-sm text-gray-500">{t('creditScore.metrics.paymentSuccessRate')}</p>
                <p className="text-lg font-semibold text-gray-900">{creditScore.payment_success_rate}%</p>
              </div>
            </div>

            <p className="text-xs text-gray-400 mt-4">
              {t('creditScore.lastUpdated')}: {formatDate(creditScore.last_calculated)}
            </p>
          </div>

          {/* Finance Partners */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('partners.title')}</h2>

            <div className="grid gap-4 md:grid-cols-2">
              {partners.map((partner) => (
                <div key={partner.id} className="border border-gray-200 rounded-lg p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-12 h-12 bg-gray-100 rounded-lg flex items-center justify-center">
                        <span className="text-lg font-bold text-gray-600">{partner.name.charAt(0)}</span>
                      </div>
                      <div>
                        <h3 className="font-semibold text-gray-900">{partner.name}</h3>
                        <p className="text-sm text-gray-500">{partner.partner_type}</p>
                      </div>
                    </div>
                    {partner.is_featured && (
                      <span className="px-2 py-1 text-xs font-medium bg-emerald-100 text-emerald-800 rounded-full">
                        {t('partners.featured')}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-600 mt-3">{partner.description}</p>
                  <div className="grid grid-cols-2 gap-2 mt-4 text-sm">
                    <div>
                      <span className="text-gray-500">{t('partners.interestRate')}:</span>
                      <span className="ml-1 font-medium">{partner.min_interest_rate}% - {partner.max_interest_rate}%</span>
                    </div>
                    <div>
                      <span className="text-gray-500">{t('partners.terms')}:</span>
                      <span className="ml-1 font-medium">{partner.min_term_months} - {partner.max_term_months} {t('partners.months')}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">{t('partners.minLoan')}:</span>
                      <span className="ml-1 font-medium">{formatCurrency(partner.min_loan_amount)}</span>
                    </div>
                    <div>
                      <span className="text-gray-500">{t('partners.maxLoan')}:</span>
                      <span className="ml-1 font-medium">{formatCurrency(partner.max_loan_amount)}</span>
                    </div>
                  </div>
                  <button
                    onClick={() => setActiveTab('apply')}
                    className="mt-4 w-full py-2 px-4 bg-emerald-500 text-white text-sm font-medium rounded-lg hover:bg-emerald-600 transition-colors"
                  >
                    {t('partners.apply')}
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Apply Tab */}
      {activeTab === 'apply' && (
        <div className="space-y-6">
          {/* Pending Applications */}
          {applications.length > 0 && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('applications.title')}</h2>
              <div className="space-y-4">
                {applications.map((app) => (
                  <div key={app.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                    <div>
                      <p className="font-medium text-gray-900">{app.application_number}</p>
                      <p className="text-sm text-gray-500">{app.partner_name} - {formatCurrency(app.amount_requested)}</p>
                      {app.submitted_at && (
                        <p className="text-xs text-gray-400 mt-1">{t('applications.submitted')}: {formatDate(app.submitted_at)}</p>
                      )}
                    </div>
                    <span className={`px-3 py-1 text-sm font-medium rounded-full ${getStatusColor(app.status)}`}>
                      {t(`applications.status.${app.status}`)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* New Application Form */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('application.title')}</h2>

            <form className="space-y-6">
              {/* Partner Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('application.selectPartner')}
                </label>
                <select className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500">
                  <option value="">-- {t('application.selectPartner')} --</option>
                  {partners.map((partner) => (
                    <option key={partner.id} value={partner.id}>{partner.name}</option>
                  ))}
                </select>
              </div>

              {/* Amount */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('application.amountRequested')}
                </label>
                <input
                  type="number"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  placeholder="1000000"
                />
              </div>

              {/* Term */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('application.termMonths')}
                </label>
                <select className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500">
                  {[3, 6, 9, 12, 18, 24].map((months) => (
                    <option key={months} value={months}>{months} {t('partners.months')}</option>
                  ))}
                </select>
              </div>

              {/* Purpose */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('application.purpose')}
                </label>
                <select className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500">
                  <option value="working_capital">{t('application.purposes.working_capital')}</option>
                  <option value="equipment">{t('application.purposes.equipment')}</option>
                  <option value="expansion">{t('application.purposes.expansion')}</option>
                  <option value="inventory">{t('application.purposes.inventory')}</option>
                  <option value="renovation">{t('application.purposes.renovation')}</option>
                  <option value="marketing">{t('application.purposes.marketing')}</option>
                  <option value="other">{t('application.purposes.other')}</option>
                </select>
              </div>

              {/* Purpose Details */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('application.purposeDetails')}
                </label>
                <textarea
                  rows={4}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                  placeholder={t('application.purposeDetailsPlaceholder')}
                ></textarea>
              </div>

              {/* Terms */}
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="terms"
                  className="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
                />
                <label htmlFor="terms" className="text-sm text-gray-700">
                  {t('application.termsAccept')}
                </label>
              </div>

              <button
                type="submit"
                className="w-full py-3 px-4 bg-emerald-500 text-white font-medium rounded-lg hover:bg-emerald-600 transition-colors"
              >
                {t('application.submit')}
              </button>
            </form>
          </div>
        </div>
      )}

      {/* Loans Tab */}
      {activeTab === 'loans' && (
        <div className="space-y-6">
          {loans.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-12 text-center">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">{t('loans.noLoans')}</h3>
              <p className="text-gray-500">{t('loans.noLoansDesc')}</p>
            </div>
          ) : (
            <div className="space-y-4">
              {loans.map((loan) => (
                <div key={loan.id} className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                  <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <h3 className="font-semibold text-gray-900">{loan.loan_number}</h3>
                        <span className={`px-2 py-0.5 text-xs font-medium rounded-full ${getStatusColor(loan.status)}`}>
                          {t(`loans.status.${loan.status}`)}
                        </span>
                      </div>
                      <p className="text-sm text-gray-500 mt-1">{loan.partner_name}</p>
                    </div>
                    <div className="flex items-center gap-3">
                      <div className="text-right">
                        <p className="text-sm text-gray-500">{t('loans.outstanding')}</p>
                        <p className="text-lg font-semibold text-gray-900">{formatCurrency(loan.outstanding_balance)}</p>
                      </div>
                    </div>
                  </div>

                  {/* Progress Bar */}
                  <div className="mt-4">
                    <div className="flex justify-between text-sm mb-1">
                      <span className="text-gray-500">{t('loans.progress')}</span>
                      <span className="font-medium text-gray-900">{loan.progress_percentage}%</span>
                    </div>
                    <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
                      <div
                        className="h-full bg-emerald-500 rounded-full transition-all"
                        style={{ width: `${loan.progress_percentage}%` }}
                      ></div>
                    </div>
                    <div className="flex justify-between text-xs text-gray-400 mt-1">
                      <span>{t('loans.paid')}: {formatCurrency(loan.amount_repaid)}</span>
                      <span>{t('loans.principal')}: {formatCurrency(loan.principal)}</span>
                    </div>
                  </div>

                  {/* Next Payment */}
                  <div className="flex flex-col md:flex-row md:items-center justify-between mt-4 pt-4 border-t border-gray-100 gap-4">
                    <div>
                      <p className="text-sm text-gray-500">{t('loans.nextPayment')}</p>
                      <p className="font-semibold text-gray-900">{formatCurrency(loan.next_payment_amount)}</p>
                      <p className="text-xs text-gray-400">{t('loans.dueDate')}: {formatDate(loan.next_payment_date)}</p>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-gray-500">{t('loans.autoDeduct')}:</span>
                      <span className={`px-2 py-1 text-xs font-medium rounded ${loan.auto_deduct_enabled ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-600'}`}>
                        {loan.auto_deduct_enabled ? t('loans.enabled') : t('loans.disabled')}
                      </span>
                    </div>
                    <button className="px-4 py-2 bg-emerald-500 text-white text-sm font-medium rounded-lg hover:bg-emerald-600 transition-colors">
                      {t('loans.makePayment')}
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Calculator Tab */}
      {activeTab === 'calculator' && (
        <div className="grid md:grid-cols-2 gap-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('calculator.title')}</h2>
            <p className="text-gray-500 mb-6">{t('calculator.subtitle')}</p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('calculator.loanAmount')} (XOF)
                </label>
                <input
                  type="number"
                  value={calcAmount}
                  onChange={(e) => setCalcAmount(Number(e.target.value))}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('calculator.interestRate')} (%)
                </label>
                <input
                  type="number"
                  value={calcRate}
                  onChange={(e) => setCalcRate(Number(e.target.value))}
                  step="0.5"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  {t('calculator.loanTerm')}
                </label>
                <select
                  value={calcTerm}
                  onChange={(e) => setCalcTerm(Number(e.target.value))}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
                >
                  {[3, 6, 9, 12, 18, 24].map((months) => (
                    <option key={months} value={months}>{months} {t('partners.months')}</option>
                  ))}
                </select>
              </div>

              <button
                onClick={calculateLoan}
                className="w-full py-3 px-4 bg-emerald-500 text-white font-medium rounded-lg hover:bg-emerald-600 transition-colors"
              >
                {t('calculator.calculate')}
              </button>
            </div>
          </div>

          {calcResults && (
            <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">{t('calculator.results.title')}</h2>

              <div className="space-y-4">
                <div className="p-4 bg-emerald-50 rounded-lg">
                  <p className="text-sm text-emerald-600">{t('calculator.results.monthlyPayment')}</p>
                  <p className="text-3xl font-bold text-emerald-700">{formatCurrency(calcResults.monthlyPayment)}</p>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-500">{t('calculator.results.totalInterest')}</p>
                    <p className="text-xl font-semibold text-gray-900">{formatCurrency(calcResults.totalInterest)}</p>
                  </div>
                  <div className="p-4 bg-gray-50 rounded-lg">
                    <p className="text-sm text-gray-500">{t('calculator.results.totalRepayment')}</p>
                    <p className="text-xl font-semibold text-gray-900">{formatCurrency(calcResults.totalRepayment)}</p>
                  </div>
                </div>

                {/* Repayment Schedule Preview */}
                <div className="mt-4">
                  <h3 className="text-sm font-medium text-gray-700 mb-2">{t('calculator.results.schedule')}</h3>
                  <div className="border border-gray-200 rounded-lg overflow-hidden">
                    <table className="w-full text-sm">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-3 py-2 text-left text-gray-500">{t('calculator.schedule.month')}</th>
                          <th className="px-3 py-2 text-right text-gray-500">{t('calculator.schedule.payment')}</th>
                          <th className="px-3 py-2 text-right text-gray-500">{t('calculator.schedule.balance')}</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {Array.from({ length: Math.min(calcTerm, 6) }).map((_, i) => {
                          const monthlyRate = calcRate / 100 / 12;
                          let balance = calcAmount;
                          for (let j = 0; j <= i; j++) {
                            const interest = balance * monthlyRate;
                            const principal = calcResults.monthlyPayment - interest;
                            balance -= principal;
                          }
                          return (
                            <tr key={i}>
                              <td className="px-3 py-2 text-gray-900">{i + 1}</td>
                              <td className="px-3 py-2 text-right text-gray-900">{formatCurrency(calcResults.monthlyPayment)}</td>
                              <td className="px-3 py-2 text-right text-gray-900">{formatCurrency(Math.max(0, Math.round(balance)))}</td>
                            </tr>
                          );
                        })}
                        {calcTerm > 6 && (
                          <tr>
                            <td colSpan={3} className="px-3 py-2 text-center text-gray-500">
                              ... {calcTerm - 6} more months
                            </td>
                          </tr>
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Settings Tab */}
      {activeTab === 'settings' && (
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-6">{t('settings.title')}</h2>

          <div className="space-y-6">
            {/* Enable Financing */}
            <div className="flex items-center justify-between">
              <div>
                <p className="font-medium text-gray-900">{t('settings.enableFinancing')}</p>
                <p className="text-sm text-gray-500">{t('settings.enableFinancingDesc')}</p>
              </div>
              <button
                onClick={() => setFinancingEnabled(!financingEnabled)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  financingEnabled ? 'bg-emerald-500' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    financingEnabled ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* Auto-Deduct Consent */}
            <div className="flex items-center justify-between pt-4 border-t border-gray-100">
              <div>
                <p className="font-medium text-gray-900">{t('settings.autoDeductConsent')}</p>
                <p className="text-sm text-gray-500">{t('settings.autoDeductConsentDesc')}</p>
              </div>
              <button
                onClick={() => setAutoDeductConsent(!autoDeductConsent)}
                className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                  autoDeductConsent ? 'bg-emerald-500' : 'bg-gray-200'
                }`}
              >
                <span
                  className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                    autoDeductConsent ? 'translate-x-6' : 'translate-x-1'
                  }`}
                />
              </button>
            </div>

            {/* Max Auto-Deduct */}
            <div className="pt-4 border-t border-gray-100">
              <label className="block font-medium text-gray-900 mb-1">{t('settings.maxAutoDeduct')}</label>
              <p className="text-sm text-gray-500 mb-3">{t('settings.maxAutoDeductDesc')}</p>
              <div className="flex items-center gap-4">
                <input
                  type="range"
                  min="5"
                  max="30"
                  value={maxAutoDeduct}
                  onChange={(e) => setMaxAutoDeduct(Number(e.target.value))}
                  className="flex-1"
                />
                <span className="text-lg font-semibold text-gray-900 w-16 text-right">{maxAutoDeduct}%</span>
              </div>
            </div>

            {/* Notifications */}
            <div className="pt-4 border-t border-gray-100">
              <p className="font-medium text-gray-900 mb-4">{t('settings.notifications')}</p>

              <div className="space-y-3">
                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={notifyPaymentDue}
                    onChange={(e) => setNotifyPaymentDue(e.target.checked)}
                    className="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
                  />
                  <span className="text-gray-700">{t('settings.notifyPaymentDue')}</span>
                </label>

                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={notifyPaymentProcessed}
                    onChange={(e) => setNotifyPaymentProcessed(e.target.checked)}
                    className="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
                  />
                  <span className="text-gray-700">{t('settings.notifyPaymentProcessed')}</span>
                </label>

                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={notifyNewOffers}
                    onChange={(e) => setNotifyNewOffers(e.target.checked)}
                    className="w-4 h-4 text-emerald-600 border-gray-300 rounded focus:ring-emerald-500"
                  />
                  <span className="text-gray-700">{t('settings.notifyNewOffers')}</span>
                </label>
              </div>
            </div>

            {/* Save Button */}
            <div className="pt-4 border-t border-gray-100">
              <button className="px-6 py-2 bg-emerald-500 text-white font-medium rounded-lg hover:bg-emerald-600 transition-colors">
                {t('settings.save')}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
