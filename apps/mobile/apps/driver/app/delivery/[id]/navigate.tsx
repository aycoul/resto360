/**
 * Navigation screen with map and open-in-maps button.
 */
import { useState, useEffect } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { useLocalSearchParams, Stack } from 'expo-router';
import * as Linking from 'expo-linking';
import MapWithRoute from '../../../components/MapWithRoute';
import { api } from '../../../services/api';
import { getCurrentLocation } from '../../../services/location';
import { Delivery } from '../../../hooks/useDeliveries';

export default function NavigateScreen() {
  const { id, type } = useLocalSearchParams<{ id: string; type: 'pickup' | 'delivery' }>();
  const [delivery, setDelivery] = useState<Delivery | null>(null);
  const [currentLocation, setCurrentLocation] = useState<{ lat: number; lng: number } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      if (!id) return;
      try {
        const [deliveryData, location] = await Promise.all([
          api.getDelivery(id),
          getCurrentLocation(),
        ]);
        setDelivery(deliveryData);
        setCurrentLocation({
          lat: location.coords.latitude,
          lng: location.coords.longitude,
        });
      } catch (error: unknown) {
        const message = error instanceof Error ? error.message : 'Failed to load data';
        Alert.alert('Error', message);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [id]);

  const openInExternalMaps = () => {
    if (!delivery) return;

    const destination = type === 'pickup'
      ? { lat: delivery.pickup_lat || 5.33, lng: delivery.pickup_lng || -4.01 }
      : { lat: delivery.delivery_lat, lng: delivery.delivery_lng };

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

  const screenTitle = type === 'pickup' ? 'Navigate to Pickup' : 'Navigate to Delivery';

  if (loading) {
    return (
      <>
        <Stack.Screen options={{ title: screenTitle }} />
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#4CAF50" />
        </View>
      </>
    );
  }

  if (!delivery) {
    return (
      <>
        <Stack.Screen options={{ title: screenTitle }} />
        <View style={styles.center}>
          <Text>Delivery not found</Text>
        </View>
      </>
    );
  }

  const destination = type === 'pickup'
    ? { lat: delivery.pickup_lat || 5.33, lng: delivery.pickup_lng || -4.01 }
    : { lat: delivery.delivery_lat, lng: delivery.delivery_lng };

  const address = type === 'pickup' ? delivery.pickup_address : delivery.delivery_address;

  return (
    <>
      <Stack.Screen options={{ title: screenTitle }} />
      <View style={styles.container}>
        <MapWithRoute
          driverLocation={currentLocation}
          deliveryLocation={destination}
        />

        <View style={styles.infoCard}>
          <Text style={styles.label}>{type === 'pickup' ? 'Pickup' : 'Delivery'} Address</Text>
          <Text style={styles.address}>{address}</Text>

          <TouchableOpacity style={styles.openMapsButton} onPress={openInExternalMaps}>
            <Text style={styles.openMapsText}>Open in Maps App</Text>
          </TouchableOpacity>
        </View>
      </View>
    </>
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
