'use client';

import { useTranslations } from 'next-intl';

const testimonials = [
  {
    id: 1,
    name: 'Adjoua Konan',
    role: 'Restaurant Owner',
    location: 'Cocody, Abidjan',
    avatar: 'AK',
    avatarBg: 'bg-emerald-500',
    quote: "BIZ360 has transformed how we serve our customers. The QR menu saves us on printing costs and customers love the instant access.",
    quoteFr: "BIZ360 a transforme notre façon de servir nos clients. Le menu QR nous fait economiser sur les couts d'impression et les clients adorent l'acces instantane.",
    rating: 5,
  },
  {
    id: 2,
    name: 'Kouamé Brou',
    role: 'Cafe Owner',
    location: 'Plateau, Abidjan',
    avatar: 'KB',
    avatarBg: 'bg-teal-500',
    quote: "The offline mode is incredible. Even when internet is down, we keep taking orders. When it comes back, everything syncs automatically.",
    quoteFr: "Le mode hors ligne est incroyable. Meme quand internet tombe, on continue a prendre des commandes. Quand ça revient, tout se synchronise.",
    rating: 5,
  },
  {
    id: 3,
    name: 'Aya Tra',
    role: 'Food Truck Owner',
    location: 'Treichville, Abidjan',
    avatar: 'AT',
    avatarBg: 'bg-orange-500',
    quote: "I update my menu from my phone while setting up at different locations. The mobile money integration makes payments so easy!",
    quoteFr: "Je mets a jour mon menu depuis mon telephone en m'installant a differents endroits. L'integration mobile money rend les paiements si faciles !",
    rating: 5,
  },
  {
    id: 4,
    name: 'Jean-Pierre Mensah',
    role: 'Hotel Manager',
    location: 'Accra, Ghana',
    avatar: 'JM',
    avatarBg: 'bg-purple-500',
    quote: "Managing our restaurant, pool bar, and room service from one dashboard has streamlined our entire operation.",
    quoteFr: "Gerer notre restaurant, bar piscine et room service depuis un seul tableau de bord a simplifie toute notre operation.",
    rating: 5,
  },
  {
    id: 5,
    name: 'Moussa Keita',
    role: 'Dark Kitchen Operator',
    location: 'Lagos, Nigeria',
    avatar: 'MK',
    avatarBg: 'bg-red-500',
    quote: "The delivery tracking keeps customers informed and has reduced our support calls by 50%. They can see exactly where their food is.",
    quoteFr: "Le suivi de livraison garde les clients informes et a reduit nos appels support de 50%. Ils voient exactement ou est leur commande.",
    rating: 5,
  },
  {
    id: 6,
    name: 'Aisha Okonkwo',
    role: 'Catering Business Owner',
    location: 'Abuja, Nigeria',
    avatar: 'AO',
    avatarBg: 'bg-pink-500',
    quote: "We handle multiple events simultaneously now without losing track. The inventory management ensures we never run out of ingredients.",
    quoteFr: "On gere plusieurs evenements simultanement maintenant sans perdre le fil. La gestion des stocks assure qu'on ne manque jamais d'ingredients.",
    rating: 5,
  },
];

export function Testimonials() {
  const t = useTranslations('marketing.testimonials');

  return (
    <section className="py-20 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-4">
            {t('title')}
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            {t('subtitle')}
          </p>
        </div>

        {/* Testimonials Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {testimonials.map((testimonial) => (
            <div
              key={testimonial.id}
              className="bg-white rounded-2xl p-6 shadow-sm hover:shadow-md transition-shadow"
            >
              {/* Stars */}
              <div className="flex gap-1 mb-4">
                {[...Array(testimonial.rating)].map((_, i) => (
                  <svg key={i} className="w-5 h-5 text-yellow-400" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                  </svg>
                ))}
              </div>

              {/* Quote */}
              <p className="text-gray-600 mb-6 leading-relaxed">
                "{testimonial.quote}"
              </p>

              {/* Author */}
              <div className="flex items-center gap-3">
                <div className={`w-12 h-12 ${testimonial.avatarBg} rounded-full flex items-center justify-center text-white font-semibold`}>
                  {testimonial.avatar}
                </div>
                <div>
                  <p className="font-semibold text-gray-900">{testimonial.name}</p>
                  <p className="text-sm text-gray-500">{testimonial.role}</p>
                  <p className="text-sm text-gray-400">{testimonial.location}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
