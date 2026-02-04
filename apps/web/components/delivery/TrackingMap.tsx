/**
 * Map component for delivery tracking.
 * Uses Google Maps API via script tag (lightweight alternative to @react-google-maps/api).
 */
'use client';

import { useEffect, useRef, useState } from 'react';

interface Location {
  lat: number;
  lng: number;
}

interface TrackingMapProps {
  driverLocation: Location | null;
  deliveryLocation: Location;
  restaurantLocation?: Location;
}

declare global {
  interface Window {
    google: typeof google;
    initMap: () => void;
  }
}

export default function TrackingMap({
  driverLocation,
  deliveryLocation,
  restaurantLocation,
}: TrackingMapProps) {
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<google.maps.Map | null>(null);
  const driverMarkerRef = useRef<google.maps.Marker | null>(null);
  const [isLoaded, setIsLoaded] = useState(false);

  // Load Google Maps script
  useEffect(() => {
    if (window.google) {
      setIsLoaded(true);
      return;
    }

    const apiKey = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
    if (!apiKey) {
      console.warn('Google Maps API key not configured');
      return;
    }

    window.initMap = () => setIsLoaded(true);

    const script = document.createElement('script');
    script.src = `https://maps.googleapis.com/maps/api/js?key=${apiKey}&callback=initMap`;
    script.async = true;
    script.defer = true;
    document.head.appendChild(script);

    return () => {
      delete window.initMap;
    };
  }, []);

  // Initialize map
  useEffect(() => {
    if (!isLoaded || !mapRef.current || mapInstanceRef.current) return;

    const center = driverLocation || deliveryLocation;

    const map = new google.maps.Map(mapRef.current, {
      center: { lat: center.lat, lng: center.lng },
      zoom: 15,
      disableDefaultUI: true,
      zoomControl: true,
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: false,
    });

    mapInstanceRef.current = map;

    // Add delivery location marker (red)
    new google.maps.Marker({
      position: deliveryLocation,
      map,
      icon: {
        path: google.maps.SymbolPath.CIRCLE,
        scale: 10,
        fillColor: '#F44336',
        fillOpacity: 1,
        strokeColor: '#ffffff',
        strokeWeight: 2,
      },
      title: 'Delivery Location',
    });

    // Add restaurant marker (green) if available
    if (restaurantLocation) {
      new google.maps.Marker({
        position: restaurantLocation,
        map,
        icon: {
          path: google.maps.SymbolPath.CIRCLE,
          scale: 10,
          fillColor: '#4CAF50',
          fillOpacity: 1,
          strokeColor: '#ffffff',
          strokeWeight: 2,
        },
        title: 'Restaurant',
      });
    }

    // Create driver marker (will be updated)
    if (driverLocation) {
      driverMarkerRef.current = new google.maps.Marker({
        position: driverLocation,
        map,
        icon: {
          path: google.maps.SymbolPath.FORWARD_CLOSED_ARROW,
          scale: 6,
          fillColor: '#2196F3',
          fillOpacity: 1,
          strokeColor: '#ffffff',
          strokeWeight: 2,
          rotation: 0,
        },
        title: 'Driver',
      });
    }
  }, [isLoaded, deliveryLocation, restaurantLocation, driverLocation]);

  // Update driver marker position
  useEffect(() => {
    if (!mapInstanceRef.current || !driverLocation) return;

    if (driverMarkerRef.current) {
      // Animate marker movement
      driverMarkerRef.current.setPosition(driverLocation);
    } else {
      // Create marker if not exists
      driverMarkerRef.current = new google.maps.Marker({
        position: driverLocation,
        map: mapInstanceRef.current,
        icon: {
          path: google.maps.SymbolPath.FORWARD_CLOSED_ARROW,
          scale: 6,
          fillColor: '#2196F3',
          fillOpacity: 1,
          strokeColor: '#ffffff',
          strokeWeight: 2,
          rotation: 0,
        },
        title: 'Driver',
      });
    }

    // Pan map to keep driver in view
    mapInstanceRef.current.panTo(driverLocation);
  }, [driverLocation]);

  if (!isLoaded) {
    return (
      <div className="w-full h-64 bg-gray-100 rounded-lg flex items-center justify-center">
        <span className="text-gray-500">Loading map...</span>
      </div>
    );
  }

  return (
    <div ref={mapRef} className="w-full h-64 rounded-lg overflow-hidden shadow-md" />
  );
}
