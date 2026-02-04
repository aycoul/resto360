/**
 * Driver information card with contact options.
 */
'use client';

import { useTranslations } from 'next-intl';

interface DriverInfoProps {
  driver: {
    name: string;
    phone: string;
    vehicle_type: string;
  };
}

export default function DriverInfo({ driver }: DriverInfoProps) {
  const t = useTranslations('delivery');

  const vehicleLabels: Record<string, string> = {
    motorcycle: 'Motorcycle',
    bicycle: 'Bicycle',
    car: 'Car',
    foot: 'On Foot',
  };

  const handleCall = () => {
    window.location.href = `tel:${driver.phone}`;
  };

  const handleMessage = () => {
    // Use SMS on mobile, WhatsApp fallback
    const message = encodeURIComponent("Hi, I have a question about my delivery");
    window.location.href = `sms:${driver.phone}?body=${message}`;
  };

  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <h3 className="text-sm font-medium text-gray-500 mb-3">
        {t('yourDriver', { defaultValue: 'Your Driver' })}
      </h3>

      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
            <span className="text-xl">
              {driver.vehicle_type === 'motorcycle' ? '🏍️' :
               driver.vehicle_type === 'bicycle' ? '🚲' :
               driver.vehicle_type === 'car' ? '🚗' : '🚶'}
            </span>
          </div>
          <div>
            <p className="font-semibold">{driver.name}</p>
            <p className="text-sm text-gray-500">
              {vehicleLabels[driver.vehicle_type] || driver.vehicle_type}
            </p>
          </div>
        </div>

        <div className="flex space-x-2">
          <button
            onClick={handleCall}
            className="p-3 bg-green-500 text-white rounded-full hover:bg-green-600 transition-colors"
            aria-label={t('callDriver', { defaultValue: 'Call driver' })}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path d="M2 3a1 1 0 011-1h2.153a1 1 0 01.986.836l.74 4.435a1 1 0 01-.54 1.06l-1.548.773a11.037 11.037 0 006.105 6.105l.774-1.548a1 1 0 011.059-.54l4.435.74a1 1 0 01.836.986V17a1 1 0 01-1 1h-2C7.82 18 2 12.18 2 5V3z" />
            </svg>
          </button>
          <button
            onClick={handleMessage}
            className="p-3 bg-blue-500 text-white rounded-full hover:bg-blue-600 transition-colors"
            aria-label={t('messageDriver', { defaultValue: 'Message driver' })}
          >
            <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M18 10c0 3.866-3.582 7-8 7a8.841 8.841 0 01-4.083-.98L2 17l1.338-3.123C2.493 12.767 2 11.434 2 10c0-3.866 3.582-7 8-7s8 3.134 8 7zM7 9H5v2h2V9zm8 0h-2v2h2V9zM9 9h2v2H9V9z" clipRule="evenodd" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}
