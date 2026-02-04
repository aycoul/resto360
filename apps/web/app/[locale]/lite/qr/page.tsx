'use client';

import { useState, useRef, useEffect } from 'react';
import { useTranslations, useLocale } from 'next-intl';
import { useLiteContext } from '../layout';
import { UpgradePrompt } from '@/components/lite/UpgradePrompt';

type QRSize = 'small' | 'medium' | 'large' | 'print';

const QR_SIZES: Record<QRSize, number> = {
  small: 200,
  medium: 400,
  large: 800,
  print: 1200,
};

export default function LiteQRPage() {
  const locale = useLocale();
  const t = useTranslations('lite.qr');
  const { restaurant } = useLiteContext();
  const [copied, setCopied] = useState(false);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const menuUrl = typeof window !== 'undefined'
    ? `${window.location.origin}/${locale}/menu/${restaurant?.slug || 'demo'}`
    : '';

  // Generate QR code on canvas
  useEffect(() => {
    if (!canvasRef.current || !menuUrl) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Import QRCode library dynamically
    import('qrcode').then((QRCode) => {
      QRCode.toCanvas(canvas, menuUrl, {
        width: 280,
        margin: 2,
        color: {
          dark: '#059669',
          light: '#ffffff',
        },
        errorCorrectionLevel: 'M',
      });
    }).catch((err) => {
      console.error('Failed to generate QR code:', err);
      // Fallback: draw placeholder
      ctx.fillStyle = '#f3f4f6';
      ctx.fillRect(0, 0, 280, 280);
      ctx.fillStyle = '#9ca3af';
      ctx.font = '14px sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText('QR Code', 140, 140);
    });
  }, [menuUrl]);

  const handleCopyLink = async () => {
    try {
      await navigator.clipboard.writeText(menuUrl);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleDownload = async (size: QRSize, format: 'png' | 'svg' = 'png') => {
    if (!menuUrl) return;

    try {
      const QRCode = await import('qrcode');
      const dimension = QR_SIZES[size];

      if (format === 'svg') {
        const svg = await QRCode.toString(menuUrl, {
          type: 'svg',
          width: dimension,
          margin: 2,
          color: {
            dark: '#059669',
            light: '#ffffff',
          },
        });
        const blob = new Blob([svg], { type: 'image/svg+xml' });
        downloadBlob(blob, `${restaurant?.slug || 'menu'}-qr.svg`);
      } else {
        const dataUrl = await QRCode.toDataURL(menuUrl, {
          width: dimension,
          margin: 2,
          color: {
            dark: '#059669',
            light: '#ffffff',
          },
        });
        const link = document.createElement('a');
        link.download = `${restaurant?.slug || 'menu'}-qr-${size}.png`;
        link.href = dataUrl;
        link.click();
      }
    } catch (err) {
      console.error('Failed to download QR code:', err);
    }
  };

  const downloadBlob = (blob: Blob, filename: string) => {
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.download = filename;
    link.href = url;
    link.click();
    URL.revokeObjectURL(url);
  };

  const downloadSizes: { key: QRSize; label: string }[] = [
    { key: 'small', label: t('sizeSmall') },
    { key: 'medium', label: t('sizeMedium') },
    { key: 'large', label: t('sizeLarge') },
    { key: 'print', label: t('sizePrint') },
  ];

  return (
    <div className="max-w-4xl mx-auto">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">{t('title')}</h1>
        <p className="text-gray-500 mt-1">{t('subtitle')}</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* QR Preview */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h2 className="font-semibold text-gray-900 mb-4">{t('preview')}</h2>
          <div className="flex flex-col items-center">
            <div className="bg-white p-4 rounded-xl border-2 border-dashed border-gray-200">
              <canvas ref={canvasRef} width={280} height={280} className="rounded-lg" />
            </div>
            <p className="text-sm text-gray-500 mt-4 text-center max-w-xs">
              {t('scanToView')}
            </p>
          </div>
        </div>

        {/* Download Options */}
        <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
          <h2 className="font-semibold text-gray-900 mb-4">{t('downloadOptions')}</h2>

          {/* PNG Downloads */}
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-700 mb-3">{t('pngFormat')}</h3>
            <div className="grid grid-cols-2 gap-3">
              {downloadSizes.map(({ key, label }) => (
                <button
                  key={key}
                  onClick={() => handleDownload(key, 'png')}
                  className="flex items-center justify-center gap-2 px-4 py-3 bg-gray-50 hover:bg-gray-100 rounded-lg text-sm font-medium text-gray-700 transition-colors"
                >
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                  </svg>
                  {label}
                </button>
              ))}
            </div>
          </div>

          {/* SVG Download */}
          <div className="mb-6">
            <h3 className="text-sm font-medium text-gray-700 mb-3">{t('svgFormat')}</h3>
            <button
              onClick={() => handleDownload('large', 'svg')}
              className="w-full flex items-center justify-center gap-2 px-4 py-3 bg-emerald-50 hover:bg-emerald-100 rounded-lg text-sm font-medium text-emerald-700 transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
              </svg>
              {t('downloadSvg')}
            </button>
          </div>

          {/* Menu Link */}
          <div>
            <h3 className="text-sm font-medium text-gray-700 mb-3">{t('menuLink')}</h3>
            <div className="flex gap-2">
              <input
                type="text"
                readOnly
                value={menuUrl}
                className="flex-1 px-3 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-600 truncate"
              />
              <button
                onClick={handleCopyLink}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  copied
                    ? 'bg-emerald-100 text-emerald-700'
                    : 'bg-gray-100 hover:bg-gray-200 text-gray-700'
                }`}
              >
                {copied ? t('copied') : t('copy')}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Instructions */}
      <div className="mt-6 bg-white rounded-xl p-6 shadow-sm border border-gray-100">
        <h2 className="font-semibold text-gray-900 mb-4">{t('instructions')}</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 bg-emerald-100 text-emerald-600 rounded-lg flex items-center justify-center font-bold">
              1
            </div>
            <div>
              <h3 className="font-medium text-gray-900">{t('step1Title')}</h3>
              <p className="text-sm text-gray-500 mt-1">{t('step1Desc')}</p>
            </div>
          </div>
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 bg-emerald-100 text-emerald-600 rounded-lg flex items-center justify-center font-bold">
              2
            </div>
            <div>
              <h3 className="font-medium text-gray-900">{t('step2Title')}</h3>
              <p className="text-sm text-gray-500 mt-1">{t('step2Desc')}</p>
            </div>
          </div>
          <div className="flex gap-3">
            <div className="flex-shrink-0 w-8 h-8 bg-emerald-100 text-emerald-600 rounded-lg flex items-center justify-center font-bold">
              3
            </div>
            <div>
              <h3 className="font-medium text-gray-900">{t('step3Title')}</h3>
              <p className="text-sm text-gray-500 mt-1">{t('step3Desc')}</p>
            </div>
          </div>
        </div>
      </div>

      {/* Upgrade prompt for branding removal */}
      {restaurant?.plan_type === 'free' && (
        <div className="mt-6">
          <div className="bg-white rounded-xl p-6 shadow-sm border border-gray-100">
            <div className="flex items-center gap-3 text-gray-600 mb-4">
              <svg className="w-5 h-5 text-amber-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span className="text-sm">{t('brandingNote')}</span>
            </div>
            <UpgradePrompt variant="inline" />
          </div>
        </div>
      )}
    </div>
  );
}
