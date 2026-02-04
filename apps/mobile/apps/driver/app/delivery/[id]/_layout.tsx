/**
 * Layout for delivery detail screens (navigate, confirm).
 */
import { Stack } from 'expo-router';

export default function DeliveryLayout() {
  return (
    <Stack
      screenOptions={{
        headerShown: true,
        headerBackTitle: 'Back',
      }}
    />
  );
}
