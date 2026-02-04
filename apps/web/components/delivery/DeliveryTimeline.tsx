/**
 * Delivery status timeline showing progress.
 */
'use client';

import { useTranslations } from 'next-intl';

interface DeliveryTimelineProps {
  status: string;
  assignedAt?: string;
  pickedUpAt?: string;
  enRouteAt?: string;
  deliveredAt?: string;
}

const STATUSES = ['assigned', 'picked_up', 'en_route', 'delivered'];

export default function DeliveryTimeline({
  status,
  assignedAt,
  pickedUpAt,
  enRouteAt,
  deliveredAt,
}: DeliveryTimelineProps) {
  const t = useTranslations('delivery');

  const statusLabels: Record<string, string> = {
    pending_assignment: t('statusPending', { defaultValue: 'Finding driver...' }),
    assigned: t('statusAssigned', { defaultValue: 'Driver assigned' }),
    picked_up: t('statusPickedUp', { defaultValue: 'Order picked up' }),
    en_route: t('statusEnRoute', { defaultValue: 'On the way' }),
    delivered: t('statusDelivered', { defaultValue: 'Delivered' }),
  };

  const timestamps: Record<string, string | undefined> = {
    assigned: assignedAt,
    picked_up: pickedUpAt,
    en_route: enRouteAt,
    delivered: deliveredAt,
  };

  const formatTime = (isoString?: string) => {
    if (!isoString) return '';
    return new Date(isoString).toLocaleTimeString([], {
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const currentIndex = STATUSES.indexOf(status);

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <h3 className="text-sm font-medium text-gray-500 mb-4">
        {t('deliveryProgress', { defaultValue: 'Delivery Progress' })}
      </h3>

      <div className="space-y-4">
        {STATUSES.map((s, index) => {
          const isComplete = index < currentIndex || status === 'delivered';
          const isCurrent = s === status;

          return (
            <div key={s} className="flex items-start">
              {/* Status indicator */}
              <div className="flex flex-col items-center mr-4">
                <div
                  className={`w-6 h-6 rounded-full flex items-center justify-center ${
                    isComplete || isCurrent
                      ? 'bg-green-500 text-white'
                      : 'bg-gray-200 text-gray-400'
                  }`}
                >
                  {isComplete ? (
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  ) : (
                    <span className="text-xs">{index + 1}</span>
                  )}
                </div>
                {index < STATUSES.length - 1 && (
                  <div
                    className={`w-0.5 h-8 mt-1 ${
                      index < currentIndex ? 'bg-green-500' : 'bg-gray-200'
                    }`}
                  />
                )}
              </div>

              {/* Status text */}
              <div className="flex-1 pb-4">
                <p
                  className={`font-medium ${
                    isComplete || isCurrent ? 'text-gray-900' : 'text-gray-400'
                  }`}
                >
                  {statusLabels[s]}
                </p>
                {timestamps[s] && (
                  <p className="text-sm text-gray-500">{formatTime(timestamps[s])}</p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
