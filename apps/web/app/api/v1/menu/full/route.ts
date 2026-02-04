import { NextResponse } from 'next/server';

// Mock seed data for testing
// Localized for Côte d'Ivoire
const SEED_DATA = {
  categories: [
    {
      id: 'cat-1',
      name: 'Plats Principaux',
      display_order: 1,
      is_visible: true,
      items: [
        {
          id: 'item-1',
          name: 'Kédjenou de Poulet',
          description: 'Poulet mijoté aux légumes dans une sauce épicée - spécialité baoulé',
          price: 4500,
          thumbnail_url: 'https://placehold.co/200x200/orange/white?text=Kedjenou',
          is_available: true,
          modifiers: [
            {
              id: 'mod-1',
              name: 'Accompagnement',
              required: true,
              max_selections: 1,
              options: [
                { id: 'opt-1', name: 'Attiéké', price_adjustment: 0, is_available: true },
                { id: 'opt-2', name: 'Foutou banane', price_adjustment: 500, is_available: true },
                { id: 'opt-3', name: 'Riz blanc', price_adjustment: 0, is_available: true },
              ],
            },
          ],
        },
        {
          id: 'item-2',
          name: 'Garba',
          description: 'Attiéké avec thon frit, oignons et piment - plat populaire ivoirien',
          price: 1500,
          thumbnail_url: 'https://placehold.co/200x200/gold/black?text=Garba',
          is_available: true,
          modifiers: [
            {
              id: 'mod-4',
              name: 'Supplément',
              required: false,
              max_selections: 2,
              options: [
                { id: 'opt-10', name: 'Oeuf', price_adjustment: 200, is_available: true },
                { id: 'opt-11', name: 'Avocat', price_adjustment: 300, is_available: true },
              ],
            },
          ],
        },
        {
          id: 'item-3',
          name: 'Sauce Graine',
          description: 'Sauce à base de noix de palme avec viande de boeuf',
          price: 5000,
          thumbnail_url: 'https://placehold.co/200x200/brown/white?text=Graine',
          is_available: true,
          modifiers: [
            {
              id: 'mod-2',
              name: 'Accompagnement',
              required: true,
              max_selections: 1,
              options: [
                { id: 'opt-4', name: 'Foutou igname', price_adjustment: 0, is_available: true },
                { id: 'opt-5', name: 'Foutou banane', price_adjustment: 0, is_available: true },
                { id: 'opt-6', name: 'Placali', price_adjustment: 0, is_available: true },
              ],
            },
          ],
        },
      ],
    },
    {
      id: 'cat-2',
      name: 'Grillades',
      display_order: 2,
      is_visible: true,
      items: [
        {
          id: 'item-4',
          name: 'Poulet Braisé',
          description: 'Poulet grillé aux épices, servi avec attiéké ou alloco',
          price: 4500,
          thumbnail_url: 'https://placehold.co/200x200/darkred/white?text=Braise',
          is_available: true,
          modifiers: [],
        },
        {
          id: 'item-5',
          name: 'Poisson Braisé',
          description: 'Poisson grillé au charbon avec sauce claire',
          price: 5000,
          thumbnail_url: 'https://placehold.co/200x200/blue/white?text=Poisson',
          is_available: true,
          modifiers: [
            {
              id: 'mod-3',
              name: 'Accompagnement',
              required: true,
              max_selections: 1,
              options: [
                { id: 'opt-7', name: 'Attiéké', price_adjustment: 0, is_available: true },
                { id: 'opt-8', name: 'Alloco', price_adjustment: 500, is_available: true },
                { id: 'opt-9', name: 'Riz blanc', price_adjustment: 0, is_available: true },
              ],
            },
          ],
        },
        {
          id: 'item-9',
          name: 'Alloco Poisson',
          description: 'Bananes plantains frites avec poisson braisé',
          price: 3500,
          thumbnail_url: 'https://placehold.co/200x200/gold/black?text=Alloco',
          is_available: true,
          modifiers: [],
        },
      ],
    },
    {
      id: 'cat-3',
      name: 'Boissons',
      display_order: 3,
      is_visible: true,
      items: [
        {
          id: 'item-6',
          name: 'Bissap',
          description: 'Jus d\'hibiscus frais et sucré',
          price: 500,
          thumbnail_url: 'https://placehold.co/200x200/purple/white?text=Bissap',
          is_available: true,
          modifiers: [],
        },
        {
          id: 'item-7',
          name: 'Gnamakoudji',
          description: 'Jus de gingembre maison',
          price: 500,
          thumbnail_url: 'https://placehold.co/200x200/yellow/black?text=Gingembre',
          is_available: true,
          modifiers: [],
        },
        {
          id: 'item-8',
          name: 'Bandji',
          description: 'Vin de palme naturel',
          price: 1000,
          thumbnail_url: 'https://placehold.co/200x200/beige/black?text=Bandji',
          is_available: true,
          modifiers: [],
        },
      ],
    },
  ],
};

export async function GET() {
  // Simulate network delay
  await new Promise(resolve => setTimeout(resolve, 300));

  return NextResponse.json(SEED_DATA);
}
