/**
 * Toggle switch for driver availability.
 */
import { View, Text, Switch, StyleSheet, ActivityIndicator } from 'react-native';

interface AvailabilityToggleProps {
  isAvailable: boolean;
  onToggle: () => void;
  disabled?: boolean;
}

export default function AvailabilityToggle({
  isAvailable,
  onToggle,
  disabled = false,
}: AvailabilityToggleProps) {
  return (
    <View style={styles.container}>
      {disabled ? (
        <ActivityIndicator size="small" color="#4CAF50" style={styles.loader} />
      ) : (
        <Text style={[styles.status, isAvailable ? styles.online : styles.offline]}>
          {isAvailable ? 'Online' : 'Offline'}
        </Text>
      )}
      <Switch
        value={isAvailable}
        onValueChange={onToggle}
        trackColor={{ false: '#ccc', true: '#81C784' }}
        thumbColor={isAvailable ? '#4CAF50' : '#f4f3f4'}
        ios_backgroundColor="#ccc"
        disabled={disabled}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  status: {
    marginRight: 10,
    fontWeight: '600',
    fontSize: 14,
  },
  online: {
    color: '#4CAF50',
  },
  offline: {
    color: '#999',
  },
  loader: {
    marginRight: 10,
  },
});
