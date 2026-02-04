'use client';

import { useState, useEffect, useRef } from 'react';
import { useTranslations } from 'next-intl';
import { useLocale } from 'next-intl';
import { useRouter } from 'next/navigation';
import QRCode from 'qrcode';

interface QRCodeStepProps {
  restaurantSlug: string;
  onBack: () => void;
}

type QRSize = 'small' | 'medium' | 'large';

const QR_SIZES: Record<QRSize, number> = {
  small: 200,
  medium: 400,
  large: 800,
};

export function QRCodeStep({ restaurantSlug, onBack }: QRCodeStepProps) {
  const t = useTranslations('onboarding.qrCode');
  const locale = useLocale();
  const router = useRouter();
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const printCanvasRef = useRef<HTMLCanvasElement>(null);

  const [menuUrl, setMenuUrl] = useState('');
  const [copied, setCopied] = useState(false);
  const [qrDataUrl, setQrDataUrl] = useState<string>('');

  useEffect(() => {
    // Build the menu URL
    const baseUrl = typeof window !== 'undefined' ? window.location.origin : '';
    const url = `${baseUrl}/${locale}/menu/${restaurantSlug}`;
    setMenuUrl(url);

    // Generate QR code
    generateQRCode(url);
  }, [locale, restaurantSlug]);

  const generateQRCode = async (url: string) => {
    if (!canvasRef.current) return;

    try {
      await QRCode.toCanvas(canvasRef.current, url, {
        width: 240,
        margin: 2,
        color: {
          dark: '#059669', // emerald-600
          light: '#ffffff',
        },
      });

      // Also create data URL for preview
      const dataUrl = await QRCode.toDataURL(url, {
        width: 240,
        margin: 2,
        color: {
          dark: '#059669',
          light: '#ffffff',
        },
      });
      setQrDataUrl(dataUrl);
    } catch (err) {
      console.error('Failed to generate QR code:', err);
    }
  };

  const downloadQRCode = async (size: QRSize) => {
    const width = QR_SIZES[size];

    try {
      const dataUrl = await QRCode.toDataURL(menuUrl, {
        width,
        margin: 2,
        color: {
          dark: '#059669',
          light: '#ffffff',
        },
      });

      // Create download link
      const link = document.createElement('a');
      link.download = `qr-code-${restaurantSlug}-${size}.png`;
      link.href = dataUrl;
      link.click();
    } catch (err) {
      console.error('Failed to download QR code:', err);
    }
  };

  const printQRCode = async () => {
    try {
      // Generate large QR code for printing
      const dataUrl = await QRCode.toDataURL(menuUrl, {
        width: 600,
        margin: 4,
        color: {
          dark: '#059669',
          light: '#ffffff',
        },
      });

      // Create print window
      const printWindow = window.open('', '_blank');
      if (!printWindow) {
        alert('Please allow popups for printing');
        return;
      }

      printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>QR Code - ${restaurantSlug}</title>
          <style>
            body {
              margin: 0;
              padding: 40px;
              display: flex;
              flex-direction: column;
              align-items: center;
              justify-content: center;
              min-height: 100vh;
              font-family: system-ui, -apple-system, sans-serif;
            }
            img {
              max-width: 100%;
              height: auto;
            }
            .title {
              margin-bottom: 20px;
              font-size: 24px;
              font-weight: bold;
              color: #059669;
            }
            .url {
              margin-top: 20px;
              font-size: 14px;
              color: #666;
              word-break: break-all;
            }
            @media print {
              body {
                padding: 20px;
              }
            }
          </style>
        </head>
        <body>
          <div class="title">Scannez pour voir notre menu</div>
          <img src="${dataUrl}" alt="QR Code">
          <div class="url">${menuUrl}</div>
        </body>
        </html>
      `);

      printWindow.document.close();
      printWindow.onload = () => {
        printWindow.print();
      };
    } catch (err) {
      console.error('Failed to print QR code:', err);
    }
  };

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(menuUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      // Fallback for older browsers
      const input = document.createElement('input');
      input.value = menuUrl;
      document.body.appendChild(input);
      input.select();
      document.execCommand('copy');
      document.body.removeChild(input);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const goToDashboard = () => {
    router.push(`/${locale}/lite/dashboard`);
  };

  return (
    <div className="max-w-lg mx-auto">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900">{t('title')}</h2>
        <p className="text-gray-500 mt-2">{t('subtitle')}</p>
      </div>

      {/* QR Code Display */}
      <div className="flex justify-center mb-8">
        <div className="bg-white p-6 rounded-2xl shadow-lg border border-gray-100">
          <canvas ref={canvasRef} className="mx-auto" />
        </div>
      </div>

      {/* Download Options */}
      <div className="mb-8">
        <label className="block text-sm font-medium text-gray-700 mb-3 text-center">
          {t('download')}
        </label>
        <div className="flex gap-3 justify-center">
          <button
            onClick={() => downloadQRCode('small')}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
          >
            {t('small')}
          </button>
          <button
            onClick={() => downloadQRCode('medium')}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
          >
            {t('medium')}
          </button>
          <button
            onClick={() => downloadQRCode('large')}
            className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 transition-colors text-sm"
          >
            {t('large')}
          </button>
        </div>
      </div>

      {/* Print Button */}
      <div className="mb-8 text-center">
        <button
          onClick={printQRCode}
          className="inline-flex items-center gap-2 px-6 py-3 bg-white border border-gray-300 text-gray-700 rounded-xl hover:bg-gray-50 transition-colors"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-4a2 2 0 00-2-2H9a2 2 0 00-2 2v4a2 2 0 002 2zm8-12V5a2 2 0 00-2-2H9a2 2 0 00-2 2v4h10z" />
          </svg>
          {t('print')}
        </button>
      </div>

      {/* Menu URL */}
      <div className="mb-8">
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {t('menuUrl')}
        </label>
        <div className="flex gap-2">
          <input
            type="text"
            value={menuUrl}
            readOnly
            className="flex-1 px-4 py-3 bg-gray-50 border border-gray-200 rounded-xl text-gray-600 text-sm"
          />
          <button
            onClick={copyLink}
            className={`px-4 py-3 rounded-xl transition-colors ${
              copied
                ? 'bg-emerald-100 text-emerald-700'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {copied ? (
              <span className="flex items-center gap-1">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                {t('copied')}
              </span>
            ) : (
              t('copyLink')
            )}
          </button>
        </div>
      </div>

      {/* Actions */}
      <div className="flex gap-3">
        <button
          onClick={onBack}
          className="flex-1 py-3 border border-gray-300 text-gray-700 font-medium rounded-xl hover:bg-gray-50 transition-colors"
        >
          {t('back')}
        </button>
        <button
          onClick={goToDashboard}
          className="flex-1 py-3 bg-emerald-600 text-white font-semibold rounded-xl hover:bg-emerald-700 transition-colors"
        >
          {t('goToDashboard')}
        </button>
      </div>

      {/* Hidden canvas for printing */}
      <canvas ref={printCanvasRef} className="hidden" />
    </div>
  );
}
