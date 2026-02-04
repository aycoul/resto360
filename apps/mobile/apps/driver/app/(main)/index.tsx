/**
 * Driver dashboard with availability toggle and stats.
 */
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  RefreshControl,
  Alert,
} from 'react-native';
import { useState, useEffect, useCallback } from 'react';
import { useAuthStore } from '../../stores/auth';
import { api } from '../../services/api';
import { startLocationTracking, stopLocationTracking } from '../../services/location';
import AvailabilityToggle from '../../components/AvailabilityToggle';

interface TodayStats {
  deliveries: number;
  earnings: number;
}

export default function DashboardScreen() {
  const { driver, updateDriver } = useAuthStore();
  const [refreshing, setRefreshing] = useState(false);
  const [todayStats, setTodayStats] = useState<TodayStats>({ deliveries: 0, earnings: 0 });
  const [isToggling, setIsToggling] = useState(false);

  const loadData = useCallback(async () => {
    try {
      const profile = await api.getDriverProfile();
      updateDriver(profile);
    } catch (error) {
      console.error('Failed to load profile:', error);
    }
  }, [updateDriver]);

  const handleToggleAvailability = async () => {
    if (!driver || isToggling) return;

    setIsToggling(true);
    try {
      const updated = await api.toggleAvailability(driver.id);
      updateDriver(updated);

      // Start/stop location tracking based on availability
      if (updated.is_available) {
        try {
          await startLocationTracking(driver.id);
          Alert.alert('Online', 'You are now accepting deliveries');
        } catch (locationError) {
          console.error('Location tracking error:', locationError);
          Alert.alert(
            'Location Required',
            'Please grant location permissions to go online.'
          );
          // Revert the toggle on the server
          await api.toggleAvailability(driver.id);
          updateDriver({ is_available: false });
        }
      } else {
        await stopLocationTracking();
        Alert.alert('Offline', 'You are no longer accepting deliveries');
      }
    } catch (error) {
      console.error('Failed to toggle availability:', error);
      Alert.alert('Error', 'Failed to update availability. Please try again.');
    } finally {
      setIsToggling(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadData();
    setRefreshing(false);
  };

  useEffect(() => {
    loadData();
  }, [loadData]);

  if (!driver) {
    return (
      <View style={styles.container}>
        <Text style={styles.loadingText}>Loading...</Text>
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={onRefresh}
          tintColor="#4CAF50"
        />
      }
    >
      <View style={styles.header}>
        <View style={styles.greetingContainer}>
          <Text style={styles.greeting}>Hello, {driver.user_name || 'Driver'}!</Text>
          <Text style={styles.statusText}>
            {driver.is_available ? 'Ready for deliveries' : 'Currently offline'}
          </Text>
        </View>
        <AvailabilityToggle
          isAvailable={driver.is_available}
          onToggle={handleToggleAvailability}
          disabled={isToggling}
        />
      </View>

      <View style={styles.statsContainer}>
        <Text style={styles.sectionTitle}>Today's Stats</Text>
        <View style={styles.statsRow}>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>{todayStats.deliveries}</Text>
            <Text style={styles.statLabel}>Deliveries</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>{todayStats.earnings.toLocaleString()} XOF</Text>
            <Text style={styles.statLabel}>Earnings</Text>
          </View>
        </View>
      </View>

      <View style={styles.statsContainer}>
        <Text style={styles.sectionTitle}>All Time</Text>
        <View style={styles.statsRow}>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>{driver.total_deliveries}</Text>
            <Text style={styles.statLabel}>Total Deliveries</Text>
          </View>
          <View style={styles.statCard}>
            <Text style={styles.statValue}>
              {typeof driver.average_rating === 'number'
                ? driver.average_rating.toFixed(1)
                : '5.0'}
            </Text>
            <Text style={styles.statLabel}>Rating</Text>
          </View>
        </View>
      </View>

      <View style={styles.vehicleInfo}>
        <Text style={styles.sectionTitle}>Vehicle</Text>
        <View style={styles.vehicleRow}>
          <Text style={styles.vehicleLabel}>Type:</Text>
          <Text style={styles.vehicleText}>
            {driver.vehicle_type
              ? driver.vehicle_type.charAt(0).toUpperCase() + driver.vehicle_type.slice(1)
              : 'Not set'}
          </Text>
        </View>
        {driver.vehicle_plate && (
          <View style={styles.vehicleRow}>
            <Text style={styles.vehicleLabel}>Plate:</Text>
            <Text style={styles.vehicleText}>{driver.vehicle_plate}</Text>
          </View>
        )}
      </View>

      <View style={styles.tipContainer}>
        <Text style={styles.tipTitle}>Tips for Drivers</Text>
        <Text style={styles.tipText}>
          - Stay online during peak hours (11am-2pm, 6pm-9pm){'\n'}
          - Keep your phone charged{'\n'}
          - Update your location for faster assignments
        </Text>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    textAlign: 'center',
    marginTop: 50,
    color: '#666',
  },
  header: {
    backgroundColor: 'white',
    padding: 20,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  greetingContainer: {
    flex: 1,
  },
  greeting: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#333',
  },
  statusText: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  statsContainer: {
    backgroundColor: 'white',
    margin: 15,
    marginBottom: 0,
    padding: 15,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    marginBottom: 15,
    color: '#666',
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-around',
  },
  statCard: {
    alignItems: 'center',
    flex: 1,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#4CAF50',
  },
  statLabel: {
    fontSize: 14,
    color: '#999',
    marginTop: 4,
  },
  vehicleInfo: {
    backgroundColor: 'white',
    margin: 15,
    marginBottom: 0,
    padding: 15,
    borderRadius: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 2,
  },
  vehicleRow: {
    flexDirection: 'row',
    marginBottom: 8,
  },
  vehicleLabel: {
    fontSize: 14,
    color: '#666',
    width: 60,
  },
  vehicleText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#333',
  },
  tipContainer: {
    backgroundColor: '#E8F5E9',
    margin: 15,
    padding: 15,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#C8E6C9',
  },
  tipTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: '#2E7D32',
    marginBottom: 8,
  },
  tipText: {
    fontSize: 13,
    color: '#388E3C',
    lineHeight: 20,
  },
});
