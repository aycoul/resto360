/**
 * Delivery detail screen with status actions.
 */
import { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Alert, ActivityIndicator } from 'react-native';
import { useLocalSearchParams, router, Stack } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as Linking from 'expo-linking';
import { api } from '../../../services/api';
import { Delivery } from '../../../hooks/useDeliveries';

type IconName = keyof typeof Ionicons.glyphMap;

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
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Failed to load delivery';
      Alert.alert('Error', message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDelivery();
  }, [id]);

  const handlePickup = async () => {
    if (!delivery) return;
    setUpdating(true);
    try {
      const updated = await api.pickupDelivery(delivery.id);
      setDelivery(updated);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Failed to update status';
      Alert.alert('Error', message);
    } finally {
      setUpdating(false);
    }
  };

  const handleStartDelivery = async () => {
    if (!delivery) return;
    setUpdating(true);
    try {
      const updated = await api.startDelivery(delivery.id);
      setDelivery(updated);
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Failed to update status';
      Alert.alert('Error', message);
    } finally {
      setUpdating(false);
    }
  };

  const callCustomer = () => {
    if (delivery?.customer_phone) {
      Linking.openURL(`tel:${delivery.customer_phone}`);
    }
  };

  if (loading) {
    return (
      <>
        <Stack.Screen options={{ title: 'Delivery Details' }} />
        <View style={styles.center}>
          <ActivityIndicator size="large" color="#4CAF50" />
        </View>
      </>
    );
  }

  if (!delivery) {
    return (
      <>
        <Stack.Screen options={{ title: 'Delivery Details' }} />
        <View style={styles.center}>
          <Text>Delivery not found</Text>
        </View>
      </>
    );
  }

  const canPickUp = delivery.status === 'assigned';
  const canMarkEnRoute = delivery.status === 'picked_up';
  const canConfirm = delivery.status === 'en_route';

  return (
    <>
      <Stack.Screen options={{ title: `Order #${delivery.order_number}` }} />
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
              <Ionicons name={'call' as IconName} size={24} color="#4CAF50" />
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
              <Ionicons name={'navigate' as IconName} size={20} color="white" />
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
              <Ionicons name={'navigate' as IconName} size={20} color="white" />
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
              onPress={handlePickup}
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
              onPress={handleStartDelivery}
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
    </>
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
