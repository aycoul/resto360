/**
 * Background location tracking service.
 * Uses expo-location and expo-task-manager for background updates.
 */
import * as Location from 'expo-location';
import * as TaskManager from 'expo-task-manager';
import { useAuthStore } from '../stores/auth';

const LOCATION_TASK_NAME = 'driver-background-location';
const WS_URL = process.env.EXPO_PUBLIC_WS_URL || 'ws://localhost:8000';

let wsConnection: WebSocket | null = null;

// Define background task for location updates
TaskManager.defineTask(LOCATION_TASK_NAME, async ({ data, error }) => {
  if (error) {
    console.error('Location task error:', error);
    return;
  }

  if (data) {
    const { locations } = data as { locations: Location.LocationObject[] };
    const location = locations[0];

    if (location) {
      await sendLocationUpdate({
        lat: location.coords.latitude,
        lng: location.coords.longitude,
        accuracy: location.coords.accuracy,
        heading: location.coords.heading,
        speed: location.coords.speed,
        timestamp: location.timestamp,
      });
    }
  }
});

interface LocationUpdate {
  lat: number;
  lng: number;
  accuracy: number | null;
  heading: number | null;
  speed: number | null;
  timestamp: number;
}

async function sendLocationUpdate(location: LocationUpdate): Promise<void> {
  // Send via WebSocket if connected
  if (wsConnection && wsConnection.readyState === WebSocket.OPEN) {
    wsConnection.send(JSON.stringify({
      type: 'location_update',
      ...location,
    }));
  }
}

export async function requestLocationPermissions(): Promise<boolean> {
  // Request foreground permission first
  const { status: foregroundStatus } = await Location.requestForegroundPermissionsAsync();
  if (foregroundStatus !== 'granted') {
    return false;
  }

  // Then request background permission
  const { status: backgroundStatus } = await Location.requestBackgroundPermissionsAsync();
  return backgroundStatus === 'granted';
}

export async function startLocationTracking(driverId: string): Promise<void> {
  const hasPermission = await requestLocationPermissions();
  if (!hasPermission) {
    throw new Error('Location permission not granted');
  }

  // Connect WebSocket for location updates
  const { accessToken } = useAuthStore.getState();
  const wsUrl = `${WS_URL}/ws/driver/${driverId}/location/?token=${accessToken}`;

  wsConnection = new WebSocket(wsUrl);

  wsConnection.onopen = () => {
    console.log('Location WebSocket connected');
  };

  wsConnection.onclose = () => {
    console.log('Location WebSocket closed');
  };

  wsConnection.onerror = (error) => {
    console.error('Location WebSocket error:', error);
  };

  wsConnection.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      console.log('Location WebSocket message:', data);
    } catch {
      console.error('Failed to parse WebSocket message');
    }
  };

  // Start background location updates
  await Location.startLocationUpdatesAsync(LOCATION_TASK_NAME, {
    accuracy: Location.Accuracy.High,
    timeInterval: 5000,      // Every 5 seconds
    distanceInterval: 10,    // Or every 10 meters
    deferredUpdatesInterval: 5000,
    deferredUpdatesDistance: 10,
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
  // Stop background updates
  const isTracking = await TaskManager.isTaskRegisteredAsync(LOCATION_TASK_NAME);
  if (isTracking) {
    await Location.stopLocationUpdatesAsync(LOCATION_TASK_NAME);
  }

  // Close WebSocket
  if (wsConnection) {
    wsConnection.close();
    wsConnection = null;
  }
}

export async function getCurrentLocation(): Promise<Location.LocationObject> {
  const hasPermission = await requestLocationPermissions();
  if (!hasPermission) {
    throw new Error('Location permission not granted');
  }

  return Location.getCurrentPositionAsync({
    accuracy: Location.Accuracy.High,
  });
}

export function getWebSocketConnection(): WebSocket | null {
  return wsConnection;
}

export async function isTrackingActive(): Promise<boolean> {
  return TaskManager.isTaskRegisteredAsync(LOCATION_TASK_NAME);
}
