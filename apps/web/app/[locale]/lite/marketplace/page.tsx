'use client';

import { useState, useEffect, ReactNode } from 'react';
import { useTranslations } from 'next-intl';

type Tab = 'browse' | 'orders' | 'favorites' | 'cart';
type OrderFilter = 'all' | 'active' | 'completed' | 'cancelled';

interface SupplierCategory {
  id: string;
  name: string;
  slug: string;
  icon: string;
  product_count: number;
}

interface Supplier {
  id: string;
  name: string;
  slug: string;
  description: string;
  supplier_type: string;
  city: string;
  logo: string | null;
  verification_status: string;
  minimum_order_value: number;
  lead_time_days: number;
  average_rating: number;
  review_count: number;
  product_count: number;
  is_featured: boolean;
}

interface Product {
  id: string;
  supplier: string;
  supplier_name: string;
  category: string;
  category_name: string;
  name: string;
  description: string;
  unit: string;
  unit_size: number;
  price: number;
  minimum_order_quantity: number;
  is_available: boolean;
  stock_status: string;
  image: string | null;
  origin: string;
  brand: string;
  certifications: string[];
}

interface CartItem {
  id: string;
  product: Product;
  quantity: number;
  unit_price: number;
  line_total: number;
}

interface Cart {
  id: string;
  supplier: Supplier;
  items: CartItem[];
  total: number;
  item_count: number;
}

interface Order {
  id: string;
  order_number: string;
  supplier_name: string;
  status: string;
  payment_status: string;
  total: number;
  item_count: number;
  expected_delivery: string | null;
  created_at: string;
}

interface Favorite {
  id: string;
  supplier: Supplier;
  notes: string;
  created_at: string;
}

const TAB_ICONS: Record<Tab, ReactNode> = {
  browse: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
    </svg>
  ),
  orders: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
    </svg>
  ),
  favorites: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
    </svg>
  ),
  cart: (
    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
    </svg>
  ),
};

const CATEGORY_ICONS: Record<string, string> = {
  produce: '🥬',
  meat: '🍖',
  seafood: '🐟',
  dairy: '🥛',
  beverages: '🍹',
  dryGoods: '🌾',
  spices: '🌶️',
  packaging: '📦',
  equipment: '🔧',
};

function formatCurrency(value: number): string {
  return new Intl.NumberFormat('fr-FR', { style: 'decimal' }).format(value) + ' XOF';
}

function formatDate(dateString: string): string {
  return new Date(dateString).toLocaleDateString('fr-FR', {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  });
}

export default function MarketplacePage() {
  const t = useTranslations('lite.marketplace');
  const [activeTab, setActiveTab] = useState<Tab>('browse');
  const [loading, setLoading] = useState(true);

  // Browse state
  const [categories, setCategories] = useState<SupplierCategory[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState('name');

  // Cart state
  const [carts, setCarts] = useState<Cart[]>([]);
  const [cartTotal, setCartTotal] = useState(0);

  // Orders state
  const [orders, setOrders] = useState<Order[]>([]);
  const [orderFilter, setOrderFilter] = useState<OrderFilter>('all');

  // Favorites state
  const [favorites, setFavorites] = useState<Favorite[]>([]);

  const tabs: Tab[] = ['browse', 'orders', 'favorites', 'cart'];

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 500));

      // Mock categories
      setCategories([
        { id: '1', name: 'Fruits et Legumes', slug: 'produce', icon: '🥬', product_count: 45 },
        { id: '2', name: 'Viande et Volaille', slug: 'meat', icon: '🍖', product_count: 32 },
        { id: '3', name: 'Fruits de Mer', slug: 'seafood', icon: '🐟', product_count: 18 },
        { id: '4', name: 'Produits Laitiers', slug: 'dairy', icon: '🥛', product_count: 24 },
        { id: '5', name: 'Boissons', slug: 'beverages', icon: '🍹', product_count: 56 },
        { id: '6', name: 'Epicerie Seche', slug: 'dryGoods', icon: '🌾', product_count: 89 },
        { id: '7', name: 'Epices', slug: 'spices', icon: '🌶️', product_count: 42 },
        { id: '8', name: 'Emballages', slug: 'packaging', icon: '📦', product_count: 28 },
      ]);

      // Mock suppliers
      setSuppliers([
        {
          id: '1',
          name: 'Marché d\'Adjamé',
          slug: 'marche-adjame',
          description: 'Grossiste en fruits et légumes frais',
          supplier_type: 'wholesaler',
          city: 'Abidjan',
          logo: null,
          verification_status: 'verified',
          minimum_order_value: 50000,
          lead_time_days: 1,
          average_rating: 4.5,
          review_count: 28,
          product_count: 156,
          is_featured: true,
        },
        {
          id: '2',
          name: 'Ivoire Viandes',
          slug: 'ivoire-viandes',
          description: 'Fournisseur de viande halal de qualité',
          supplier_type: 'distributor',
          city: 'Abidjan',
          logo: null,
          verification_status: 'verified',
          minimum_order_value: 75000,
          lead_time_days: 2,
          average_rating: 4.8,
          review_count: 45,
          product_count: 48,
          is_featured: true,
        },
        {
          id: '3',
          name: 'San-Pédro Pêche',
          slug: 'san-pedro-peche',
          description: 'Poissons et fruits de mer frais',
          supplier_type: 'producer',
          city: 'San-Pédro',
          logo: null,
          verification_status: 'verified',
          minimum_order_value: 100000,
          lead_time_days: 1,
          average_rating: 4.3,
          review_count: 19,
          product_count: 35,
          is_featured: false,
        },
      ]);

      // Mock products
      setProducts([
        {
          id: '1',
          supplier: '1',
          supplier_name: 'Marché d\'Adjamé',
          category: '1',
          category_name: 'Fruits et Légumes',
          name: 'Oignons (sac 25kg)',
          description: 'Oignons frais de qualité supérieure',
          unit: 'kg',
          unit_size: 25,
          price: 15000,
          minimum_order_quantity: 1,
          is_available: true,
          stock_status: 'in_stock',
          image: null,
          origin: 'Côte d\'Ivoire',
          brand: '',
          certifications: [],
        },
        {
          id: '2',
          supplier: '1',
          supplier_name: 'Marché d\'Adjamé',
          category: '1',
          category_name: 'Fruits et Légumes',
          name: 'Tomates (caisse 15kg)',
          description: 'Tomates fraîches locales',
          unit: 'kg',
          unit_size: 15,
          price: 18000,
          minimum_order_quantity: 1,
          is_available: true,
          stock_status: 'in_stock',
          image: null,
          origin: 'Côte d\'Ivoire',
          brand: '',
          certifications: [],
        },
        {
          id: '3',
          supplier: '2',
          supplier_name: 'Ivoire Viandes',
          category: '2',
          category_name: 'Viande et Volaille',
          name: 'Poulet entier (carton 10kg)',
          description: 'Poulet halal certifié',
          unit: 'kg',
          unit_size: 10,
          price: 35000,
          minimum_order_quantity: 1,
          is_available: true,
          stock_status: 'in_stock',
          image: null,
          origin: 'Côte d\'Ivoire',
          brand: '',
          certifications: ['Halal'],
        },
        {
          id: '4',
          supplier: '2',
          supplier_name: 'Ivoire Viandes',
          category: '2',
          category_name: 'Viande et Volaille',
          name: 'Boeuf (carton 20kg)',
          description: 'Viande de boeuf premium',
          unit: 'kg',
          unit_size: 20,
          price: 120000,
          minimum_order_quantity: 1,
          is_available: true,
          stock_status: 'low_stock',
          image: null,
          origin: 'Côte d\'Ivoire',
          brand: '',
          certifications: ['Halal'],
        },
        {
          id: '5',
          supplier: '3',
          supplier_name: 'San-Pédro Pêche',
          category: '3',
          category_name: 'Fruits de Mer',
          name: 'Capitaine (caisse 10kg)',
          description: 'Capitaine frais du jour',
          unit: 'kg',
          unit_size: 10,
          price: 85000,
          minimum_order_quantity: 1,
          is_available: true,
          stock_status: 'in_stock',
          image: null,
          origin: 'San-Pédro',
          brand: '',
          certifications: [],
        },
      ]);

      // Mock orders
      setOrders([
        {
          id: '1',
          order_number: 'SO-20250201-0001',
          supplier_name: 'Marché d\'Adjamé',
          status: 'delivered',
          payment_status: 'paid',
          total: 165000,
          item_count: 5,
          expected_delivery: '2025-02-01',
          created_at: '2025-01-30T10:00:00Z',
        },
        {
          id: '2',
          order_number: 'SO-20250203-0002',
          supplier_name: 'Ivoire Viandes',
          status: 'processing',
          payment_status: 'pending',
          total: 275000,
          item_count: 3,
          expected_delivery: '2025-02-05',
          created_at: '2025-02-03T14:30:00Z',
        },
      ]);

      // Mock favorites
      setFavorites([
        {
          id: '1',
          supplier: suppliers[0] || {
            id: '1',
            name: 'Marché d\'Adjamé',
            slug: 'marche-adjame',
            description: 'Grossiste en fruits et légumes frais',
            supplier_type: 'wholesaler',
            city: 'Abidjan',
            logo: null,
            verification_status: 'verified',
            minimum_order_value: 50000,
            lead_time_days: 1,
            average_rating: 4.5,
            review_count: 28,
            product_count: 156,
            is_featured: true,
          },
          notes: 'Bon rapport qualité-prix pour les légumes',
          created_at: '2025-01-15T00:00:00Z',
        },
      ]);

      // Mock cart
      setCarts([]);
      setCartTotal(0);

    } catch (error) {
      console.error('Failed to load marketplace data:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredProducts = products.filter(product => {
    if (selectedCategory && product.category !== selectedCategory) return false;
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      return (
        product.name.toLowerCase().includes(query) ||
        product.supplier_name.toLowerCase().includes(query)
      );
    }
    return true;
  }).sort((a, b) => {
    switch (sortBy) {
      case 'price':
        return a.price - b.price;
      case '-price':
        return b.price - a.price;
      case '-name':
        return b.name.localeCompare(a.name);
      default:
        return a.name.localeCompare(b.name);
    }
  });

  const filteredOrders = orders.filter(order => {
    switch (orderFilter) {
      case 'active':
        return ['submitted', 'confirmed', 'processing', 'shipped'].includes(order.status);
      case 'completed':
        return order.status === 'delivered';
      case 'cancelled':
        return order.status === 'cancelled';
      default:
        return true;
    }
  });

  const addToCart = (product: Product) => {
    // Mock add to cart
    alert(`Added ${product.name} to cart`);
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft':
        return 'bg-gray-100 text-gray-700';
      case 'submitted':
        return 'bg-blue-100 text-blue-700';
      case 'confirmed':
        return 'bg-indigo-100 text-indigo-700';
      case 'processing':
        return 'bg-yellow-100 text-yellow-700';
      case 'shipped':
        return 'bg-purple-100 text-purple-700';
      case 'delivered':
        return 'bg-emerald-100 text-emerald-700';
      case 'cancelled':
        return 'bg-red-100 text-red-700';
      default:
        return 'bg-gray-100 text-gray-700';
    }
  };

  const renderBrowse = () => (
    <div className="space-y-6">
      {/* Search and Filters */}
      <div className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1 relative">
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder={t('search.placeholder')}
              className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
            />
            <svg className="w-5 h-5 text-gray-400 absolute left-3 top-2.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            className="px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
          >
            <option value="">{t('categories.all')}</option>
            {categories.map(cat => (
              <option key={cat.id} value={cat.id}>{cat.icon} {cat.name}</option>
            ))}
          </select>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="px-3 py-2 border border-gray-200 rounded-lg focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500"
          >
            <option value="name">{t('search.sortOptions.name')}</option>
            <option value="-name">{t('search.sortOptions.nameDesc')}</option>
            <option value="price">{t('search.sortOptions.price')}</option>
            <option value="-price">{t('search.sortOptions.priceDesc')}</option>
          </select>
        </div>
      </div>

      {/* Categories */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {categories.map(cat => (
          <button
            key={cat.id}
            onClick={() => setSelectedCategory(selectedCategory === cat.id ? '' : cat.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-full whitespace-nowrap transition-colors ${
              selectedCategory === cat.id
                ? 'bg-emerald-100 text-emerald-700 border-emerald-200'
                : 'bg-white text-gray-600 border-gray-200 hover:bg-gray-50'
            } border`}
          >
            <span>{cat.icon}</span>
            <span>{cat.name}</span>
            <span className="text-xs text-gray-400">({cat.product_count})</span>
          </button>
        ))}
      </div>

      {/* Featured Suppliers */}
      <div>
        <h3 className="font-semibold text-gray-900 mb-4">Fournisseurs en Vedette</h3>
        <div className="grid md:grid-cols-3 gap-4">
          {suppliers.filter(s => s.is_featured).map(supplier => (
            <div key={supplier.id} className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
              <div className="flex items-start gap-3">
                <div className="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center text-emerald-600 font-bold text-lg">
                  {supplier.name.charAt(0)}
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-2">
                    <h4 className="font-medium text-gray-900">{supplier.name}</h4>
                    {supplier.verification_status === 'verified' && (
                      <svg className="w-4 h-4 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                      </svg>
                    )}
                  </div>
                  <p className="text-sm text-gray-500">{supplier.city}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <div className="flex items-center text-yellow-500">
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                      <span className="text-sm ml-1">{supplier.average_rating}</span>
                    </div>
                    <span className="text-xs text-gray-400">({supplier.review_count} {t('supplier.reviews')})</span>
                  </div>
                </div>
              </div>
              <div className="mt-3 flex items-center justify-between text-sm">
                <span className="text-gray-500">{t('supplier.minOrder')}: {formatCurrency(supplier.minimum_order_value)}</span>
                <button className="text-emerald-600 hover:text-emerald-700 font-medium">
                  {t('supplier.viewProducts')} →
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Products Grid */}
      <div>
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-semibold text-gray-900">{t('search.results', { count: filteredProducts.length })}</h3>
        </div>
        {filteredProducts.length === 0 ? (
          <div className="bg-white rounded-xl p-8 text-center border border-gray-100">
            <div className="text-gray-400 mb-2">
              <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
              </svg>
            </div>
            <p className="text-gray-500">{t('search.noResults')}</p>
            <p className="text-sm text-gray-400 mt-1">{t('search.noResultsDesc')}</p>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredProducts.map(product => (
              <div key={product.id} className="bg-white rounded-xl p-4 shadow-sm border border-gray-100 hover:shadow-md transition-shadow">
                <div className="aspect-video bg-gray-100 rounded-lg mb-3 flex items-center justify-center">
                  {product.image ? (
                    <img src={product.image} alt={product.name} className="w-full h-full object-cover rounded-lg" />
                  ) : (
                    <span className="text-4xl">{CATEGORY_ICONS[categories.find(c => c.id === product.category)?.slug || 'dryGoods'] || '📦'}</span>
                  )}
                </div>
                <div className="flex items-start justify-between mb-2">
                  <div>
                    <h4 className="font-medium text-gray-900">{product.name}</h4>
                    <p className="text-sm text-gray-500">{product.supplier_name}</p>
                  </div>
                  {product.stock_status === 'low_stock' && (
                    <span className="text-xs px-2 py-1 bg-yellow-100 text-yellow-700 rounded-full">{t('product.lowStock')}</span>
                  )}
                  {product.stock_status === 'out_of_stock' && (
                    <span className="text-xs px-2 py-1 bg-red-100 text-red-700 rounded-full">{t('product.outOfStock')}</span>
                  )}
                </div>
                {product.certifications.length > 0 && (
                  <div className="flex gap-1 mb-2">
                    {product.certifications.map(cert => (
                      <span key={cert} className="text-xs px-2 py-0.5 bg-emerald-100 text-emerald-700 rounded-full">{cert}</span>
                    ))}
                  </div>
                )}
                <div className="flex items-center justify-between mt-3">
                  <div>
                    <div className="font-bold text-emerald-600">{formatCurrency(product.price)}</div>
                    <div className="text-xs text-gray-400">/ {product.unit_size}{product.unit}</div>
                  </div>
                  <button
                    onClick={() => addToCart(product)}
                    disabled={product.stock_status === 'out_of_stock'}
                    className="px-4 py-2 bg-emerald-600 text-white text-sm rounded-lg hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {t('product.addToCart')}
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );

  const renderOrders = () => (
    <div className="space-y-4">
      {/* Filter tabs */}
      <div className="flex gap-2">
        {(['all', 'active', 'completed', 'cancelled'] as OrderFilter[]).map(filter => (
          <button
            key={filter}
            onClick={() => setOrderFilter(filter)}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              orderFilter === filter
                ? 'bg-emerald-100 text-emerald-700'
                : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
            }`}
          >
            {t(`orders.filter.${filter}`)}
          </button>
        ))}
      </div>

      {/* Orders list */}
      {filteredOrders.length === 0 ? (
        <div className="bg-white rounded-xl p-8 text-center border border-gray-100">
          <div className="text-gray-400 mb-2">
            <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <p className="text-gray-500">{t('orders.noOrders')}</p>
          <p className="text-sm text-gray-400 mt-1">{t('orders.noOrdersDesc')}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filteredOrders.map(order => (
            <div key={order.id} className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <div className="font-medium text-gray-900">{t('order.orderNumber')}{order.order_number}</div>
                  <div className="text-sm text-gray-500">{order.supplier_name}</div>
                </div>
                <span className={`px-3 py-1 text-sm font-medium rounded-full ${getStatusColor(order.status)}`}>
                  {t(`order.status.${order.status}`)}
                </span>
              </div>
              <div className="flex items-center justify-between text-sm">
                <div className="text-gray-500">
                  {t('order.placed')}: {formatDate(order.created_at)}
                </div>
                <div className="text-gray-500">
                  {order.item_count} {t('order.items')}
                </div>
                <div className="font-medium text-gray-900">
                  {formatCurrency(order.total)}
                </div>
              </div>
              {order.expected_delivery && (
                <div className="mt-2 text-sm text-emerald-600">
                  {t('order.expectedDelivery')}: {formatDate(order.expected_delivery)}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderFavorites = () => (
    <div className="space-y-4">
      {favorites.length === 0 ? (
        <div className="bg-white rounded-xl p-8 text-center border border-gray-100">
          <div className="text-gray-400 mb-2">
            <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
            </svg>
          </div>
          <p className="text-gray-500">{t('favorites.noFavorites')}</p>
          <p className="text-sm text-gray-400 mt-1">{t('favorites.noFavoritesDesc')}</p>
        </div>
      ) : (
        <div className="grid md:grid-cols-2 gap-4">
          {favorites.map(fav => (
            <div key={fav.id} className="bg-white rounded-xl p-4 shadow-sm border border-gray-100">
              <div className="flex items-start gap-3">
                <div className="w-12 h-12 bg-emerald-100 rounded-lg flex items-center justify-center text-emerald-600 font-bold text-lg">
                  {fav.supplier.name.charAt(0)}
                </div>
                <div className="flex-1">
                  <h4 className="font-medium text-gray-900">{fav.supplier.name}</h4>
                  <p className="text-sm text-gray-500">{fav.supplier.city}</p>
                  <div className="flex items-center gap-2 mt-1">
                    <div className="flex items-center text-yellow-500">
                      <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M9.049 2.927c.3-.921 1.603-.921 1.902 0l1.07 3.292a1 1 0 00.95.69h3.462c.969 0 1.371 1.24.588 1.81l-2.8 2.034a1 1 0 00-.364 1.118l1.07 3.292c.3.921-.755 1.688-1.54 1.118l-2.8-2.034a1 1 0 00-1.175 0l-2.8 2.034c-.784.57-1.838-.197-1.539-1.118l1.07-3.292a1 1 0 00-.364-1.118L2.98 8.72c-.783-.57-.38-1.81.588-1.81h3.461a1 1 0 00.951-.69l1.07-3.292z" />
                      </svg>
                      <span className="text-sm ml-1">{fav.supplier.average_rating}</span>
                    </div>
                  </div>
                </div>
                <button className="text-red-500 hover:text-red-600">
                  <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z" clipRule="evenodd" />
                  </svg>
                </button>
              </div>
              {fav.notes && (
                <div className="mt-3 p-2 bg-gray-50 rounded-lg text-sm text-gray-600">
                  <span className="font-medium">{t('favorites.notes')}:</span> {fav.notes}
                </div>
              )}
              <div className="mt-3 flex gap-2">
                <button className="flex-1 px-3 py-2 bg-emerald-600 text-white text-sm rounded-lg hover:bg-emerald-700">
                  {t('supplier.viewProducts')}
                </button>
                <button className="px-3 py-2 border border-gray-200 text-gray-600 text-sm rounded-lg hover:bg-gray-50">
                  {t('supplier.contact')}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderCart = () => (
    <div className="space-y-4">
      {carts.length === 0 ? (
        <div className="bg-white rounded-xl p-8 text-center border border-gray-100">
          <div className="text-gray-400 mb-2">
            <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 3h2l.4 2M7 13h10l4-8H5.4M7 13L5.4 5M7 13l-2.293 2.293c-.63.63-.184 1.707.707 1.707H17m0 0a2 2 0 100 4 2 2 0 000-4zm-8 2a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
          </div>
          <p className="text-gray-500">{t('cart.empty')}</p>
          <p className="text-sm text-gray-400 mt-1">{t('cart.emptyDesc')}</p>
          <button
            onClick={() => setActiveTab('browse')}
            className="mt-4 px-4 py-2 bg-emerald-600 text-white rounded-lg hover:bg-emerald-700"
          >
            {t('cart.continueShopping')}
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          {carts.map(cart => (
            <div key={cart.id} className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
              <div className="p-4 border-b border-gray-100 bg-gray-50">
                <div className="flex items-center justify-between">
                  <div className="font-medium text-gray-900">{cart.supplier.name}</div>
                  <button className="text-sm text-red-600 hover:text-red-700">{t('cart.clear')}</button>
                </div>
              </div>
              <div className="divide-y divide-gray-100">
                {cart.items.map(item => (
                  <div key={item.id} className="p-4 flex items-center gap-4">
                    <div className="flex-1">
                      <div className="font-medium text-gray-900">{item.product.name}</div>
                      <div className="text-sm text-gray-500">{formatCurrency(item.unit_price)} x {item.quantity}</div>
                    </div>
                    <div className="font-medium text-gray-900">{formatCurrency(item.line_total)}</div>
                    <button className="text-red-500 hover:text-red-600">
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                      </svg>
                    </button>
                  </div>
                ))}
              </div>
              <div className="p-4 border-t border-gray-100 bg-gray-50">
                <div className="flex items-center justify-between mb-3">
                  <span className="text-gray-600">{t('cart.subtotal')}</span>
                  <span className="font-bold text-gray-900">{formatCurrency(cart.total)}</span>
                </div>
                <button className="w-full px-4 py-3 bg-emerald-600 text-white font-medium rounded-lg hover:bg-emerald-700">
                  {t('cart.checkout')}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );

  const renderContent = () => {
    if (loading) {
      return (
        <div className="flex items-center justify-center py-12">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-600" />
        </div>
      );
    }

    switch (activeTab) {
      case 'browse':
        return renderBrowse();
      case 'orders':
        return renderOrders();
      case 'favorites':
        return renderFavorites();
      case 'cart':
        return renderCart();
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 pb-8">
      {/* Header */}
      <div className="bg-white border-b border-gray-100">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <h1 className="text-2xl font-bold text-gray-900">{t('title')}</h1>
          <p className="text-gray-500 mt-1">{t('subtitle')}</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 py-6">
        {/* Tabs */}
        <div className="flex gap-2 mb-6">
          {tabs.map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                activeTab === tab
                  ? 'bg-emerald-100 text-emerald-700'
                  : 'bg-white text-gray-600 hover:bg-gray-50 border border-gray-200'
              }`}
            >
              {TAB_ICONS[tab]}
              {t(`tabs.${tab}`)}
              {tab === 'cart' && carts.length > 0 && (
                <span className="ml-1 px-2 py-0.5 bg-emerald-600 text-white text-xs rounded-full">
                  {carts.reduce((sum, cart) => sum + cart.item_count, 0)}
                </span>
              )}
            </button>
          ))}
        </div>

        {/* Content */}
        {renderContent()}
      </div>
    </div>
  );
}
