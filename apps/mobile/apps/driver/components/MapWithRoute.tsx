/**
 * Map component with driver and destination markers.
 * Shows driver location (blue), pickup (green), and delivery (red) markers.
 */
import { View, StyleSheet, Platform } from 'react-native';
import MapView, { Marker, PROVIDER_GOOGLE, PROVIDER_DEFAULT } from 'react-native-maps';

interface Location {
  lat: number;
  lng: number;
}

interface MapWithRouteProps {
  pickupLocation?: Location;
  deliveryLocation: Location;
  driverLocation?: Location | null;
}

export default function MapWithRoute({
  pickupLocation,
  deliveryLocation,
  driverLocation,
}: MapWithRouteProps) {
  // Calculate region to show all markers
  const calculateRegion = () => {
    const points: Location[] = [deliveryLocation];
    if (driverLocation) points.push(driverLocation);
    if (pickupLocation) points.push(pickupLocation);

    if (points.length === 1) {
      return {
        latitude: points[0].lat,
        longitude: points[0].lng,
        latitudeDelta: 0.02,
        longitudeDelta: 0.02,
      };
    }

    const lats = points.map((p) => p.lat);
    const lngs = points.map((p) => p.lng);

    const minLat = Math.min(...lats);
    const maxLat = Math.max(...lats);
    const minLng = Math.min(...lngs);
    const maxLng = Math.max(...lngs);

    const latDelta = (maxLat - minLat) * 1.5 || 0.02;
    const lngDelta = (maxLng - minLng) * 1.5 || 0.02;

    return {
      latitude: (minLat + maxLat) / 2,
      longitude: (minLng + maxLng) / 2,
      latitudeDelta: Math.max(latDelta, 0.02),
      longitudeDelta: Math.max(lngDelta, 0.02),
    };
  };

  const region = calculateRegion();

  // Use Google Maps on Android for better performance, default on iOS
  const provider = Platform.OS === 'android' ? PROVIDER_GOOGLE : PROVIDER_DEFAULT;

  return (
    <View style={styles.container}>
      <MapView
        provider={provider}
        style={styles.map}
        region={region}
        showsUserLocation={false}
        showsMyLocationButton={false}
      >
        {/* Pickup marker (green) */}
        {pickupLocation && (
          <Marker
            coordinate={{
              latitude: pickupLocation.lat,
              longitude: pickupLocation.lng,
            }}
            title="Pickup"
            description="Restaurant pickup location"
            pinColor="green"
          />
        )}

        {/* Delivery marker (red) */}
        <Marker
          coordinate={{
            latitude: deliveryLocation.lat,
            longitude: deliveryLocation.lng,
          }}
          title="Delivery"
          description="Customer delivery location"
          pinColor="red"
        />

        {/* Driver marker (blue) */}
        {driverLocation && (
          <Marker
            coordinate={{
              latitude: driverLocation.lat,
              longitude: driverLocation.lng,
            }}
            title="You"
            description="Your current location"
            pinColor="blue"
          />
        )}
      </MapView>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  map: {
    flex: 1,
  },
});
