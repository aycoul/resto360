export interface Category {
  id: string;
  name: string;
  display_order: number;
  is_visible: boolean;
  items: MenuItem[];
}

// Phase 7: Menu Metadata Types
export type AllergenType =
  | "celery"
  | "gluten"
  | "crustaceans"
  | "eggs"
  | "fish"
  | "lupin"
  | "milk"
  | "molluscs"
  | "mustard"
  | "nuts"
  | "peanuts"
  | "sesame"
  | "soya"
  | "sulphites";

export type DietaryTagType =
  | "vegan"
  | "vegetarian"
  | "gluten_free"
  | "dairy_free"
  | "halal"
  | "kosher"
  | "keto"
  | "low_carb"
  | "nut_free"
  | "organic";

export type SpiceLevel = 0 | 1 | 2 | 3 | 4;

export interface NutritionInfo {
  calories: number | null;
  protein_grams: number | null;
  carbs_grams: number | null;
  fat_grams: number | null;
  fiber_grams: number | null;
  sodium_mg: number | null;
}

export interface MenuMetadataChoice {
  value: string;
  label: string;
}

export interface MenuMetadataChoices {
  allergens: MenuMetadataChoice[];
  dietary_tags: MenuMetadataChoice[];
  spice_levels: MenuMetadataChoice[];
}

export interface MenuItem {
  id: string;
  category: string;
  category_name?: string;
  name: string;
  description: string;
  price: number;
  image?: string;
  thumbnail_url: string | null;
  is_available: boolean;
  modifiers: Modifier[];
  // Phase 7: Menu Metadata
  allergens: AllergenType[];
  allergen_display: string[];
  dietary_tags: DietaryTagType[];
  dietary_tag_display: string[];
  spice_level: SpiceLevel;
  spice_level_display: string;
  prep_time_minutes: number | null;
  ingredients: string;
  nutrition: NutritionInfo | null;
  has_nutrition_info: boolean;
}

export interface Modifier {
  id: string;
  name: string;
  required: boolean;
  max_selections: number;
  options: ModifierOption[];
}

export interface ModifierOption {
  id: string;
  name: string;
  price_adjustment: number;
  is_available: boolean;
}

export interface Order {
  id: string;
  order_number: number;
  order_type: "dine_in" | "takeout" | "delivery";
  status: "pending" | "preparing" | "ready" | "completed" | "cancelled";
  table: string | null;
  customer_name: string;
  customer_phone: string;
  notes: string;
  subtotal: number;
  total: number;
  items: OrderItem[];
  created_at: string;
}

export interface OrderItem {
  id: string;
  menu_item: string;
  menu_item_name: string;
  quantity: number;
  unit_price: number;
  notes: string;
  modifiers: OrderItemModifier[];
}

export interface OrderItemModifier {
  modifier_option: string;
  modifier_option_name: string;
  price_adjustment: number;
}

export interface CreateOrderPayload {
  order_type: "dine_in" | "takeout" | "delivery";
  table?: string;
  customer_name?: string;
  customer_phone?: string;
  notes?: string;
  items: {
    menu_item_id: string;
    quantity: number;
    notes?: string;
    modifiers: { modifier_option_id: string }[];
  }[];
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface ApiError {
  detail: string;
  code?: string;
}

// Phase 8: Menu Theme Types
export type MenuTemplate =
  | "minimalist"
  | "elegant"
  | "modern"
  | "casual"
  | "fine_dining"
  | "vibrant";

export type FontChoice =
  | "inter"
  | "playfair"
  | "roboto"
  | "lato"
  | "montserrat"
  | "merriweather"
  | "open_sans"
  | "poppins";

export type LogoPosition = "left" | "center" | "right";

export interface MenuTheme {
  id?: string;
  is_active: boolean;
  template: MenuTemplate;
  template_display?: string;
  primary_color: string;
  secondary_color: string;
  background_color: string;
  text_color: string;
  heading_font: FontChoice;
  heading_font_display?: string;
  body_font: FontChoice;
  body_font_display?: string;
  logo?: string | null;
  logo_url?: string | null;
  cover_image?: string | null;
  cover_image_url?: string | null;
  logo_position: LogoPosition;
  show_prices: boolean;
  show_descriptions: boolean;
  show_images: boolean;
  compact_mode: boolean;
}

export interface ThemeChoices {
  templates: { value: string; label: string }[];
  fonts: { value: string; label: string }[];
}

// Phase 9: AI Menu Builder Types
export interface AIJob {
  id: string;
  job_type: AIJobType;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  input_data: Record<string, unknown>;
  output_data: Record<string, unknown>;
  error_message: string;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
}

export type AIJobType =
  | 'description'
  | 'photo_analysis'
  | 'menu_ocr'
  | 'bulk_import'
  | 'translation'
  | 'price_suggestion';

export interface MenuImportBatch {
  id: string;
  source_type: 'csv' | 'excel' | 'ocr' | 'manual';
  original_filename: string;
  status: 'pending' | 'confirmed' | 'cancelled';
  items: ImportedMenuItem[];
  errors: string[];
  total_items: number;
  valid_items: number;
  created_items: number;
  created_at: string;
  confirmed_at: string | null;
}

export interface ImportedMenuItem {
  name: string;
  price: number;
  description?: string;
  category?: string;
  is_available?: boolean;
  allergens?: string[];
  dietary_tags?: string[];
  spice_level?: number;
  prep_time_minutes?: number;
  ingredients?: string;
}

export interface AIGenerateDescriptionRequest {
  item_name: string;
  category: string;
  ingredients?: string;
  cuisine_type?: string;
  language?: 'en' | 'fr';
}

export interface AIPhotoAnalysis {
  quality_score: number;
  description: string;
  suggestions: string[];
  menu_ready: 'yes' | 'no' | 'with-edits';
}

export interface AIPriceSuggestion {
  suggested_price: number;
  price_range_low: number;
  price_range_high: number;
  reasoning: string;
}

export interface AITranslationResult {
  name: string;
  description: string | null;
}

export interface AIUsageSummary {
  total_tokens: number;
  total_cost_cents: number;
  by_type: Record<AIJobType, {
    label: string;
    count: number;
    tokens: number;
    cost_cents: number;
  }>;
}

// Phase 10: Reservations Types
export type ReservationStatus =
  | 'pending'
  | 'confirmed'
  | 'seated'
  | 'completed'
  | 'cancelled'
  | 'no_show';

export type ReservationSource =
  | 'online'
  | 'phone'
  | 'walk_in'
  | 'third_party';

export interface TableConfiguration {
  id: string;
  name: string;
  capacity: number;
  min_capacity: number;
  location: string;
  is_active: boolean;
  display_order: number;
}

export interface BusinessHours {
  id: number;
  day_of_week: number;
  day_name: string;
  is_open: boolean;
  open_time: string | null;
  close_time: string | null;
  last_seating_time: string | null;
}

export interface SpecialHours {
  id: number;
  date: string;
  is_closed: boolean;
  open_time: string | null;
  close_time: string | null;
  reason: string;
}

export interface ReservationSettings {
  min_advance_hours: number;
  max_advance_days: number;
  slot_duration_minutes: number;
  default_dining_duration_minutes: number;
  max_party_size: number;
  require_phone: boolean;
  require_email: boolean;
  confirmation_required: boolean;
  cancellation_hours: number;
  no_show_threshold: number;
  confirmation_message: string;
  reminder_hours: number;
}

export interface Reservation {
  id: string;
  date: string;
  time: string;
  duration_minutes: number;
  end_time: string;
  party_size: number;
  table: string | null;
  table_name: string | null;
  customer_name: string;
  customer_phone: string;
  customer_email: string;
  status: ReservationStatus;
  status_display: string;
  source: ReservationSource;
  source_display: string;
  special_requests: string;
  occasion: string;
  confirmation_code: string;
  confirmed_at: string | null;
  seated_at: string | null;
  completed_at: string | null;
  cancelled_at: string | null;
  cancellation_reason: string;
  created_at: string;
}

export interface CreateReservationRequest {
  date: string;
  time: string;
  party_size: number;
  customer_name: string;
  customer_phone?: string;
  customer_email?: string;
  special_requests?: string;
  occasion?: string;
}

export interface AvailabilitySlot {
  time: string;
  available_tables: number;
  max_party_size: number;
}

export interface AvailabilityResponse {
  date: string;
  party_size: number;
  slots: AvailabilitySlot[];
  is_available: boolean;
}

export interface WaitlistEntry {
  id: string;
  customer_name: string;
  customer_phone: string;
  party_size: number;
  is_notified: boolean;
  is_seated: boolean;
  is_cancelled: boolean;
  estimated_wait_minutes: number | null;
  notified_at: string | null;
  seated_at: string | null;
  created_at: string;
}

export interface DailySummary {
  date: string;
  total_reservations: number;
  total_guests: number;
  confirmed: number;
  pending: number;
  seated: number;
  cancelled: number;
  no_shows: number;
}

// Phase 11: Reviews Types
export type ReviewStatus = 'pending' | 'approved' | 'rejected' | 'flagged';
export type ReviewSource = 'website' | 'qr_code' | 'email' | 'sms' | 'google';

export interface ReviewPhoto {
  id: string;
  image: string;
  image_url: string;
  caption: string;
  display_order: number;
}

export interface ReviewResponse {
  id: string;
  content: string;
  responder_name: string;
  created_at: string;
}

export interface Review {
  id: string;
  rating: number;
  title: string;
  content: string;
  reviewer_name: string;
  reviewer_email: string;
  is_verified: boolean;
  visit_date: string | null;
  food_rating: number | null;
  service_rating: number | null;
  ambiance_rating: number | null;
  value_rating: number | null;
  status: ReviewStatus;
  status_display: string;
  source: ReviewSource;
  source_display: string;
  is_featured: boolean;
  photos: ReviewPhoto[];
  response: ReviewResponse | null;
  has_response: boolean;
  created_at: string;
}

export interface ReviewSettings {
  auto_approve: boolean;
  min_rating_auto_approve: number;
  auto_request_feedback: boolean;
  request_delay_hours: number;
  request_channel: 'email' | 'sms' | 'both';
  show_reviews_on_menu: boolean;
  min_reviews_to_show: number;
  show_average_rating: boolean;
  response_template: string;
}

export interface ReviewSummary {
  total_reviews: number;
  average_rating: number;
  rating_distribution: Record<string, number>;
  avg_food_rating: number | null;
  avg_service_rating: number | null;
  avg_ambiance_rating: number | null;
  avg_value_rating: number | null;
  response_rate: number;
  last_updated: string;
}

export interface FeedbackRequest {
  id: string;
  customer_name: string;
  customer_email: string;
  customer_phone: string;
  channel: 'email' | 'sms';
  sent_at: string | null;
  opened_at: string | null;
  completed_at: string | null;
  created_at: string;
}
