import { NextRequest, NextResponse } from 'next/server';

// Mock restaurant data for QR menu - matches PublicMenuResponse interface
// Localized for Côte d'Ivoire
const RESTAURANTS: Record<string, any> = {
  'maquis-ivoire': {
    restaurant: {
      id: 'rest-1',
      name: 'Maquis Ivoire',
      slug: 'maquis-ivoire',
      address: 'Rue des Jardins, Cocody, Abidjan',
      phone: '+225 07 12 34 56 78',
    },
    categories: [
      {
        id: 'cat-1',
        name: 'Plats Principaux',
        display_order: 1,
        is_visible: true,
        items: [
          {
            id: 'item-1',
            name: 'Garba',
            description: 'Attiéké avec thon frit, oignons et piment - plat populaire ivoirien',
            price: 1500,
            thumbnail_url: 'https://placehold.co/400x300/orange/white?text=Garba',
            is_available: true,
            modifiers: [
              {
                id: 'mod-1',
                name: 'Supplément',
                required: false,
                max_selections: 2,
                options: [
                  { id: 'opt-1', name: 'Oeuf', price_adjustment: 200, is_available: true },
                  { id: 'opt-2', name: 'Avocat', price_adjustment: 300, is_available: true },
                ],
              },
            ],
          },
          {
            id: 'item-2',
            name: 'Kédjenou de Poulet',
            description: 'Poulet mijoté aux légumes dans une sauce épicée - spécialité baoulé',
            price: 4500,
            thumbnail_url: 'https://placehold.co/400x300/red/white?text=Kedjenou',
            is_available: true,
            modifiers: [
              {
                id: 'mod-2',
                name: 'Accompagnement',
                required: true,
                max_selections: 1,
                options: [
                  { id: 'opt-3', name: 'Attiéké', price_adjustment: 0, is_available: true },
                  { id: 'opt-4', name: 'Foutou banane', price_adjustment: 500, is_available: true },
                  { id: 'opt-5', name: 'Riz blanc', price_adjustment: 0, is_available: true },
                ],
              },
            ],
          },
          {
            id: 'item-3',
            name: 'Alloco Poisson',
            description: 'Bananes plantains frites avec poisson braisé et sauce tomate',
            price: 3500,
            thumbnail_url: 'https://placehold.co/400x300/gold/black?text=Alloco',
            is_available: true,
            modifiers: [],
          },
          {
            id: 'item-4',
            name: 'Sauce Graine',
            description: 'Sauce à base de noix de palme avec viande de boeuf',
            price: 5000,
            thumbnail_url: 'https://placehold.co/400x300/brown/white?text=Graine',
            is_available: true,
            modifiers: [
              {
                id: 'mod-3',
                name: 'Accompagnement',
                required: true,
                max_selections: 1,
                options: [
                  { id: 'opt-6', name: 'Foutou igname', price_adjustment: 0, is_available: true },
                  { id: 'opt-7', name: 'Placali', price_adjustment: 0, is_available: true },
                ],
              },
            ],
          },
        ],
      },
      {
        id: 'cat-2',
        name: 'Boissons',
        display_order: 2,
        is_visible: true,
        items: [
          {
            id: 'item-6',
            name: 'Bissap',
            description: 'Jus d\'hibiscus frais et sucré',
            price: 500,
            thumbnail_url: 'https://placehold.co/400x300/purple/white?text=Bissap',
            is_available: true,
            modifiers: [],
          },
          {
            id: 'item-7',
            name: 'Gnamakoudji',
            description: 'Jus de gingembre maison',
            price: 500,
            thumbnail_url: 'https://placehold.co/400x300/yellow/black?text=Gingembre',
            is_available: true,
            modifiers: [],
          },
          {
            id: 'item-8',
            name: 'Bandji',
            description: 'Vin de palme naturel',
            price: 1000,
            thumbnail_url: 'https://placehold.co/400x300/cream/brown?text=Bandji',
            is_available: true,
            modifiers: [],
          },
        ],
      },
    ],
  },
  'teranga': {
    restaurant: {
      id: 'rest-2',
      name: 'Restaurant Teranga',
      slug: 'teranga',
      address: 'Boulevard Lagunaire, Plateau, Abidjan',
      phone: '+225 27 20 21 22 23',
    },
    categories: [
      {
        id: 'cat-1',
        name: 'Plats Principaux',
        display_order: 1,
        is_visible: true,
        items: [
          {
            id: 'item-1',
            name: 'Poulet Braisé',
            description: 'Poulet grillé aux épices, servi avec attiéké et alloco',
            price: 4500,
            thumbnail_url: 'https://placehold.co/400x300/orange/white?text=Braise',
            is_available: true,
            modifiers: [
              {
                id: 'mod-1',
                name: 'Accompagnement',
                required: true,
                max_selections: 1,
                options: [
                  { id: 'opt-1', name: 'Attiéké', price_adjustment: 0, is_available: true },
                  { id: 'opt-2', name: 'Alloco', price_adjustment: 500, is_available: true },
                ],
              },
            ],
          },
          {
            id: 'item-2',
            name: 'Poisson Braisé',
            description: 'Poisson grillé au charbon avec sauce claire',
            price: 5000,
            thumbnail_url: 'https://placehold.co/400x300/blue/white?text=Poisson',
            is_available: true,
            modifiers: [],
          },
        ],
      },
    ],
  },
};

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ slug: string }> }
) {
  const { slug } = await params;

  const data = RESTAURANTS[slug];

  if (!data) {
    return NextResponse.json(
      { error: 'Restaurant not found' },
      { status: 404 }
    );
  }

  return NextResponse.json(data);
}
