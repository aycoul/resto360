'use client';

import { useState } from 'react';
import { useTranslations } from 'next-intl';
import { useLocale } from 'next-intl';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { setTokens } from '@/lib/api/client';

interface FormData {
  restaurant_name: string;
  phone: string;
  email: string;
  password: string;
  password_confirm: string;
}

interface FormErrors {
  restaurant_name?: string;
  phone?: string;
  email?: string;
  password?: string;
  password_confirm?: string;
  general?: string;
}

export default function RegisterPage() {
  const t = useTranslations('register');
  const locale = useLocale();
  const router = useRouter();

  const [formData, setFormData] = useState<FormData>({
    restaurant_name: '',
    phone: '',
    email: '',
    password: '',
    password_confirm: '',
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    if (!formData.restaurant_name.trim()) {
      newErrors.restaurant_name = t('errors.required');
    }

    if (!formData.phone.trim()) {
      newErrors.phone = t('errors.required');
    }

    if (!formData.email.trim()) {
      newErrors.email = t('errors.required');
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = t('errors.invalid_email');
    }

    if (!formData.password) {
      newErrors.password = t('errors.required');
    } else if (formData.password.length < 8) {
      newErrors.password = t('errors.password_min');
    }

    if (!formData.password_confirm) {
      newErrors.password_confirm = t('errors.required');
    } else if (formData.password !== formData.password_confirm) {
      newErrors.password_confirm = t('errors.password_mismatch');
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    // Clear error when user starts typing
    if (errors[name as keyof FormErrors]) {
      setErrors(prev => ({ ...prev, [name]: undefined }));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    setErrors({});

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
      const response = await fetch(`${apiUrl}/api/v1/auth/register/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          restaurant_name: formData.restaurant_name,
          phone: formData.phone,
          email: formData.email,
          password: formData.password,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        if (errorData.email) {
          setErrors({ email: errorData.email[0] || t('errors.email_exists') });
        } else if (errorData.phone) {
          setErrors({ phone: errorData.phone[0] || t('errors.phone_exists') });
        } else {
          setErrors({ general: errorData.detail || t('errors.general') });
        }
        return;
      }

      const data = await response.json();

      // Store tokens
      setTokens({
        access: data.tokens.access,
        refresh: data.tokens.refresh,
      });

      // Store restaurant info for onboarding
      if (typeof window !== 'undefined') {
        sessionStorage.setItem('onboarding_restaurant', JSON.stringify({
          id: data.restaurant.id,
          name: data.restaurant.name,
          slug: data.restaurant.slug,
        }));
      }

      // Redirect to onboarding
      router.push(`/${locale}/onboarding`);
    } catch {
      setErrors({ general: t('errors.network') });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-emerald-50 to-teal-50 px-4 py-12">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <Link href={`/${locale}`} className="inline-block">
            <h1 className="text-3xl font-bold text-emerald-600">RESTO360</h1>
          </Link>
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <h2 className="text-2xl font-bold text-gray-900 text-center mb-2">
            {t('title')}
          </h2>
          <p className="text-gray-500 text-center mb-8">
            {t('subtitle')}
          </p>

          {errors.general && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
              {errors.general}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            {/* Restaurant Name */}
            <div>
              <label htmlFor="restaurant_name" className="block text-sm font-medium text-gray-700 mb-1">
                {t('restaurant_name')}
              </label>
              <input
                type="text"
                id="restaurant_name"
                name="restaurant_name"
                value={formData.restaurant_name}
                onChange={handleChange}
                className={`w-full px-4 py-3 border rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors ${
                  errors.restaurant_name ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="Chez Maman"
              />
              {errors.restaurant_name && (
                <p className="mt-1 text-sm text-red-600">{errors.restaurant_name}</p>
              )}
            </div>

            {/* Phone */}
            <div>
              <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">
                {t('phone')}
              </label>
              <input
                type="tel"
                id="phone"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                className={`w-full px-4 py-3 border rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors ${
                  errors.phone ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="+225 07 00 00 00 00"
              />
              {errors.phone && (
                <p className="mt-1 text-sm text-red-600">{errors.phone}</p>
              )}
            </div>

            {/* Email */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                {t('email')}
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                className={`w-full px-4 py-3 border rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors ${
                  errors.email ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="contact@restaurant.ci"
              />
              {errors.email && (
                <p className="mt-1 text-sm text-red-600">{errors.email}</p>
              )}
            </div>

            {/* Password */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                {t('password')}
              </label>
              <input
                type="password"
                id="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                className={`w-full px-4 py-3 border rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors ${
                  errors.password ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="********"
              />
              {errors.password && (
                <p className="mt-1 text-sm text-red-600">{errors.password}</p>
              )}
            </div>

            {/* Confirm Password */}
            <div>
              <label htmlFor="password_confirm" className="block text-sm font-medium text-gray-700 mb-1">
                {t('password_confirm')}
              </label>
              <input
                type="password"
                id="password_confirm"
                name="password_confirm"
                value={formData.password_confirm}
                onChange={handleChange}
                className={`w-full px-4 py-3 border rounded-xl focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition-colors ${
                  errors.password_confirm ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="********"
              />
              {errors.password_confirm && (
                <p className="mt-1 text-sm text-red-600">{errors.password_confirm}</p>
              )}
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-4 bg-emerald-600 text-white font-semibold rounded-xl hover:bg-emerald-700 focus:ring-4 focus:ring-emerald-500/50 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
            >
              {isSubmitting ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  {t('submitting')}
                </span>
              ) : (
                t('submit')
              )}
            </button>
          </form>

          {/* Login Link */}
          <p className="mt-6 text-center text-gray-600">
            {t('login_link')}{' '}
            <Link href={`/${locale}/login`} className="text-emerald-600 font-semibold hover:text-emerald-700">
              {t('login_cta')}
            </Link>
          </p>
        </div>

        {/* No credit card required */}
        <p className="mt-6 text-center text-gray-500 text-sm">
          {t('no_credit_card')}
        </p>
      </div>
    </div>
  );
}
