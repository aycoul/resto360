---
phase: 05-delivery
plan: 03b
type: execute
wave: 4
depends_on: ["05-03"]
files_modified:
  - apps/mobile/apps/driver/app/(main)/deliveries/index.tsx
  - apps/mobile/apps/driver/app/(main)/deliveries/[id].tsx
  - apps/mobile/apps/driver/app/(main)/profile.tsx
  - apps/mobile/apps/driver/app/delivery/[id]/navigate.tsx
  - apps/mobile/apps/driver/app/delivery/[id]/confirm.tsx
  - apps/mobile/apps/driver/components/MapWithRoute.tsx
  - apps/mobile/apps/driver/components/SignatureCapture.tsx
  - apps/mobile/apps/driver/components/PhotoCapture.tsx
autonomous: false

must_haves:
  truths:
    - "Driver can navigate to pickup and delivery addresses"
    - "Driver can confirm delivery with photo or signature"
    - "Driver can see delivery details and update status"
  artifacts:
    - path: "apps/mobile/apps/driver/app/delivery/[id]/confirm.tsx"
      provides: "Delivery confirmation with photo/signature"
      contains: "SignatureCanvas"
    - path: "apps/mobile/apps/driver/app/delivery/[id]/navigate.tsx"
      provides: "Navigation screen with map"
      contains: "MapView"
    - path: "apps/mobile/apps/driver/app/(main)/deliveries/[id].tsx"
      provides: "Delivery detail with status actions"
      min_lines: 100
  key_links:
    - from: "apps/mobile/apps/driver/app/delivery/[id]/confirm.tsx"
      to: "/api/v1/delivery/deliveries/{id}/confirm/"
      via: "confirmDelivery API call"
      pattern: "api.confirmDelivery"
    - from: "apps/mobile/apps/driver/app/delivery/[id]/navigate.tsx"
      to: "expo-linking"
      via: "Open external maps app"
      pattern: "Linking.openURL"
---

<objective>
Complete driver mobile app with navigation and delivery confirmation screens

Purpose: Enable drivers to navigate to delivery addresses using external maps apps and confirm deliveries with photo or signature proof. This completes the driver mobile experience.

Output:
- Delivery list and detail screens with status actions
- Navigation screen with map and open-in-maps button
- Photo and signature capture for proof of delivery
- Profile screen with logout
</objective>

<execution_context>
@C:\Users\dell\.claude/get-shit-done/workflows/execute-plan.md
@C:\Users\dell\.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@.planning/PROJECT.md
@.planning/ROADMAP.md
@.planning/STATE.md
@.planning/phases/05-delivery/05-RESEARCH.md
@.planning/phases/05-delivery/05-03-SUMMARY.md
</context>

<tasks>

<task type="auto">
  <name>Task 1: Create delivery list, detail, and profile screens</name>
  <files>
    apps/mobile/apps/driver/app/(main)/deliveries/index.tsx
    apps/mobile/apps/driver/app/(main)/deliveries/[id].tsx
    apps/mobile/apps/driver/app/(main)/profile.tsx
  </files>
  <action>
Create apps/mobile/apps/driver/app/(main)/deliveries/index.tsx:
```tsx
/**
 * List of active deliveries.
 */
import { View, FlatList, Text, StyleSheet, RefreshControl } from 'react-native';
import { useDeliveries } from '../../../hooks/useDeliveries';
import DeliveryCard from '../../../components/DeliveryCard';

export default function DeliveriesScreen() {
  const { deliveries, loading, error, refresh } = useDeliveries();

  if (error) {
    return (
      <View style={styles.center}>
        <Text style={styles.error}>{error}</Text>
      </View>
    );
  }

  return (
    <FlatList
      data={deliveries}
      keyExtractor={(item) => item.id}
      renderItem={({ item }) => <DeliveryCard delivery={item} />}
      refreshControl={
        <RefreshControl refreshing={loading} onRefresh={refresh} />
      }
      ListEmptyComponent={
        <View style={styles.center}>
          <Text style={styles.empty}>No active deliveries</Text>
        </View>
      }
      contentContainerStyle={deliveries.length === 0 ? styles.emptyList : undefined}
    />
  );
}

const styles = StyleSheet.create({
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  error: { color: 'red' },
  empty: { color: '#999', fontSize: 16 },
  emptyList: { flex: 1 },
});
```

Create apps/mobile/apps/driver/app/(main)/deliveries/[id].tsx:
```tsx
/**
 * Delivery detail screen with status actions.
 */
import { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { useLocalSearchParams, router } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as Linking from 'expo-linking';
import { api } from '../../../services/api';
import { Delivery } from '../../../hooks/useDeliveries';

export default function DeliveryDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [delivery, setDelivery] = useState<Delivery | null>(null);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);

  const fetchDelivery = async () => {
    if (!id) return;
    try {
      setLoading(true);
      const data = await api.getDelivery(id);
      setDelivery(data);
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to load delivery');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDelivery();
  }, [id]);

  const handleStatusUpdate = async (newStatus: string) => {
    if (!delivery) return;
    setUpdating(true);
    try {
      const updated = await api.updateDeliveryStatus(delivery.id, newStatus);
      setDelivery(updated);
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to update status');
    } finally {
      setUpdating(false);
    }
  };

  const openInMaps = (lat: number, lng: number, label: string) => {
    const url = `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}&destination_place_id=${encodeURIComponent(label)}`;
    Linking.openURL(url);
  };

  const callCustomer = () => {
    if (delivery?.customer_phone) {
      Linking.openURL(`tel:${delivery.customer_phone}`);
    }
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#4CAF50" />
      </View>
    );
  }

  if (!delivery) {
    return (
      <View style={styles.center}>
        <Text>Delivery not found</Text>
      </View>
    );
  }

  const canPickUp = delivery.status === 'assigned';
  const canMarkEnRoute = delivery.status === 'picked_up';
  const canConfirm = delivery.status === 'en_route';

  return (
    <ScrollView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.orderNumber}>Order #{delivery.order_number}</Text>
        <View style={[styles.statusBadge, { backgroundColor: getStatusColor(delivery.status) }]}>
          <Text style={styles.statusText}>{getStatusLabel(delivery.status)}</Text>
        </View>
      </View>

      {/* Customer */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Customer</Text>
        <View style={styles.row}>
          <Text style={styles.label}>{delivery.customer_name}</Text>
          <TouchableOpacity onPress={callCustomer}>
            <Ionicons name="call" size={24} color="#4CAF50" />
          </TouchableOpacity>
        </View>
        <Text style={styles.phone}>{delivery.customer_phone}</Text>
      </View>

      {/* Pickup */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Pickup</Text>
        <Text style={styles.address}>{delivery.pickup_address}</Text>
        {delivery.status === 'assigned' && (
          <TouchableOpacity
            style={styles.mapButton}
            onPress={() => router.push(`/delivery/${delivery.id}/navigate?type=pickup`)}
          >
            <Ionicons name="navigate" size={20} color="white" />
            <Text style={styles.mapButtonText}>Navigate to Pickup</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Delivery */}
      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Delivery</Text>
        <Text style={styles.address}>{delivery.delivery_address}</Text>
        {delivery.delivery_notes && (
          <Text style={styles.notes}>Notes: {delivery.delivery_notes}</Text>
        )}
        {(delivery.status === 'picked_up' || delivery.status === 'en_route') && (
          <TouchableOpacity
            style={styles.mapButton}
            onPress={() => router.push(`/delivery/${delivery.id}/navigate?type=delivery`)}
          >
            <Ionicons name="navigate" size={20} color="white" />
            <Text style={styles.mapButtonText}>Navigate to Delivery</Text>
          </TouchableOpacity>
        )}
      </View>

      {/* Fee */}
      <View style={styles.section}>
        <View style={styles.row}>
          <Text style={styles.sectionTitle}>Delivery Fee</Text>
          <Text style={styles.fee}>{delivery.delivery_fee.toLocaleString()} XOF</Text>
        </View>
      </View>

      {/* Actions */}
      <View style={styles.actions}>
        {canPickUp && (
          <TouchableOpacity
            style={[styles.actionButton, styles.primaryButton]}
            onPress={() => handleStatusUpdate('picked_up')}
            disabled={updating}
          >
            <Text style={styles.actionButtonText}>
              {updating ? 'Updating...' : 'Mark as Picked Up'}
            </Text>
          </TouchableOpacity>
        )}

        {canMarkEnRoute && (
          <TouchableOpacity
            style={[styles.actionButton, styles.primaryButton]}
            onPress={() => handleStatusUpdate('en_route')}
            disabled={updating}
          >
            <Text style={styles.actionButtonText}>
              {updating ? 'Updating...' : 'Start Delivery'}
            </Text>
          </TouchableOpacity>
        )}

        {canConfirm && (
          <TouchableOpacity
            style={[styles.actionButton, styles.successButton]}
            onPress={() => router.push(`/delivery/${delivery.id}/confirm`)}
          >
            <Text style={styles.actionButtonText}>Confirm Delivery</Text>
          </TouchableOpacity>
        )}
      </View>
    </ScrollView>
  );
}

function getStatusColor(status: string): string {
  const colors: Record<string, string> = {
    assigned: '#2196F3',
    picked_up: '#FF9800',
    en_route: '#4CAF50',
    delivered: '#8BC34A',
  };
  return colors[status] || '#999';
}

function getStatusLabel(status: string): string {
  const labels: Record<string, string> = {
    assigned: 'Assigned',
    picked_up: 'Picked Up',
    en_route: 'En Route',
    delivered: 'Delivered',
  };
  return labels[status] || status;
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  header: {
    backgroundColor: 'white',
    padding: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  orderNumber: { fontSize: 24, fontWeight: 'bold' },
  statusBadge: { paddingHorizontal: 12, paddingVertical: 6, borderRadius: 16 },
  statusText: { color: 'white', fontWeight: '600' },
  section: {
    backgroundColor: 'white',
    margin: 15,
    marginBottom: 0,
    padding: 15,
    borderRadius: 12,
  },
  sectionTitle: { fontSize: 14, fontWeight: '600', color: '#666', marginBottom: 8 },
  row: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  label: { fontSize: 16, fontWeight: '600' },
  phone: { color: '#666', marginTop: 4 },
  address: { fontSize: 16 },
  notes: { color: '#666', marginTop: 8, fontStyle: 'italic' },
  fee: { fontSize: 20, fontWeight: 'bold', color: '#4CAF50' },
  mapButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2196F3',
    padding: 12,
    borderRadius: 8,
    marginTop: 12,
    justifyContent: 'center',
  },
  mapButtonText: { color: 'white', fontWeight: '600', marginLeft: 8 },
  actions: { padding: 15 },
  actionButton: { padding: 16, borderRadius: 12, alignItems: 'center', marginBottom: 10 },
  primaryButton: { backgroundColor: '#2196F3' },
  successButton: { backgroundColor: '#4CAF50' },
  actionButtonText: { color: 'white', fontSize: 16, fontWeight: 'bold' },
});
```

Create apps/mobile/apps/driver/app/(main)/profile.tsx:
```tsx
/**
 * Driver profile screen with logout.
 */
import { View, Text, StyleSheet, TouchableOpacity, Alert } from 'react-native';
import { useAuthStore } from '../../stores/auth';
import { stopLocationTracking } from '../../services/location';

export default function ProfileScreen() {
  const { user, driver, logout } = useAuthStore();

  const handleLogout = async () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: async () => {
            await stopLocationTracking();
            await logout();
          },
        },
      ]
    );
  };

  return (
    <View style={styles.container}>
      <View style={styles.section}>
        <Text style={styles.label}>Name</Text>
        <Text style={styles.value}>{user?.name || 'N/A'}</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.label}>Phone</Text>
        <Text style={styles.value}>{driver?.phone || user?.phone || 'N/A'}</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.label}>Vehicle</Text>
        <Text style={styles.value}>
          {driver?.vehicle_type || 'N/A'}
          {driver?.vehicle_plate ? ` - ${driver.vehicle_plate}` : ''}
        </Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.label}>Total Deliveries</Text>
        <Text style={styles.value}>{driver?.total_deliveries || 0}</Text>
      </View>

      <View style={styles.section}>
        <Text style={styles.label}>Rating</Text>
        <Text style={styles.value}>{driver?.average_rating?.toFixed(1) || '5.0'}</Text>
      </View>

      <TouchableOpacity style={styles.logoutButton} onPress={handleLogout}>
        <Text style={styles.logoutText}>Logout</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f5f5f5', padding: 15 },
  section: {
    backgroundColor: 'white',
    padding: 15,
    borderRadius: 12,
    marginBottom: 10,
  },
  label: { fontSize: 12, color: '#666', marginBottom: 4 },
  value: { fontSize: 16, fontWeight: '600' },
  logoutButton: {
    backgroundColor: '#F44336',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 20,
  },
  logoutText: { color: 'white', fontSize: 16, fontWeight: 'bold' },
});
```
  </action>
  <verify>
    - Delivery list shows active deliveries with refresh
    - Delivery detail shows customer info, addresses, and status actions
    - Profile screen shows driver info and logout button
  </verify>
  <done>Delivery list, detail, and profile screens created</done>
</task>

<task type="auto">
  <name>Task 2: Create navigation and confirmation screens</name>
  <files>
    apps/mobile/apps/driver/app/delivery/[id]/navigate.tsx
    apps/mobile/apps/driver/app/delivery/[id]/confirm.tsx
    apps/mobile/apps/driver/components/MapWithRoute.tsx
    apps/mobile/apps/driver/components/SignatureCapture.tsx
    apps/mobile/apps/driver/components/PhotoCapture.tsx
  </files>
  <action>
Create apps/mobile/apps/driver/app/delivery/[id]/navigate.tsx:
```tsx
/**
 * Navigation screen with map and open-in-maps button.
 */
import { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { useLocalSearchParams, router } from 'expo-router';
import * as Linking from 'expo-linking';
import MapWithRoute from '../../../components/MapWithRoute';
import { api } from '../../../services/api';
import { getCurrentLocation } from '../../../services/location';

export default function NavigateScreen() {
  const { id, type } = useLocalSearchParams<{ id: string; type: 'pickup' | 'delivery' }>();
  const [delivery, setDelivery] = useState<any>(null);
  const [currentLocation, setCurrentLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        const [deliveryData, location] = await Promise.all([
          api.getDelivery(id!),
          getCurrentLocation(),
        ]);
        setDelivery(deliveryData);
        setCurrentLocation({
          lat: location.coords.latitude,
          lng: location.coords.longitude,
        });
      } catch (error: any) {
        Alert.alert('Error', error.message || 'Failed to load data');
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [id]);

  const openInExternalMaps = () => {
    if (!delivery) return;

    const destination = type === 'pickup'
      ? { lat: delivery.pickup_lat, lng: delivery.pickup_lng, label: 'Pickup' }
      : { lat: delivery.delivery_lat, lng: delivery.delivery_lng, label: 'Delivery' };

    // Try Google Maps first, then Apple Maps
    const googleMapsUrl = `https://www.google.com/maps/dir/?api=1&destination=${destination.lat},${destination.lng}`;
    const appleMapsUrl = `http://maps.apple.com/?daddr=${destination.lat},${destination.lng}`;

    Linking.canOpenURL(googleMapsUrl).then((supported) => {
      if (supported) {
        Linking.openURL(googleMapsUrl);
      } else {
        Linking.openURL(appleMapsUrl);
      }
    });
  };

  if (loading) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#4CAF50" />
      </View>
    );
  }

  if (!delivery) {
    return (
      <View style={styles.center}>
        <Text>Delivery not found</Text>
      </View>
    );
  }

  const destination = type === 'pickup'
    ? { lat: delivery.pickup_lat || 5.33, lng: delivery.pickup_lng || -4.01 }
    : { lat: delivery.delivery_lat, lng: delivery.delivery_lng };

  return (
    <View style={styles.container}>
      <MapWithRoute
        driverLocation={currentLocation}
        deliveryLocation={destination}
      />

      <View style={styles.infoCard}>
        <Text style={styles.label}>{type === 'pickup' ? 'Pickup' : 'Delivery'} Address</Text>
        <Text style={styles.address}>
          {type === 'pickup' ? delivery.pickup_address : delivery.delivery_address}
        </Text>

        <TouchableOpacity style={styles.openMapsButton} onPress={openInExternalMaps}>
          <Text style={styles.openMapsText}>Open in Maps App</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  infoCard: {
    backgroundColor: 'white',
    padding: 20,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: -2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 5,
  },
  label: { fontSize: 12, color: '#666', marginBottom: 4 },
  address: { fontSize: 16, fontWeight: '600', marginBottom: 16 },
  openMapsButton: {
    backgroundColor: '#4CAF50',
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
  },
  openMapsText: { color: 'white', fontSize: 16, fontWeight: 'bold' },
});
```

Create apps/mobile/apps/driver/app/delivery/[id]/confirm.tsx:
```tsx
/**
 * Delivery confirmation with photo/signature.
 */
import { useState, useRef } from 'react';
import { View, Text, TextInput, TouchableOpacity, Image, StyleSheet, Alert } from 'react-native';
import { useLocalSearchParams, router } from 'expo-router';
import SignatureCanvas from 'react-native-signature-canvas';
import * as ImagePicker from 'expo-image-picker';
import { api } from '../../../services/api';

export default function ConfirmDeliveryScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [confirmationType, setConfirmationType] = useState<'photo' | 'signature'>('photo');
  const [photoUri, setPhotoUri] = useState<string | null>(null);
  const [signatureData, setSignatureData] = useState<string | null>(null);
  const [recipientName, setRecipientName] = useState('');
  const [loading, setLoading] = useState(false);
  const signatureRef = useRef<SignatureCanvas>(null);

  const takePhoto = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission needed', 'Camera permission is required');
      return;
    }

    const result = await ImagePicker.launchCameraAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      quality: 0.7,
      base64: true,
    });

    if (!result.canceled && result.assets[0]) {
      setPhotoUri(result.assets[0].uri);
    }
  };

  const handleSignature = (signature: string) => {
    setSignatureData(signature);
  };

  const confirmDelivery = async () => {
    if (!id) return;

    const proofData = confirmationType === 'photo'
      ? photoUri || ''
      : signatureData || '';

    if (!proofData) {
      Alert.alert('Error', 'Please provide proof of delivery');
      return;
    }

    setLoading(true);
    try {
      await api.confirmDelivery(id, confirmationType, proofData, recipientName);
      Alert.alert('Success', 'Delivery confirmed!', [
        { text: 'OK', onPress: () => router.replace('/(main)/deliveries') }
      ]);
    } catch (error: any) {
      Alert.alert('Error', error.message || 'Failed to confirm delivery');
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <View style={styles.tabs}>
        <TouchableOpacity
          style={[styles.tab, confirmationType === 'photo' && styles.activeTab]}
          onPress={() => setConfirmationType('photo')}
        >
          <Text style={[styles.tabText, confirmationType === 'photo' && styles.activeTabText]}>
            Photo
          </Text>
        </TouchableOpacity>
        <TouchableOpacity
          style={[styles.tab, confirmationType === 'signature' && styles.activeTab]}
          onPress={() => setConfirmationType('signature')}
        >
          <Text style={[styles.tabText, confirmationType === 'signature' && styles.activeTabText]}>
            Signature
          </Text>
        </TouchableOpacity>
      </View>

      <View style={styles.content}>
        {confirmationType === 'photo' ? (
          photoUri ? (
            <View style={styles.photoContainer}>
              <Image source={{ uri: photoUri }} style={styles.photo} />
              <TouchableOpacity style={styles.retakeButton} onPress={takePhoto}>
                <Text style={styles.retakeText}>Retake Photo</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <TouchableOpacity style={styles.placeholder} onPress={takePhoto}>
              <Text style={styles.placeholderText}>Tap to Take Photo</Text>
            </TouchableOpacity>
          )
        ) : (
          <View style={styles.signatureContainer}>
            <SignatureCanvas
              ref={signatureRef}
              onOK={handleSignature}
              onEmpty={() => setSignatureData(null)}
              descriptionText="Customer Signature"
              clearText="Clear"
              confirmText="Save"
              webStyle={`.m-signature-pad { box-shadow: none; border: 1px solid #ddd; }`}
            />
          </View>
        )}
      </View>

      <View style={styles.recipientSection}>
        <Text style={styles.inputLabel}>Recipient Name (optional)</Text>
        <TextInput
          style={styles.input}
          placeholder="Who received the delivery?"
          value={recipientName}
          onChangeText={setRecipientName}
        />
      </View>

      <TouchableOpacity
        style={[styles.button, loading && styles.buttonDisabled]}
        onPress={confirmDelivery}
        disabled={loading || (!photoUri && !signatureData)}
      >
        <Text style={styles.buttonText}>
          {loading ? 'Confirming...' : 'Confirm Delivery'}
        </Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#f5f5f5' },
  tabs: { flexDirection: 'row', marginBottom: 16 },
  tab: {
    flex: 1,
    padding: 12,
    backgroundColor: '#e0e0e0',
    alignItems: 'center',
    borderRadius: 8,
    marginHorizontal: 4,
  },
  activeTab: { backgroundColor: '#4CAF50' },
  tabText: { fontWeight: '600', color: '#666' },
  activeTabText: { color: 'white' },
  content: { flex: 1, marginBottom: 16 },
  photoContainer: { flex: 1 },
  photo: { flex: 1, borderRadius: 8 },
  retakeButton: {
    backgroundColor: '#FF9800',
    padding: 12,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 8,
  },
  retakeText: { color: 'white', fontWeight: '600' },
  placeholder: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: 'white',
    borderRadius: 8,
    borderWidth: 2,
    borderColor: '#ddd',
    borderStyle: 'dashed',
  },
  placeholderText: { color: '#999', fontSize: 16 },
  signatureContainer: {
    flex: 1,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    overflow: 'hidden',
    backgroundColor: 'white',
  },
  recipientSection: { marginBottom: 16 },
  inputLabel: { fontSize: 12, color: '#666', marginBottom: 4 },
  input: {
    backgroundColor: 'white',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#ddd',
  },
  button: {
    backgroundColor: '#4CAF50',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
  },
  buttonDisabled: { opacity: 0.7 },
  buttonText: { color: 'white', fontSize: 16, fontWeight: 'bold' },
});
```

Create apps/mobile/apps/driver/components/MapWithRoute.tsx:
```tsx
/**
 * Map component with driver location.
 */
import { View, StyleSheet } from 'react-native';
import MapView, { Marker, PROVIDER_GOOGLE } from 'react-native-maps';

interface MapWithRouteProps {
  pickupLocation?: { lat: number; lng: number };
  deliveryLocation: { lat: number; lng: number };
  driverLocation?: { lat: number; lng: number } | null;
}

export default function MapWithRoute({ pickupLocation, deliveryLocation, driverLocation }: MapWithRouteProps) {
  const region = {
    latitude: driverLocation?.lat || deliveryLocation.lat,
    longitude: driverLocation?.lng || deliveryLocation.lng,
    latitudeDelta: 0.02,
    longitudeDelta: 0.02,
  };

  return (
    <View style={styles.container}>
      <MapView provider={PROVIDER_GOOGLE} style={styles.map} region={region}>
        {pickupLocation && (
          <Marker
            coordinate={{ latitude: pickupLocation.lat, longitude: pickupLocation.lng }}
            title="Pickup"
            pinColor="green"
          />
        )}
        <Marker
          coordinate={{ latitude: deliveryLocation.lat, longitude: deliveryLocation.lng }}
          title="Delivery"
          pinColor="red"
        />
        {driverLocation && (
          <Marker
            coordinate={{ latitude: driverLocation.lat, longitude: driverLocation.lng }}
            title="You"
            pinColor="blue"
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
  </action>
  <verify>
    - Navigate screen shows map with driver and destination markers
    - Navigate screen has "Open in Maps App" button that works
    - Confirm screen has both photo and signature options
    - Photo capture works with camera
    - Signature capture saves base64 data
  </verify>
  <done>Navigation and confirmation screens with photo/signature capture created</done>
</task>

<task type="checkpoint:human-verify" gate="blocking">
  <what-built>React Native driver app with Expo - complete with navigation, map, and delivery confirmation with photo/signature</what-built>
  <how-to-verify>
1. Navigate to apps/mobile/apps/driver/
2. Run `npm install` to install dependencies
3. Run `npx expo start` to start the development server
4. Scan QR code with Expo Go (note: Google Maps won't work in Expo Go - use development build for full testing)
5. Verify:
   - Login screen appears and accepts credentials
   - After login, dashboard shows with availability toggle
   - Toggling availability starts/stops location tracking
   - Deliveries tab shows list of active deliveries
   - Tapping a delivery shows detail with status actions
   - Navigate button opens map and "Open in Maps App" works
   - Confirm delivery screen allows photo or signature capture
   - Profile tab shows driver info and logout works

6. Test on physical device (recommended):
   - Background location tracking works when online
   - Camera opens for photo capture
   - Signature canvas captures signature

Note: Full testing requires:
- Development build (not Expo Go) for Google Maps
- Backend running with driver account configured
- Google Maps API keys configured in app.json
  </how-to-verify>
  <resume-signal>Type "approved" or describe issues found</resume-signal>
</task>

</tasks>

<verification>
1. Project builds: `cd apps/mobile/apps/driver && npm install && npx expo start`
2. TypeScript compiles without errors
3. All screens render without crashes
4. Navigation flow works (login -> dashboard -> deliveries -> detail -> confirm)
5. External maps opening works on device
</verification>

<success_criteria>
- [ ] Delivery list and detail screens complete
- [ ] Navigation screen with map and external maps button
- [ ] Photo capture for proof of delivery
- [ ] Signature capture for proof of delivery
- [ ] Profile screen with logout
- [ ] Human verification of complete app functionality
</success_criteria>

<output>
After completion, create `.planning/phases/05-delivery/05-03b-SUMMARY.md`
</output>
