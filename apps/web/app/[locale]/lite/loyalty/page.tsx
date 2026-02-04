'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { api } from '@/lib/api/client';

interface LoyaltyTier {
  id: string;
  name: string;
  min_points: number;
  min_lifetime_points: number;
  points_multiplier: number;
  discount_percentage: number;
  color: string;
  customers_count: number;
}

interface LoyaltyProgram {
  id: string;
  is_active: boolean;
  points_per_currency: number;
  currency_unit: number;
  signup_bonus: number;
  referral_bonus_referrer: number;
  referral_bonus_referee: number;
  birthday_bonus: number;
  review_bonus: number;
  points_expire: boolean;
  expiry_months: number;
  min_points_redeem: number;
  points_value_currency: number;
  tiers: LoyaltyTier[];
}

interface Customer {
  id: string;
  name: string;
  email: string;
  phone: string;
  loyalty_points: number;
  lifetime_points: number;
  tier_name: string | null;
  tier_color: string | null;
  total_visits: number;
  total_spent: number;
  last_visit_at: string | null;
  created_at: string;
}

interface CRMSummary {
  total_customers: number;
  active_customers: number;
  new_customers_month: number;
  total_points_issued: number;
  total_points_redeemed: number;
  total_rewards_redeemed: number;
  avg_customer_value: number;
  customers_by_tier: { tier: string; color: string; count: number }[];
}

interface LoyaltyReward {
  id: string;
  name: string;
  description: string;
  points_required: number;
  reward_type: string;
  is_active: boolean;
  is_available: boolean;
  redemption_count: number;
}

type TabType = 'overview' | 'customers' | 'rewards' | 'settings';

export default function LoyaltyPage() {
  const t = useTranslations('lite.loyalty');
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [summary, setSummary] = useState<CRMSummary | null>(null);
  const [program, setProgram] = useState<LoyaltyProgram | null>(null);
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [rewards, setRewards] = useState<LoyaltyReward[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');

  // Modals
  const [showCustomerModal, setShowCustomerModal] = useState(false);
  const [showRewardModal, setShowRewardModal] = useState(false);
  const [selectedCustomer, setSelectedCustomer] = useState<Customer | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const [summaryData, programData, customersData, rewardsData] = await Promise.all([
        api.get<CRMSummary>('/api/v1/crm/summary/'),
        api.get<LoyaltyProgram>('/api/v1/crm/program/'),
        api.get<Customer[]>('/api/v1/crm/customers/'),
        api.get<LoyaltyReward[]>('/api/v1/crm/rewards/'),
      ]);
      setSummary(summaryData);
      setProgram(programData);
      setCustomers(customersData);
      setRewards(rewardsData);
    } catch (error) {
      console.error('Failed to load CRM data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const searchCustomers = async () => {
    if (!searchQuery.trim()) {
      loadData();
      return;
    }
    try {
      const data = await api.get<Customer[]>(`/api/v1/crm/customers/?search=${encodeURIComponent(searchQuery)}`);
      setCustomers(data);
    } catch (error) {
      console.error('Search failed:', error);
    }
  };

  const updateProgram = async (updates: Partial<LoyaltyProgram>) => {
    try {
      const updated = await api.patch<LoyaltyProgram>('/api/v1/crm/program/', updates);
      setProgram(updated);
    } catch (error) {
      console.error('Failed to update program:', error);
    }
  };

  const tabs = [
    { id: 'overview' as TabType, label: t('tabs.overview'), icon: '📊' },
    { id: 'customers' as TabType, label: t('tabs.customers'), icon: '👥' },
    { id: 'rewards' as TabType, label: t('tabs.rewards'), icon: '🎁' },
    { id: 'settings' as TabType, label: t('tabs.settings'), icon: '⚙️' },
  ];

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{t('title')}</h1>
        <p className="text-gray-500 mt-1">{t('subtitle')}</p>
      </div>

      {/* Tabs */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 mb-6">
        <div className="flex border-b border-gray-200">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
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

      {/* Overview Tab */}
      {activeTab === 'overview' && summary && (
        <div className="space-y-6">
          {/* Summary Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
              <p className="text-sm text-gray-500">{t('totalCustomers')}</p>
              <p className="text-2xl font-bold text-gray-900">{summary.total_customers}</p>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
              <p className="text-sm text-gray-500">{t('activeCustomers')}</p>
              <p className="text-2xl font-bold text-emerald-600">{summary.active_customers}</p>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
              <p className="text-sm text-gray-500">{t('newThisMonth')}</p>
              <p className="text-2xl font-bold text-blue-600">+{summary.new_customers_month}</p>
            </div>
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
              <p className="text-sm text-gray-500">{t('avgCustomerValue')}</p>
              <p className="text-2xl font-bold text-gray-900">
                {Number(summary.avg_customer_value).toLocaleString()} XOF
              </p>
            </div>
          </div>

          {/* Points Stats */}
          <div className="grid md:grid-cols-2 gap-6">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="font-semibold text-gray-900 mb-4">{t('pointsOverview')}</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-500">{t('totalIssued')}</span>
                  <span className="font-semibold text-emerald-600">
                    {summary.total_points_issued.toLocaleString()} pts
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-500">{t('totalRedeemed')}</span>
                  <span className="font-semibold text-orange-600">
                    {summary.total_points_redeemed.toLocaleString()} pts
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-500">{t('rewardsRedeemed')}</span>
                  <span className="font-semibold text-purple-600">
                    {summary.total_rewards_redeemed}
                  </span>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
              <h3 className="font-semibold text-gray-900 mb-4">{t('customersByTier')}</h3>
              <div className="space-y-3">
                {summary.customers_by_tier.map((tier, index) => (
                  <div key={index} className="flex items-center gap-3">
                    <div
                      className="w-3 h-3 rounded-full"
                      style={{ backgroundColor: tier.color }}
                    />
                    <span className="flex-1 text-gray-700">{tier.tier}</span>
                    <span className="font-semibold">{tier.count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Customers Tab */}
      {activeTab === 'customers' && (
        <div className="space-y-4">
          {/* Search and Add */}
          <div className="flex gap-4">
            <div className="flex-1 relative">
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && searchCustomers()}
                placeholder={t('searchCustomers')}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg pl-10"
              />
              <svg className="w-5 h-5 text-gray-400 absolute left-3 top-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            </div>
            <button
              onClick={() => setShowCustomerModal(true)}
              className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700"
            >
              {t('addCustomer')}
            </button>
          </div>

          {/* Customers List */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 overflow-hidden">
            {customers.length === 0 ? (
              <div className="p-12 text-center">
                <div className="text-4xl mb-4">👥</div>
                <h3 className="text-lg font-medium text-gray-900 mb-2">{t('noCustomers')}</h3>
                <p className="text-gray-500">{t('noCustomersDesc')}</p>
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">{t('customer')}</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">{t('contact')}</th>
                      <th className="px-4 py-3 text-left text-sm font-medium text-gray-500">{t('tier')}</th>
                      <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">{t('points')}</th>
                      <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">{t('visits')}</th>
                      <th className="px-4 py-3 text-right text-sm font-medium text-gray-500">{t('totalSpent')}</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {customers.map((customer) => (
                      <tr
                        key={customer.id}
                        className="hover:bg-gray-50 cursor-pointer"
                        onClick={() => setSelectedCustomer(customer)}
                      >
                        <td className="px-4 py-3">
                          <div className="flex items-center gap-3">
                            <div className="w-8 h-8 bg-emerald-100 rounded-full flex items-center justify-center">
                              <span className="text-emerald-700 font-semibold text-sm">
                                {customer.name.charAt(0).toUpperCase()}
                              </span>
                            </div>
                            <span className="font-medium text-gray-900">{customer.name}</span>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-sm text-gray-500">
                          {customer.email || customer.phone || '-'}
                        </td>
                        <td className="px-4 py-3">
                          {customer.tier_name ? (
                            <span
                              className="px-2 py-1 text-xs font-medium rounded-full"
                              style={{
                                backgroundColor: `${customer.tier_color || '#6B7280'}20`,
                                color: customer.tier_color || '#6B7280',
                              }}
                            >
                              {customer.tier_name}
                            </span>
                          ) : (
                            <span className="text-gray-400">-</span>
                          )}
                        </td>
                        <td className="px-4 py-3 text-right font-medium text-emerald-600">
                          {customer.loyalty_points.toLocaleString()}
                        </td>
                        <td className="px-4 py-3 text-right text-gray-700">
                          {customer.total_visits}
                        </td>
                        <td className="px-4 py-3 text-right text-gray-700">
                          {Number(customer.total_spent).toLocaleString()} XOF
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Rewards Tab */}
      {activeTab === 'rewards' && (
        <div className="space-y-4">
          <div className="flex justify-end">
            <button
              onClick={() => setShowRewardModal(true)}
              className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700"
            >
              {t('addReward')}
            </button>
          </div>

          {rewards.length === 0 ? (
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
              <div className="text-4xl mb-4">🎁</div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">{t('noRewards')}</h3>
              <p className="text-gray-500">{t('noRewardsDesc')}</p>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {rewards.map((reward) => (
                <div
                  key={reward.id}
                  className="bg-white rounded-xl shadow-sm border border-gray-200 p-4"
                >
                  <div className="flex justify-between items-start mb-3">
                    <h3 className="font-semibold text-gray-900">{reward.name}</h3>
                    <span
                      className={`px-2 py-1 text-xs font-medium rounded-full ${
                        reward.is_active
                          ? 'bg-green-100 text-green-700'
                          : 'bg-gray-100 text-gray-500'
                      }`}
                    >
                      {reward.is_active ? t('active') : t('inactive')}
                    </span>
                  </div>
                  {reward.description && (
                    <p className="text-sm text-gray-500 mb-3">{reward.description}</p>
                  )}
                  <div className="flex justify-between items-center">
                    <span className="text-lg font-bold text-emerald-600">
                      {reward.points_required.toLocaleString()} pts
                    </span>
                    <span className="text-sm text-gray-500">
                      {reward.redemption_count} {t('redeemed')}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Settings Tab */}
      {activeTab === 'settings' && program && (
        <div className="space-y-6">
          {/* Program Toggle */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="font-semibold text-gray-900">{t('loyaltyProgram')}</h3>
                <p className="text-sm text-gray-500">{t('enableDisableProgram')}</p>
              </div>
              <label className="relative inline-flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={program.is_active}
                  onChange={(e) => updateProgram({ is_active: e.target.checked })}
                  className="sr-only peer"
                />
                <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-emerald-600" />
              </label>
            </div>
          </div>

          {/* Points Earning Rules */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-4">{t('pointsEarning')}</h3>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('pointsPerUnit')}
                </label>
                <div className="flex gap-2">
                  <input
                    type="number"
                    value={program.points_per_currency}
                    onChange={(e) => updateProgram({ points_per_currency: Number(e.target.value) })}
                    className="w-24 px-3 py-2 border border-gray-300 rounded-lg"
                  />
                  <span className="flex items-center text-gray-500">
                    {t('pointsPer')} {program.currency_unit} XOF
                  </span>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('signupBonus')}
                </label>
                <input
                  type="number"
                  value={program.signup_bonus}
                  onChange={(e) => updateProgram({ signup_bonus: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('referralBonusReferrer')}
                </label>
                <input
                  type="number"
                  value={program.referral_bonus_referrer}
                  onChange={(e) => updateProgram({ referral_bonus_referrer: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('referralBonusReferee')}
                </label>
                <input
                  type="number"
                  value={program.referral_bonus_referee}
                  onChange={(e) => updateProgram({ referral_bonus_referee: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('birthdayBonus')}
                </label>
                <input
                  type="number"
                  value={program.birthday_bonus}
                  onChange={(e) => updateProgram({ birthday_bonus: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('reviewBonus')}
                </label>
                <input
                  type="number"
                  value={program.review_bonus}
                  onChange={(e) => updateProgram({ review_bonus: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
            </div>
          </div>

          {/* Points Redemption */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <h3 className="font-semibold text-gray-900 mb-4">{t('pointsRedemption')}</h3>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('minPointsRedeem')}
                </label>
                <input
                  type="number"
                  value={program.min_points_redeem}
                  onChange={(e) => updateProgram({ min_points_redeem: Number(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  {t('pointsValue')}
                </label>
                <div className="flex gap-2">
                  <input
                    type="number"
                    value={program.points_value_currency}
                    onChange={(e) => updateProgram({ points_value_currency: Number(e.target.value) })}
                    className="w-24 px-3 py-2 border border-gray-300 rounded-lg"
                  />
                  <span className="flex items-center text-gray-500">XOF {t('perPoint')}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Tiers */}
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
            <div className="flex justify-between items-center mb-4">
              <h3 className="font-semibold text-gray-900">{t('loyaltyTiers')}</h3>
              <button className="text-emerald-600 hover:text-emerald-700 text-sm font-medium">
                + {t('addTier')}
              </button>
            </div>
            {program.tiers.length === 0 ? (
              <p className="text-gray-500 text-sm">{t('noTiersDesc')}</p>
            ) : (
              <div className="space-y-3">
                {program.tiers.map((tier) => (
                  <div
                    key={tier.id}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className="w-4 h-4 rounded-full"
                        style={{ backgroundColor: tier.color }}
                      />
                      <span className="font-medium">{tier.name}</span>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-gray-500">
                      <span>{tier.min_points.toLocaleString()}+ pts</span>
                      <span>{tier.points_multiplier}x</span>
                      <span>{tier.customers_count} {t('customers')}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Customer Modal - simplified for now */}
      {showCustomerModal && (
        <CustomerModal
          onClose={() => setShowCustomerModal(false)}
          onSave={() => {
            setShowCustomerModal(false);
            loadData();
          }}
        />
      )}

      {/* Reward Modal - simplified for now */}
      {showRewardModal && (
        <RewardModal
          onClose={() => setShowRewardModal(false)}
          onSave={() => {
            setShowRewardModal(false);
            loadData();
          }}
        />
      )}
    </div>
  );
}

interface ModalProps {
  onClose: () => void;
  onSave: () => void;
}

function CustomerModal({ onClose, onSave }: ModalProps) {
  const t = useTranslations('lite.loyalty');
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setIsSubmitting(true);
    try {
      await api.post('/api/v1/crm/customers/', { name, email, phone });
      onSave();
    } catch (error) {
      console.error('Failed to create customer:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-lg max-w-md w-full">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">{t('addCustomer')}</h2>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('customerName')} *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('email')}
            </label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('phone')}
            </label>
            <input
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              {t('cancel')}
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !name.trim()}
              className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50"
            >
              {isSubmitting ? t('saving') : t('save')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}

function RewardModal({ onClose, onSave }: ModalProps) {
  const t = useTranslations('lite.loyalty');
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [pointsRequired, setPointsRequired] = useState(100);
  const [rewardType, setRewardType] = useState('free_item');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) return;

    setIsSubmitting(true);
    try {
      await api.post('/api/v1/crm/rewards/', {
        name,
        description,
        points_required: pointsRequired,
        reward_type: rewardType,
      });
      onSave();
    } catch (error) {
      console.error('Failed to create reward:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-lg max-w-md w-full">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">{t('addReward')}</h2>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('rewardName')} *
            </label>
            <input
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder={t('rewardNamePlaceholder')}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('description')}
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={2}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('pointsRequired')} *
            </label>
            <input
              type="number"
              value={pointsRequired}
              onChange={(e) => setPointsRequired(Number(e.target.value))}
              min={1}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              required
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('rewardType')}
            </label>
            <select
              value={rewardType}
              onChange={(e) => setRewardType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            >
              <option value="free_item">{t('rewardTypes.freeItem')}</option>
              <option value="discount_amount">{t('rewardTypes.discountAmount')}</option>
              <option value="discount_percent">{t('rewardTypes.discountPercent')}</option>
              <option value="experience">{t('rewardTypes.experience')}</option>
            </select>
          </div>
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              {t('cancel')}
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !name.trim()}
              className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50"
            >
              {isSubmitting ? t('saving') : t('save')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
