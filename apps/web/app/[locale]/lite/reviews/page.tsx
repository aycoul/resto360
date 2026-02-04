'use client';

import { useState, useEffect } from 'react';
import { useTranslations } from 'next-intl';
import { api } from '@/lib/api/client';
import type { Review, ReviewSummary, ReviewStatus } from '@/lib/api/types';

export default function ReviewsPage() {
  const t = useTranslations('lite.reviews');
  const tCommon = useTranslations('common');

  const [reviews, setReviews] = useState<Review[]>([]);
  const [summary, setSummary] = useState<ReviewSummary | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [selectedReview, setSelectedReview] = useState<Review | null>(null);

  useEffect(() => {
    loadData();
  }, [filter]);

  const loadData = async () => {
    setIsLoading(true);
    try {
      const params = filter !== 'all' ? `?status=${filter}` : '';
      const [reviewsData, summaryData] = await Promise.all([
        api.get<Review[]>(`/api/v1/reviews/reviews/${params}`),
        api.get<ReviewSummary>('/api/v1/reviews/summary/'),
      ]);
      setReviews(reviewsData);
      setSummary(summaryData);
    } catch (error) {
      console.error('Failed to load reviews:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleApprove = async (review: Review) => {
    try {
      await api.post(`/api/v1/reviews/reviews/${review.id}/approve/`, {});
      loadData();
    } catch (error) {
      console.error('Failed to approve review:', error);
    }
  };

  const handleReject = async (review: Review) => {
    try {
      await api.post(`/api/v1/reviews/reviews/${review.id}/reject/`, {});
      loadData();
    } catch (error) {
      console.error('Failed to reject review:', error);
    }
  };

  const handleFeature = async (review: Review) => {
    try {
      await api.post(`/api/v1/reviews/reviews/${review.id}/feature/`, {});
      loadData();
    } catch (error) {
      console.error('Failed to toggle feature:', error);
    }
  };

  const getStatusBadgeColor = (status: ReviewStatus) => {
    switch (status) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800';
      case 'approved':
        return 'bg-green-100 text-green-800';
      case 'rejected':
        return 'bg-red-100 text-red-800';
      case 'flagged':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const renderStars = (rating: number) => {
    return (
      <div className="flex gap-0.5">
        {[1, 2, 3, 4, 5].map((star) => (
          <svg
            key={star}
            className={`w-4 h-4 ${star <= rating ? 'text-yellow-400' : 'text-gray-300'}`}
            fill="currentColor"
            viewBox="0 0 20 20"
          >
            <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
          </svg>
        ))}
      </div>
    );
  };

  return (
    <div className="max-w-6xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{t('title')}</h1>
        <p className="text-gray-500 mt-1">{t('subtitle')}</p>
      </div>

      {/* Summary Cards */}
      {summary && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <p className="text-sm text-gray-500">{t('totalReviews')}</p>
            <p className="text-2xl font-bold text-gray-900">{summary.total_reviews}</p>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <p className="text-sm text-gray-500">{t('averageRating')}</p>
            <div className="flex items-center gap-2">
              <p className="text-2xl font-bold text-gray-900">
                {Number(summary.average_rating).toFixed(1)}
              </p>
              {renderStars(Math.round(Number(summary.average_rating)))}
            </div>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <p className="text-sm text-gray-500">{t('responseRate')}</p>
            <p className="text-2xl font-bold text-emerald-600">
              {Number(summary.response_rate).toFixed(0)}%
            </p>
          </div>
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4">
            <p className="text-sm text-gray-500">{t('pendingModeration')}</p>
            <p className="text-2xl font-bold text-yellow-600">
              {reviews.filter(r => r.status === 'pending').length}
            </p>
          </div>
        </div>
      )}

      {/* Filters */}
      <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-4 mb-6">
        <div className="flex flex-wrap gap-2">
          {['all', 'pending', 'approved', 'rejected'].map((status) => (
            <button
              key={status}
              onClick={() => setFilter(status)}
              className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                filter === status
                  ? 'bg-emerald-600 text-white'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              {t(`filter.${status}`)}
            </button>
          ))}
        </div>
      </div>

      {/* Reviews List */}
      <div className="space-y-4">
        {isLoading ? (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 flex items-center justify-center">
            <div className="w-8 h-8 border-4 border-emerald-600 border-t-transparent rounded-full animate-spin" />
          </div>
        ) : reviews.length === 0 ? (
          <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-12 text-center">
            <div className="text-4xl mb-4">⭐</div>
            <h3 className="text-lg font-medium text-gray-900 mb-2">{t('noReviews')}</h3>
            <p className="text-gray-500">{t('noReviewsDesc')}</p>
          </div>
        ) : (
          reviews.map((review) => (
            <div
              key={review.id}
              className="bg-white rounded-xl shadow-sm border border-gray-200 p-6"
            >
              <div className="flex justify-between items-start mb-4">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-emerald-100 rounded-full flex items-center justify-center">
                    <span className="text-emerald-700 font-semibold">
                      {review.reviewer_name.charAt(0).toUpperCase()}
                    </span>
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-gray-900">
                        {review.reviewer_name}
                      </span>
                      {review.is_verified && (
                        <span className="px-2 py-0.5 text-xs bg-blue-100 text-blue-700 rounded-full">
                          {t('verified')}
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-2 mt-1">
                      {renderStars(review.rating)}
                      <span className="text-sm text-gray-500">
                        {new Date(review.created_at).toLocaleDateString()}
                      </span>
                    </div>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusBadgeColor(review.status)}`}>
                    {review.status_display}
                  </span>
                  {review.is_featured && (
                    <span className="px-2 py-1 text-xs bg-purple-100 text-purple-700 rounded-full">
                      {t('featured')}
                    </span>
                  )}
                </div>
              </div>

              {review.title && (
                <h4 className="font-medium text-gray-900 mb-2">{review.title}</h4>
              )}

              {review.content && (
                <p className="text-gray-600 mb-4">{review.content}</p>
              )}

              {/* Sub-ratings */}
              {(review.food_rating || review.service_rating || review.ambiance_rating || review.value_rating) && (
                <div className="flex flex-wrap gap-4 mb-4 text-sm">
                  {review.food_rating && (
                    <div className="flex items-center gap-1">
                      <span className="text-gray-500">{t('food')}:</span>
                      {renderStars(review.food_rating)}
                    </div>
                  )}
                  {review.service_rating && (
                    <div className="flex items-center gap-1">
                      <span className="text-gray-500">{t('service')}:</span>
                      {renderStars(review.service_rating)}
                    </div>
                  )}
                  {review.ambiance_rating && (
                    <div className="flex items-center gap-1">
                      <span className="text-gray-500">{t('ambiance')}:</span>
                      {renderStars(review.ambiance_rating)}
                    </div>
                  )}
                  {review.value_rating && (
                    <div className="flex items-center gap-1">
                      <span className="text-gray-500">{t('value')}:</span>
                      {renderStars(review.value_rating)}
                    </div>
                  )}
                </div>
              )}

              {/* Owner Response */}
              {review.response && (
                <div className="mt-4 p-4 bg-gray-50 rounded-lg border-l-4 border-emerald-500">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="font-medium text-gray-900">
                      {review.response.responder_name || t('ownerResponse')}
                    </span>
                    <span className="text-sm text-gray-500">
                      {new Date(review.response.created_at).toLocaleDateString()}
                    </span>
                  </div>
                  <p className="text-gray-600">{review.response.content}</p>
                </div>
              )}

              {/* Actions */}
              <div className="flex gap-2 mt-4 pt-4 border-t border-gray-100">
                {review.status === 'pending' && (
                  <>
                    <button
                      onClick={() => handleApprove(review)}
                      className="px-3 py-1.5 text-sm bg-green-100 text-green-700 rounded-lg hover:bg-green-200"
                    >
                      {t('approve')}
                    </button>
                    <button
                      onClick={() => handleReject(review)}
                      className="px-3 py-1.5 text-sm bg-red-100 text-red-700 rounded-lg hover:bg-red-200"
                    >
                      {t('reject')}
                    </button>
                  </>
                )}
                {review.status === 'approved' && (
                  <>
                    <button
                      onClick={() => handleFeature(review)}
                      className={`px-3 py-1.5 text-sm rounded-lg ${
                        review.is_featured
                          ? 'bg-purple-100 text-purple-700 hover:bg-purple-200'
                          : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                      }`}
                    >
                      {review.is_featured ? t('unfeature') : t('feature')}
                    </button>
                    {!review.response && (
                      <button
                        onClick={() => setSelectedReview(review)}
                        className="px-3 py-1.5 text-sm bg-emerald-100 text-emerald-700 rounded-lg hover:bg-emerald-200"
                      >
                        {t('respond')}
                      </button>
                    )}
                  </>
                )}
              </div>
            </div>
          ))
        )}
      </div>

      {/* Response Modal */}
      {selectedReview && (
        <ResponseModal
          review={selectedReview}
          onClose={() => setSelectedReview(null)}
          onResponded={() => {
            setSelectedReview(null);
            loadData();
          }}
        />
      )}
    </div>
  );
}

interface ResponseModalProps {
  review: Review;
  onClose: () => void;
  onResponded: () => void;
}

function ResponseModal({ review, onClose, onResponded }: ResponseModalProps) {
  const t = useTranslations('lite.reviews');
  const [content, setContent] = useState('');
  const [responderName, setResponderName] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!content.trim()) return;

    setIsSubmitting(true);
    try {
      await api.post(`/api/v1/reviews/reviews/${review.id}/respond/`, {
        content,
        responder_name: responderName || undefined,
      });
      onResponded();
    } catch (error) {
      console.error('Failed to respond:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-lg max-w-lg w-full">
        <div className="p-6 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">{t('respondToReview')}</h2>
        </div>
        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          <div className="p-4 bg-gray-50 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <span className="font-medium">{review.reviewer_name}</span>
              <span className="text-yellow-500">{'★'.repeat(review.rating)}</span>
            </div>
            {review.content && (
              <p className="text-gray-600 text-sm">{review.content}</p>
            )}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('responderName')}
            </label>
            <input
              type="text"
              value={responderName}
              onChange={(e) => setResponderName(e.target.value)}
              placeholder={t('responderNamePlaceholder')}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              {t('yourResponse')} *
            </label>
            <textarea
              value={content}
              onChange={(e) => setContent(e.target.value)}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg"
              required
            />
          </div>

          <div className="flex justify-end gap-3">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50"
            >
              {t('cancel')}
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !content.trim()}
              className="px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700 disabled:opacity-50"
            >
              {isSubmitting ? t('sending') : t('sendResponse')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
