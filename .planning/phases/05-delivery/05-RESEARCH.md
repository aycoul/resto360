# Phase 5: Delivery - Research

**Researched:** 2026-02-04
**Domain:** Delivery Management with Real-Time GPS Tracking, Mobile Apps, and Geospatial Zones
**Confidence:** HIGH

## Summary

This phase implements end-to-end delivery management for restaurants in Ivory Coast, including polygon-based delivery zones, driver management, real-time GPS tracking, automatic driver assignment, and mobile apps for drivers and customers. The core technical challenges are: (1) geospatial queries for zone containment and nearest-driver calculations, (2) real-time location streaming via WebSocket, and (3) cross-platform mobile apps with background location tracking.

The standard approach uses **GeoDjango with PostGIS** for all spatial operations (zone polygon storage, point-in-polygon queries, distance calculations), **Django Channels** (already in project) for real-time driver location broadcasting, and **React Native with Expo** for driver and customer mobile apps. The Expo managed workflow supports background location tracking with `expo-location` and `expo-task-manager`, though some Android device manufacturers require special battery optimization handling.

**Primary recommendation:** Use PostGIS `geography` type for all location data (lat/lng in meters), GeoDjango's `PolygonField` for zones, and `ST_DWithin` / `ST_Distance` for driver assignment. For mobile apps, use development builds (not Expo Go) as react-native-maps with Google Maps is required for proper map rendering.

## Standard Stack

The established libraries/tools for this domain:

### Core Backend (Geospatial)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| GeoDjango | Built-in | Spatial data types and queries | Django's official geographic framework |
| PostGIS | 3.4+ | PostgreSQL spatial extension | Industry standard for geospatial databases |
| django-rest-framework-gis | 1.1+ | GeoJSON serialization for DRF | GeoFeatureModelSerializer for proper GeoJSON output |
| GDAL | 3.6+ | Geospatial abstraction library | Required by GeoDjango for spatial transformations |

### Core Backend (Real-Time)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Django Channels | 4.3.2 | WebSocket for location updates | Already in project from Phase 2 |
| channels-redis | 4.x | Channel layer backend | Already in project for kitchen display |

### Core Mobile (React Native/Expo)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| expo | SDK 52+ | React Native framework | Project decision (mobile stack) |
| expo-location | 19.x | GPS and location services | Background location, permissions handling |
| expo-task-manager | 12.x | Background task execution | Required for background GPS updates |
| react-native-maps | 1.20.1+ | Map display with markers/polylines | Standard map component for Expo |
| expo-image-picker | 16.x | Photo capture for proof of delivery | Camera access and photo library |
| react-native-signature-canvas | 6.x | Customer signature capture | Touch signature with WebView canvas |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| expo-router | 4.x | File-based navigation | Tab + stack navigation for mobile apps |
| expo-linking | 7.x | Phone calls/SMS to customers | Driver-customer communication |
| Google Routes API | v2 | ETA calculation | Distance/duration for delivery estimates |
| OpenStreetMap/Nominatim | N/A | Geocoding (free alternative) | If Google API costs too high |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| PostGIS geography | PostGIS geometry with SRID 4326 | Geography is simpler for global lat/lng; geometry faster for local projections |
| Google Routes API | OSRM (Open Source Routing Machine) | Free but requires self-hosting; Google is more accurate for West Africa |
| react-native-maps | expo-maps | expo-maps is alpha, requires iOS 17+, less mature |
| react-native-signature-canvas | react-native-signature-capture-view | Both work; signature-canvas has more active maintenance |

**Installation (Backend):**
```bash
# PostGIS extension (requires system-level install)
# Ubuntu/Debian: apt install postgis postgresql-15-postgis-3
# Render.com: Use PostGIS-enabled PostgreSQL addon

# Python dependencies
pip install djangorestframework-gis
```

**Installation (Mobile):**
```bash
# Driver app and Customer app
npx expo install expo-location expo-task-manager react-native-maps expo-image-picker expo-linking react-native-signature-canvas react-native-webview
```

## Architecture Patterns

### Recommended Backend Structure
```
apps/api/apps/delivery/
    __init__.py
    apps.py
    models.py              # DeliveryZone, Driver, Delivery models
    serializers.py         # GeoJSON serializers for zones, driver location
    views.py               # Zone CRUD, driver management, delivery tracking
    urls.py                # Route configuration
    admin.py               # Django admin with map widgets
    services/
        __init__.py
        assignment.py      # Nearest driver algorithm
        eta.py             # ETA calculation service
        tracking.py        # Location update processing
    consumers.py           # WebSocket consumers for driver/customer location
    routing.py             # WebSocket URL routing
    tasks.py               # Celery tasks (ETA recalculation, stale driver cleanup)
    migrations/
    tests/
        __init__.py
        conftest.py
        factories.py
        test_zones.py
        test_assignment.py
        test_tracking.py
```

### Recommended Mobile Structure (Driver App)
```
apps/mobile/apps/driver/
    app/
        _layout.tsx           # Root stack navigator
        (auth)/
            _layout.tsx       # Auth flow layout
            login.tsx         # Driver login
        (main)/
            _layout.tsx       # Tab navigator
            index.tsx         # Dashboard (today's stats)
            deliveries/
                _layout.tsx   # Deliveries stack
                index.tsx     # Active deliveries list
                [id].tsx      # Single delivery details
            profile.tsx       # Driver profile, availability toggle
        delivery/
            [id]/
                navigate.tsx  # Navigation screen
                confirm.tsx   # Delivery confirmation (photo/signature)
    components/
        DeliveryCard.tsx
        MapWithRoute.tsx
        AvailabilityToggle.tsx
        SignatureCapture.tsx
        PhotoCapture.tsx
    hooks/
        useLocation.ts        # Background location hook
        useDeliveries.ts      # Active deliveries query
        useWebSocket.ts       # Real-time updates
    services/
        api.ts                # API client
        location.ts           # Background location task
    stores/
        auth.ts               # Zustand auth store
    app.json                  # Expo config
    package.json
```

### Recommended Mobile Structure (Customer App)
```
apps/mobile/apps/customer/
    app/
        _layout.tsx           # Root layout
        (auth)/
            login.tsx
            register.tsx
        (main)/
            _layout.tsx       # Tab navigator
            menu/
                index.tsx     # Restaurant menu (from Phase 2)
            orders/
                index.tsx     # Order history
                [id].tsx      # Order details
            track/
                [id].tsx      # Real-time delivery tracking
            profile.tsx
    components/
        OrderCard.tsx
        TrackingMap.tsx
        DriverInfo.tsx
    hooks/
        useOrder.ts
        useTracking.ts
    app.json
    package.json
```

### Pattern 1: Delivery Zone with PostGIS Polygon
**What:** Store delivery zones as polygon geometries with associated fees
**When to use:** Zone configuration, delivery fee calculation, zone containment checks
**Example:**
```python
# apps/delivery/models.py
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from apps.core.models import TenantModel

class DeliveryZone(TenantModel):
    """Delivery zone with polygon boundary."""

    name = models.CharField(max_length=100)
    # Using geography=True for lat/lng coordinates with distance in meters
    polygon = gis_models.PolygonField(geography=True, srid=4326)
    delivery_fee = models.PositiveIntegerField(
        help_text="Delivery fee in XOF"
    )
    minimum_order = models.PositiveIntegerField(
        default=0,
        help_text="Minimum order amount in XOF"
    )
    estimated_time_minutes = models.PositiveIntegerField(
        default=30,
        help_text="Base estimated delivery time"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def contains_point(self, lat: float, lng: float) -> bool:
        """Check if a point is within this zone."""
        point = Point(lng, lat, srid=4326)  # Note: lng, lat order for GIS
        return self.polygon.contains(point)

    @classmethod
    def find_zone_for_location(cls, restaurant, lat: float, lng: float):
        """Find the delivery zone containing a location."""
        point = Point(lng, lat, srid=4326)
        return cls.objects.filter(
            restaurant=restaurant,
            polygon__contains=point,
            is_active=True
        ).first()
```

### Pattern 2: Driver with Real-Time Location
**What:** Driver model with current GPS location and availability status
**When to use:** Driver tracking, assignment, availability management
**Example:**
```python
# apps/delivery/models.py
from django.contrib.gis.db import models as gis_models
from django.contrib.gis.geos import Point
from django.db.models import F
from django.db.models.functions import Cast

class Driver(TenantModel):
    """Delivery driver with location tracking."""

    user = models.OneToOneField(
        'authentication.User',
        on_delete=models.CASCADE,
        related_name='driver_profile'
    )
    phone = models.CharField(max_length=20)
    vehicle_type = models.CharField(
        max_length=20,
        choices=[
            ('motorcycle', 'Motorcycle'),
            ('bicycle', 'Bicycle'),
            ('car', 'Car'),
            ('foot', 'On Foot'),
        ],
        default='motorcycle'
    )

    # Availability
    is_available = models.BooleanField(default=False)
    went_online_at = models.DateTimeField(null=True, blank=True)

    # Current location (updated in real-time)
    current_location = gis_models.PointField(
        geography=True,
        srid=4326,
        null=True,
        blank=True
    )
    location_updated_at = models.DateTimeField(null=True, blank=True)

    # Stats
    total_deliveries = models.PositiveIntegerField(default=0)
    average_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=5.00
    )

    all_objects = models.Manager()
    objects = TenantManager()

    def update_location(self, lat: float, lng: float):
        """Update driver's current location."""
        from django.utils import timezone
        self.current_location = Point(lng, lat, srid=4326)
        self.location_updated_at = timezone.now()
        self.save(update_fields=['current_location', 'location_updated_at'])

    def go_online(self):
        """Mark driver as available for deliveries."""
        from django.utils import timezone
        self.is_available = True
        self.went_online_at = timezone.now()
        self.save(update_fields=['is_available', 'went_online_at'])

    def go_offline(self):
        """Mark driver as unavailable."""
        self.is_available = False
        self.save(update_fields=['is_available'])
```

### Pattern 3: Nearest Driver Assignment Algorithm
**What:** Find and assign the nearest available driver to a delivery
**When to use:** Automatic driver assignment when order is ready for delivery
**Example:**
```python
# apps/delivery/services/assignment.py
from django.contrib.gis.db.models.functions import Distance
from django.contrib.gis.geos import Point
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from apps.delivery.models import Driver, Delivery

def find_nearest_available_driver(
    restaurant,
    pickup_location: Point,
    max_distance_km: float = 10.0,
    max_stale_minutes: int = 5
) -> Driver | None:
    """
    Find the nearest available driver within range.

    Args:
        restaurant: The restaurant (for tenant filtering)
        pickup_location: Point where driver needs to go
        max_distance_km: Maximum distance in kilometers
        max_stale_minutes: Reject drivers with stale location

    Returns:
        The nearest available Driver, or None if none available
    """
    # Only consider drivers with recent location updates
    stale_threshold = timezone.now() - timedelta(minutes=max_stale_minutes)

    # Find available drivers ordered by distance
    drivers = Driver.objects.filter(
        restaurant=restaurant,
        is_available=True,
        current_location__isnull=False,
        location_updated_at__gte=stale_threshold
    ).annotate(
        distance=Distance('current_location', pickup_location)
    ).filter(
        # ST_DWithin for efficient spatial index usage
        current_location__dwithin=(pickup_location, max_distance_km * 1000)  # meters
    ).order_by('distance')

    # Return first (nearest) driver, or None
    return drivers.first()


@transaction.atomic
def assign_driver_to_delivery(delivery_id: int) -> Delivery | None:
    """
    Assign the nearest available driver to a delivery.

    Uses select_for_update to prevent race conditions.
    """
    delivery = Delivery.objects.select_for_update().get(id=delivery_id)

    if delivery.driver is not None:
        return delivery  # Already assigned

    if delivery.status != 'pending_assignment':
        return None  # Wrong status

    # Get pickup location from restaurant
    pickup_location = Point(
        delivery.order.restaurant.longitude,
        delivery.order.restaurant.latitude,
        srid=4326
    )

    driver = find_nearest_available_driver(
        restaurant=delivery.restaurant,
        pickup_location=pickup_location
    )

    if driver is None:
        return None  # No driver available

    # Assign driver and update status
    delivery.driver = driver
    delivery.status = 'assigned'
    delivery.assigned_at = timezone.now()
    delivery.save()

    # Mark driver as busy (not available for other deliveries)
    driver.is_available = False
    driver.save(update_fields=['is_available'])

    return delivery
```

### Pattern 4: WebSocket Consumer for Driver Location Updates
**What:** Real-time GPS location streaming from drivers to kitchen/customers
**When to use:** Driver app sends location updates, customer app receives them
**Example:**
```python
# apps/delivery/consumers.py
import json
from channels.generic.websocket import AsyncJsonWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone

class DriverLocationConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket for driver location updates.

    Driver connects and sends location updates.
    Kitchen and customers subscribe to receive updates.
    """

    async def connect(self):
        # Authenticate via JWT in query string (same as kitchen display)
        self.user = self.scope.get('user')
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        self.driver_id = self.scope['url_route']['kwargs'].get('driver_id')
        self.group_name = f'driver_location_{self.driver_id}'

        # Add to driver location group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    async def receive_json(self, content):
        """Handle incoming location update from driver."""
        msg_type = content.get('type')

        if msg_type == 'location_update':
            lat = content.get('lat')
            lng = content.get('lng')
            accuracy = content.get('accuracy')
            heading = content.get('heading')

            # Save to database
            await self.save_driver_location(lat, lng)

            # Broadcast to all subscribers
            await self.channel_layer.group_send(
                self.group_name,
                {
                    'type': 'driver_location',
                    'lat': lat,
                    'lng': lng,
                    'accuracy': accuracy,
                    'heading': heading,
                    'timestamp': timezone.now().isoformat()
                }
            )

    async def driver_location(self, event):
        """Send location update to subscribers."""
        await self.send_json({
            'type': 'location',
            'lat': event['lat'],
            'lng': event['lng'],
            'accuracy': event.get('accuracy'),
            'heading': event.get('heading'),
            'timestamp': event['timestamp']
        })

    @database_sync_to_async
    def save_driver_location(self, lat, lng):
        """Persist driver location to database."""
        from apps.delivery.models import Driver
        try:
            driver = Driver.all_objects.get(id=self.driver_id)
            driver.update_location(lat, lng)
        except Driver.DoesNotExist:
            pass


class DeliveryTrackingConsumer(AsyncJsonWebsocketConsumer):
    """
    WebSocket for customers tracking their delivery.

    Subscribes to a specific delivery and receives driver location updates.
    """

    async def connect(self):
        self.delivery_id = self.scope['url_route']['kwargs']['delivery_id']

        # Verify customer owns this delivery
        if not await self.verify_access():
            await self.close()
            return

        # Get driver ID for this delivery
        driver_id = await self.get_delivery_driver_id()
        if driver_id:
            self.group_name = f'driver_location_{driver_id}'
            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )

        await self.accept()

    async def driver_location(self, event):
        """Forward driver location to customer."""
        await self.send_json({
            'type': 'driver_location',
            'lat': event['lat'],
            'lng': event['lng'],
            'timestamp': event['timestamp']
        })

    @database_sync_to_async
    def verify_access(self):
        # Implementation: check customer owns this delivery
        return True

    @database_sync_to_async
    def get_delivery_driver_id(self):
        from apps.delivery.models import Delivery
        try:
            delivery = Delivery.all_objects.get(id=self.delivery_id)
            return delivery.driver_id
        except Delivery.DoesNotExist:
            return None
```

### Pattern 5: Expo Background Location Task
**What:** Continuous GPS updates even when app is in background
**When to use:** Driver app needs to track location while navigating
**Example:**
```typescript
// apps/mobile/apps/driver/services/location.ts
import * as Location from 'expo-location';
import * as TaskManager from 'expo-task-manager';

const LOCATION_TASK_NAME = 'driver-location-task';

// Define the background task
TaskManager.defineTask(LOCATION_TASK_NAME, async ({ data, error }) => {
  if (error) {
    console.error('Location task error:', error);
    return;
  }

  if (data) {
    const { locations } = data as { locations: Location.LocationObject[] };
    const location = locations[0];

    if (location) {
      // Send to WebSocket or API
      await sendLocationUpdate({
        lat: location.coords.latitude,
        lng: location.coords.longitude,
        accuracy: location.coords.accuracy,
        heading: location.coords.heading,
        timestamp: location.timestamp,
      });
    }
  }
});

export async function requestLocationPermissions(): Promise<boolean> {
  // Request foreground first
  const { status: foregroundStatus } =
    await Location.requestForegroundPermissionsAsync();

  if (foregroundStatus !== 'granted') {
    return false;
  }

  // Then request background
  const { status: backgroundStatus } =
    await Location.requestBackgroundPermissionsAsync();

  return backgroundStatus === 'granted';
}

export async function startLocationTracking(): Promise<void> {
  const hasPermission = await requestLocationPermissions();
  if (!hasPermission) {
    throw new Error('Location permission not granted');
  }

  await Location.startLocationUpdatesAsync(LOCATION_TASK_NAME, {
    accuracy: Location.Accuracy.High,
    timeInterval: 5000,        // Update every 5 seconds
    distanceInterval: 10,      // Or when moved 10 meters
    foregroundService: {
      notificationTitle: 'Driver Active',
      notificationBody: 'Tracking your location for deliveries',
      notificationColor: '#4CAF50',
    },
    pausesUpdatesAutomatically: false,
    showsBackgroundLocationIndicator: true,
  });
}

export async function stopLocationTracking(): Promise<void> {
  const isTracking = await TaskManager.isTaskRegisteredAsync(LOCATION_TASK_NAME);
  if (isTracking) {
    await Location.stopLocationUpdatesAsync(LOCATION_TASK_NAME);
  }
}

async function sendLocationUpdate(location: {
  lat: number;
  lng: number;
  accuracy: number | null;
  heading: number | null;
  timestamp: number;
}): Promise<void> {
  // Send via WebSocket if connected, otherwise queue for later
  const wsClient = getWebSocketClient();
  if (wsClient && wsClient.isConnected()) {
    wsClient.send({
      type: 'location_update',
      ...location,
    });
  }
}
```

### Pattern 6: Delivery Confirmation with Photo/Signature
**What:** Capture proof of delivery (photo or signature)
**When to use:** Driver confirms delivery to customer
**Example:**
```typescript
// apps/mobile/apps/driver/app/delivery/[id]/confirm.tsx
import { useState, useRef } from 'react';
import { View, Text, TouchableOpacity, Image } from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import SignatureCanvas from 'react-native-signature-canvas';
import { useLocalSearchParams, router } from 'expo-router';

export default function ConfirmDeliveryScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [confirmationType, setConfirmationType] = useState<'photo' | 'signature'>('photo');
  const [photoUri, setPhotoUri] = useState<string | null>(null);
  const [signatureData, setSignatureData] = useState<string | null>(null);
  const signatureRef = useRef<SignatureCanvas>(null);

  const takePhoto = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      alert('Camera permission required');
      return;
    }

    const result = await ImagePicker.launchCameraAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.7,  // Compress for upload
      allowsEditing: false,
    });

    if (!result.canceled && result.assets[0]) {
      setPhotoUri(result.assets[0].uri);
    }
  };

  const handleSignature = (signature: string) => {
    // signature is base64 data URL
    setSignatureData(signature);
  };

  const confirmDelivery = async () => {
    const proofData = confirmationType === 'photo'
      ? { type: 'photo', uri: photoUri }
      : { type: 'signature', data: signatureData };

    // Upload proof and confirm delivery
    await confirmDeliveryAPI(id, proofData);
    router.replace('/(main)/deliveries');
  };

  return (
    <View style={{ flex: 1, padding: 16 }}>
      <Text style={{ fontSize: 20, fontWeight: 'bold', marginBottom: 16 }}>
        Confirm Delivery
      </Text>

      {/* Toggle between photo and signature */}
      <View style={{ flexDirection: 'row', marginBottom: 16 }}>
        <TouchableOpacity
          onPress={() => setConfirmationType('photo')}
          style={{
            flex: 1,
            padding: 12,
            backgroundColor: confirmationType === 'photo' ? '#4CAF50' : '#E0E0E0',
          }}
        >
          <Text style={{ textAlign: 'center' }}>Photo</Text>
        </TouchableOpacity>
        <TouchableOpacity
          onPress={() => setConfirmationType('signature')}
          style={{
            flex: 1,
            padding: 12,
            backgroundColor: confirmationType === 'signature' ? '#4CAF50' : '#E0E0E0',
          }}
        >
          <Text style={{ textAlign: 'center' }}>Signature</Text>
        </TouchableOpacity>
      </View>

      {confirmationType === 'photo' ? (
        <View style={{ flex: 1 }}>
          {photoUri ? (
            <Image source={{ uri: photoUri }} style={{ flex: 1 }} resizeMode="contain" />
          ) : (
            <TouchableOpacity onPress={takePhoto} style={{ flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#F5F5F5' }}>
              <Text>Tap to Take Photo</Text>
            </TouchableOpacity>
          )}
        </View>
      ) : (
        <View style={{ flex: 1, borderWidth: 1, borderColor: '#CCC' }}>
          <SignatureCanvas
            ref={signatureRef}
            onOK={handleSignature}
            onEmpty={() => setSignatureData(null)}
            descriptionText="Sign here"
            clearText="Clear"
            confirmText="Save"
            webStyle={`.m-signature-pad { box-shadow: none; border: none; }`}
          />
        </View>
      )}

      <TouchableOpacity
        onPress={confirmDelivery}
        disabled={!photoUri && !signatureData}
        style={{
          padding: 16,
          backgroundColor: (photoUri || signatureData) ? '#4CAF50' : '#BDBDBD',
          borderRadius: 8,
          marginTop: 16,
        }}
      >
        <Text style={{ color: 'white', textAlign: 'center', fontWeight: 'bold' }}>
          Confirm Delivery
        </Text>
      </TouchableOpacity>
    </View>
  );
}
```

### Anti-Patterns to Avoid
- **Using geometry instead of geography for lat/lng:** Geography type automatically uses meters for distance; geometry requires projection management
- **Polling for location updates:** Use WebSocket for real-time location, not repeated API calls
- **Expo Go for development:** react-native-maps with Google Maps requires development builds
- **Not handling stale driver locations:** Always filter out drivers with location updates older than 5 minutes
- **Synchronous driver assignment:** Use database locking to prevent race conditions when multiple orders need assignment
- **Ignoring battery optimization:** Some Android devices (Huawei, Xiaomi) kill background tasks aggressively

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Point-in-polygon checks | Custom algorithm | PostGIS `ST_Contains` | Edge cases, performance, spatial indexing |
| Distance calculations | Haversine formula | PostGIS `ST_Distance` | Already handles Earth curvature |
| Nearest neighbor search | Sort by calculated distance | PostGIS `<->` operator with index | Order of magnitude faster with spatial index |
| GeoJSON serialization | Manual dict building | django-rest-framework-gis | Proper FeatureCollection format |
| Background location | Foreground polling | expo-location + expo-task-manager | Battery efficient, works when app closed |
| Signature capture | Canvas drawing code | react-native-signature-canvas | Touch handling, export formats |
| ETA calculation | Distance / average speed | Google Routes API | Considers traffic, road types |

**Key insight:** Geospatial operations have subtle edge cases (anti-meridian crossing, polar regions, geodesic vs planar). PostGIS handles all these correctly.

## Common Pitfalls

### Pitfall 1: Longitude/Latitude Order Confusion
**What goes wrong:** Points are saved in wrong location (swapped coordinates)
**Why it happens:** GIS libraries use (lng, lat) order; humans think (lat, lng)
**How to avoid:** Always use named parameters or comments: `Point(lng, lat)  # GIS order!`
**Warning signs:** Points appearing in wrong continent, in ocean, etc.

### Pitfall 2: Android Background Location Killed by Manufacturer
**What goes wrong:** Location updates stop after app goes to background on Huawei/Xiaomi
**Why it happens:** Aggressive battery optimization kills background services
**How to avoid:**
- Use `foregroundService` in location options (shows persistent notification)
- Prompt users to disable battery optimization for app
- Use "Don't Kill My App" website guidance per manufacturer
**Warning signs:** Location works in foreground but stops in background on specific devices

### Pitfall 3: WebSocket Reconnection with Stale Token
**What goes wrong:** Driver reconnects but sends location to wrong restaurant
**Why it happens:** JWT expired during background operation, stale token cached
**How to avoid:** Refresh token before reconnecting; validate token on server for each message
**Warning signs:** Locations appearing in wrong restaurant's dashboard

### Pitfall 4: Expo Go vs Development Build for Maps
**What goes wrong:** Google Maps doesn't work or shows blank map
**Why it happens:** Expo Go SDK 53+ doesn't support Google Maps for Android
**How to avoid:** Use `npx expo prebuild` and development builds for testing maps
**Warning signs:** Apple Maps works on iOS, Android shows errors

### Pitfall 5: Race Condition in Driver Assignment
**What goes wrong:** Same driver assigned to multiple deliveries simultaneously
**Why it happens:** Two orders ready at same time, both find same nearest driver
**How to avoid:** Use `select_for_update()` on driver row during assignment; mark driver busy atomically
**Warning signs:** Driver receives multiple delivery notifications at once

### Pitfall 6: PostGIS Geography Meter Calculations
**What goes wrong:** `ST_DWithin` returns unexpected results
**Why it happens:** Geography type uses meters, but passed kilometers or degrees
**How to avoid:** Always convert to meters: `km * 1000`
**Warning signs:** Finding drivers 1000km away when expecting 10km

### Pitfall 7: Signature Canvas Not Rendering
**What goes wrong:** Signature pad shows blank or WebView errors
**Why it happens:** react-native-signature-canvas requires react-native-webview peer dependency
**How to avoid:** Install both: `npx expo install react-native-signature-canvas react-native-webview`
**Warning signs:** White screen where signature should be, WebView component errors

## Code Examples

Verified patterns from official sources:

### GeoJSON Zone Serializer
```python
# apps/delivery/serializers.py
# Source: django-rest-framework-gis documentation
from rest_framework_gis.serializers import GeoFeatureModelSerializer
from rest_framework import serializers
from .models import DeliveryZone

class DeliveryZoneSerializer(GeoFeatureModelSerializer):
    """Serialize DeliveryZone as GeoJSON Feature."""

    class Meta:
        model = DeliveryZone
        geo_field = 'polygon'
        id_field = 'id'
        fields = [
            'id', 'name', 'delivery_fee', 'minimum_order',
            'estimated_time_minutes', 'is_active'
        ]
        # Output format:
        # {
        #   "type": "Feature",
        #   "geometry": { "type": "Polygon", "coordinates": [...] },
        #   "properties": { "name": "Zone A", "delivery_fee": 1500, ... }
        # }
```

### Check Delivery Address in Zone
```python
# apps/delivery/views.py
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.gis.geos import Point

class DeliveryZoneViewSet(viewsets.ModelViewSet):

    @action(detail=False, methods=['post'])
    def check_address(self, request):
        """Check if address is within any delivery zone."""
        lat = request.data.get('lat')
        lng = request.data.get('lng')

        if not lat or not lng:
            return Response({'error': 'lat and lng required'}, status=400)

        point = Point(float(lng), float(lat), srid=4326)

        zone = DeliveryZone.objects.filter(
            restaurant=request.restaurant,
            polygon__contains=point,
            is_active=True
        ).first()

        if zone:
            return Response({
                'deliverable': True,
                'zone': DeliveryZoneSerializer(zone).data,
            })
        else:
            return Response({
                'deliverable': False,
                'message': 'Address is outside delivery area'
            })
```

### Map with Driver Marker (React Native)
```typescript
// apps/mobile/apps/customer/components/TrackingMap.tsx
// Source: react-native-maps documentation
import React, { useEffect, useState } from 'react';
import MapView, { Marker, Polyline, PROVIDER_GOOGLE } from 'react-native-maps';
import { View, StyleSheet } from 'react-native';

interface TrackingMapProps {
  driverLocation: { lat: number; lng: number } | null;
  deliveryAddress: { lat: number; lng: number };
  restaurantLocation: { lat: number; lng: number };
}

export default function TrackingMap({
  driverLocation,
  deliveryAddress,
  restaurantLocation,
}: TrackingMapProps) {
  const [region, setRegion] = useState({
    latitude: deliveryAddress.lat,
    longitude: deliveryAddress.lng,
    latitudeDelta: 0.05,
    longitudeDelta: 0.05,
  });

  // Center map when driver location updates
  useEffect(() => {
    if (driverLocation) {
      setRegion(r => ({
        ...r,
        latitude: driverLocation.lat,
        longitude: driverLocation.lng,
      }));
    }
  }, [driverLocation]);

  return (
    <View style={styles.container}>
      <MapView
        provider={PROVIDER_GOOGLE}
        style={styles.map}
        region={region}
        showsUserLocation={false}
      >
        {/* Restaurant marker */}
        <Marker
          coordinate={{
            latitude: restaurantLocation.lat,
            longitude: restaurantLocation.lng,
          }}
          title="Restaurant"
          pinColor="green"
        />

        {/* Delivery address marker */}
        <Marker
          coordinate={{
            latitude: deliveryAddress.lat,
            longitude: deliveryAddress.lng,
          }}
          title="Your Location"
          pinColor="red"
        />

        {/* Driver marker (animated) */}
        {driverLocation && (
          <Marker
            coordinate={{
              latitude: driverLocation.lat,
              longitude: driverLocation.lng,
            }}
            title="Driver"
            image={require('../assets/driver-icon.png')}
          />
        )}

        {/* Route polyline (simplified) */}
        {driverLocation && (
          <Polyline
            coordinates={[
              { latitude: driverLocation.lat, longitude: driverLocation.lng },
              { latitude: deliveryAddress.lat, longitude: deliveryAddress.lng },
            ]}
            strokeColor="#4CAF50"
            strokeWidth={4}
          />
        )}
      </MapView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  map: { flex: 1 },
});
```

### Driver Phone/SMS Contact
```typescript
// apps/mobile/apps/customer/components/DriverContact.tsx
// Source: React Native Linking documentation
import { View, TouchableOpacity, Text, Linking, Platform } from 'react-native';

interface DriverContactProps {
  driverPhone: string;
  driverName: string;
}

export default function DriverContact({ driverPhone, driverName }: DriverContactProps) {

  const callDriver = () => {
    Linking.openURL(`tel:${driverPhone}`);
  };

  const messageDriver = () => {
    // iOS uses & for body separator, Android uses ?
    const separator = Platform.OS === 'ios' ? '&' : '?';
    const message = encodeURIComponent('Hi, I have a question about my delivery');
    Linking.openURL(`sms:${driverPhone}${separator}body=${message}`);
  };

  return (
    <View style={{ flexDirection: 'row', padding: 16, backgroundColor: 'white' }}>
      <View style={{ flex: 1 }}>
        <Text style={{ fontWeight: 'bold' }}>{driverName}</Text>
        <Text style={{ color: 'gray' }}>Your driver</Text>
      </View>

      <TouchableOpacity onPress={callDriver} style={{ padding: 12, marginRight: 8, backgroundColor: '#4CAF50', borderRadius: 8 }}>
        <Text style={{ color: 'white' }}>Call</Text>
      </TouchableOpacity>

      <TouchableOpacity onPress={messageDriver} style={{ padding: 12, backgroundColor: '#2196F3', borderRadius: 8 }}>
        <Text style={{ color: 'white' }}>Message</Text>
      </TouchableOpacity>
    </View>
  );
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Geometry type for lat/lng | Geography type | PostGIS standard | No projection management, meters by default |
| REST polling for location | WebSocket streaming | Industry standard | Lower latency, less server load |
| Expo Go for dev | Development builds | Expo SDK 53 | Required for Google Maps, native modules |
| Manual ETA calculation | Google Routes API | 2023+ | Traffic-aware, more accurate |
| react-native-maps 1.x | react-native-maps 1.20+ | 2024-2025 | New Architecture support |
| expo-location foreground only | Background with TaskManager | Expo SDK 50+ | Persistent tracking |

**Deprecated/outdated:**
- expo-maps: Still in alpha, requires iOS 17 minimum; use react-native-maps for now
- Geometry with SRID 4326 for distance: Use geography type for automatic meter calculations
- Expo Go for maps development: Must use development builds

## Open Questions

Things that couldn't be fully resolved:

1. **Google Routes API vs OSRM for ETA**
   - What we know: Google is more accurate in West Africa; OSRM is free but self-hosted
   - What's unclear: Google API costs for Ivory Coast volume; OSRM data quality for Abidjan
   - Recommendation: Start with Google Routes API; evaluate OSRM later if costs are concern

2. **Render.com PostGIS Support**
   - What we know: Render offers PostgreSQL but PostGIS addon availability unclear
   - What's unclear: Whether PostGIS extension can be enabled on Render PostgreSQL
   - Recommendation: Verify with Render support; may need external PostgreSQL (Supabase, Neon)

3. **react-native-maps 1.21.0 Stability**
   - What we know: Version 1.21.0 is New Architecture native but "stabilizing"
   - What's unclear: Production readiness for SDK 53
   - Recommendation: Start with 1.20.1 (SDK 52 default); upgrade when 1.21 is stable

4. **Battery Drain from Continuous GPS**
   - What we know: High accuracy GPS is power intensive
   - What's unclear: Optimal accuracy/interval tradeoff for delivery driving
   - Recommendation: Use High accuracy, 5s interval, 10m distance threshold; test on devices

## Sources

### Primary (HIGH confidence)
- [GeoDjango Model API](https://docs.djangoproject.com/en/5.1/ref/contrib/gis/model-api/) - Django official documentation
- [PostGIS ST_Distance](https://postgis.net/docs/ST_Distance.html) - PostGIS official documentation
- [PostGIS Nearest Neighbor](https://postgis.net/workshops/postgis-intro/knn.html) - PostGIS workshop
- [expo-location](https://docs.expo.dev/versions/latest/sdk/location/) - Expo official SDK documentation
- [react-native-maps](https://docs.expo.dev/versions/latest/sdk/map-view/) - Expo SDK documentation
- [Django Channels](https://channels.readthedocs.io/) - Official documentation (already used in Phase 2)

### Secondary (MEDIUM confidence)
- [django-rest-framework-gis GitHub](https://github.com/openwisp/django-rest-framework-gis) - GeoJSON serialization
- [Google Routes API](https://developers.google.com/maps/documentation/routes/compute-route-over) - ETA calculation
- [react-native-signature-canvas npm](https://www.npmjs.com/package/react-native-signature-canvas) - Signature capture
- [Expo Router patterns](https://docs.expo.dev/router/basics/common-navigation-patterns/) - Tab/stack navigation

### Tertiary (LOW confidence)
- Various Medium articles on React Native maps integration
- Community discussions on Expo background location issues
- [TestDriven.io Rideshare Course](https://testdriven.io/courses/real-time-app-with-django-channels-and-angular/) - Architecture patterns

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - GeoDjango/PostGIS well-documented, Expo Location official SDK
- Architecture: HIGH - Patterns from official docs and established rideshare implementations
- Pitfalls: MEDIUM - Based on community reports and official known issues
- Mobile specifics: MEDIUM - React Native ecosystem evolves quickly

**Research date:** 2026-02-04
**Valid until:** 2026-03-04 (30 days - mobile SDKs may update)

---

## Quick Reference for Planner

### Required pip packages
```
djangorestframework-gis>=1.1.0
# GDAL - system-level install required for GeoDjango
```

### Required npm packages (per mobile app)
```
expo-location
expo-task-manager
react-native-maps
expo-image-picker
react-native-signature-canvas
react-native-webview
expo-linking
```

### Model Hierarchy
```
Restaurant (existing)
├── DeliveryZone
│   └── polygon (PolygonField geography)
├── Driver
│   ├── current_location (PointField geography)
│   └── user (FK to User)
└── Delivery
    ├── order (FK to Order)
    ├── driver (FK to Driver)
    ├── status (FSM field)
    ├── pickup_address
    ├── delivery_address
    ├── delivery_location (PointField)
    └── proof_of_delivery (photo/signature)
```

### API Endpoints Needed
- `GET/POST /api/delivery/zones/` - Zone CRUD
- `POST /api/delivery/zones/check-address/` - Check if address is deliverable
- `GET/POST /api/delivery/drivers/` - Driver CRUD
- `POST /api/delivery/drivers/{id}/toggle-availability/` - Go online/offline
- `POST /api/delivery/drivers/{id}/location/` - Update driver location
- `GET /api/delivery/deliveries/` - List deliveries
- `GET /api/delivery/deliveries/active/` - Driver's active deliveries
- `PATCH /api/delivery/deliveries/{id}/status/` - Update delivery status
- `POST /api/delivery/deliveries/{id}/assign/` - Manual driver assignment
- `POST /api/delivery/deliveries/{id}/confirm/` - Confirm with photo/signature
- `WS /ws/driver/{driver_id}/location/` - Driver location WebSocket
- `WS /ws/delivery/{delivery_id}/track/` - Customer tracking WebSocket

### Delivery Status Flow
```
pending_assignment -> assigned -> picked_up -> en_route -> delivered
                  \-> cancelled (any state)
```
