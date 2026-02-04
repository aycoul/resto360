/**
 * Card component for displaying a delivery.
 */
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { router } from 'expo-router';
import { Delivery } from '../hooks/useDeliveries';

interface DeliveryCardProps {
  delivery: Delivery;
}

const STATUS_COLORS: Record<string, string> = {
  assigned: '#2196F3',
  picked_up: '#FF9800',
  en_route: '#4CAF50',
  pending_assignment: '#9E9E9E',
};

const STATUS_LABELS: Record<string, string> = {
  assigned: 'Assigned',
  picked_up: 'Picked Up',
  en_route: 'En Route',
  pending_assignment: 'Pending',
};

export default function DeliveryCard({ delivery }: DeliveryCardProps) {
  const statusColor = STATUS_COLORS[delivery.status] || '#999';
  const statusLabel = STATUS_LABELS[delivery.status] || delivery.status;

  const handlePress = () => {
    router.push(`/deliveries/${delivery.id}`);
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  return (
    <TouchableOpacity
      style={styles.card}
      onPress={handlePress}
      activeOpacity={0.7}
    >
      <View style={styles.header}>
        <Text style={styles.orderNumber}>Order #{delivery.order_number}</Text>
        <View style={[styles.statusBadge, { backgroundColor: statusColor }]}>
          <Text style={styles.statusText}>{statusLabel}</Text>
        </View>
      </View>

      <View style={styles.addressSection}>
        <View style={styles.addressRow}>
          <Ionicons name="restaurant" size={16} color="#4CAF50" />
          <Text style={styles.addressText} numberOfLines={1}>
            {delivery.pickup_address || 'Restaurant'}
          </Text>
        </View>
        <View style={styles.divider} />
        <View style={styles.addressRow}>
          <Ionicons name="location" size={16} color="#F44336" />
          <Text style={styles.addressText} numberOfLines={1}>
            {delivery.delivery_address}
          </Text>
        </View>
      </View>

      {delivery.delivery_notes && (
        <View style={styles.notesSection}>
          <Ionicons name="document-text-outline" size={14} color="#666" />
          <Text style={styles.notesText} numberOfLines={2}>
            {delivery.delivery_notes}
          </Text>
        </View>
      )}

      <View style={styles.footer}>
        <View style={styles.customerInfo}>
          <Ionicons name="person-outline" size={14} color="#666" />
          <Text style={styles.customer}>
            {delivery.customer_name}
          </Text>
        </View>
        <View style={styles.feeContainer}>
          <Text style={styles.fee}>{delivery.delivery_fee.toLocaleString()} XOF</Text>
        </View>
      </View>

      <View style={styles.timeRow}>
        <Ionicons name="time-outline" size={14} color="#999" />
        <Text style={styles.timeText}>
          Created: {formatTime(delivery.created_at)}
        </Text>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: 'white',
    borderRadius: 12,
    padding: 15,
    marginHorizontal: 15,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  orderNumber: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#333',
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '600',
  },
  addressSection: {
    marginBottom: 12,
  },
  addressRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 4,
  },
  addressText: {
    marginLeft: 8,
    flex: 1,
    color: '#666',
    fontSize: 14,
  },
  divider: {
    height: 12,
    width: 1,
    backgroundColor: '#ddd',
    marginLeft: 7,
    marginVertical: 2,
  },
  notesSection: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#FFF8E1',
    padding: 10,
    borderRadius: 8,
    marginBottom: 12,
  },
  notesText: {
    marginLeft: 8,
    flex: 1,
    color: '#666',
    fontSize: 13,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderTopWidth: 1,
    borderTopColor: '#eee',
    paddingTop: 12,
  },
  customerInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  customer: {
    color: '#666',
    fontSize: 14,
    marginLeft: 6,
  },
  feeContainer: {
    backgroundColor: '#E8F5E9',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 6,
  },
  fee: {
    fontWeight: 'bold',
    color: '#4CAF50',
    fontSize: 14,
  },
  timeRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 10,
  },
  timeText: {
    marginLeft: 6,
    color: '#999',
    fontSize: 12,
  },
});
