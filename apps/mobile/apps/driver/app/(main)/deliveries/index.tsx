/**
 * Deliveries list screen.
 * Shows active deliveries assigned to the driver.
 */
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  RefreshControl,
  ActivityIndicator,
} from 'react-native';
import { Stack } from 'expo-router';
import { useDeliveries, Delivery } from '../../../hooks/useDeliveries';
import DeliveryCard from '../../../components/DeliveryCard';

export default function DeliveriesScreen() {
  const { deliveries, loading, error, refresh } = useDeliveries();

  const renderItem = ({ item }: { item: Delivery }) => (
    <DeliveryCard delivery={item} />
  );

  const renderEmpty = () => {
    if (loading) {
      return (
        <View style={styles.emptyContainer}>
          <ActivityIndicator size="large" color="#4CAF50" />
        </View>
      );
    }

    if (error) {
      return (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyText}>{error}</Text>
        </View>
      );
    }

    return (
      <View style={styles.emptyContainer}>
        <Text style={styles.emptyEmoji}>📦</Text>
        <Text style={styles.emptyTitle}>No Active Deliveries</Text>
        <Text style={styles.emptyText}>
          Make sure you're online to receive new delivery assignments.
        </Text>
      </View>
    );
  };

  return (
    <>
      <Stack.Screen options={{ title: 'My Deliveries' }} />
      <View style={styles.container}>
        <FlatList
          data={deliveries}
          renderItem={renderItem}
          keyExtractor={(item) => item.id}
          contentContainerStyle={deliveries.length === 0 ? styles.emptyList : styles.list}
          ListEmptyComponent={renderEmpty}
          refreshControl={
            <RefreshControl
              refreshing={loading}
              onRefresh={refresh}
              tintColor="#4CAF50"
            />
          }
        />
      </View>
    </>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  list: {
    paddingVertical: 8,
  },
  emptyList: {
    flexGrow: 1,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyEmoji: {
    fontSize: 48,
    marginBottom: 16,
  },
  emptyTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 8,
  },
  emptyText: {
    fontSize: 14,
    color: '#666',
    textAlign: 'center',
    lineHeight: 20,
  },
});
