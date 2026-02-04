/**
 * API service for driver app.
 * Handles all REST API calls to the backend.
 */
import { useAuthStore } from '../stores/auth';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

class ApiService {
  private getHeaders(): HeadersInit {
    const { accessToken } = useAuthStore.getState();
    return {
      'Content-Type': 'application/json',
      ...(accessToken && { Authorization: `Bearer ${accessToken}` }),
    };
  }

  private async handleResponse<T>(response: Response): Promise<T> {
    if (response.status === 401) {
      // Try to refresh token
      await useAuthStore.getState().refreshAccessToken();
      throw new Error('Unauthorized - please try again');
    }

    if (!response.ok) {
      const error = await response.json().catch(() => ({}));
      throw new Error(error.detail || error.error || 'Request failed');
    }

    // Handle 204 No Content
    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  }

  // Driver endpoints
  async toggleAvailability(driverId: string): Promise<any> {
    const response = await fetch(
      `${API_URL}/api/v1/delivery/drivers/${driverId}/toggle_availability/`,
      {
        method: 'POST',
        headers: this.getHeaders(),
      }
    );
    return this.handleResponse(response);
  }

  async updateLocation(driverId: string, lat: number, lng: number): Promise<any> {
    const response = await fetch(
      `${API_URL}/api/v1/delivery/drivers/${driverId}/update_location/`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ lat, lng }),
      }
    );
    return this.handleResponse(response);
  }

  async getDriverProfile(): Promise<any> {
    const response = await fetch(
      `${API_URL}/api/v1/delivery/drivers/me/`,
      { headers: this.getHeaders() }
    );
    return this.handleResponse(response);
  }

  // Delivery endpoints
  async getActiveDeliveries(): Promise<any[]> {
    const response = await fetch(
      `${API_URL}/api/v1/delivery/deliveries/active/`,
      { headers: this.getHeaders() }
    );
    return this.handleResponse(response);
  }

  async getDelivery(deliveryId: string): Promise<any> {
    const response = await fetch(
      `${API_URL}/api/v1/delivery/deliveries/${deliveryId}/`,
      { headers: this.getHeaders() }
    );
    return this.handleResponse(response);
  }

  async updateDeliveryStatus(
    deliveryId: string,
    status: string,
    data?: Record<string, unknown>
  ): Promise<any> {
    const response = await fetch(
      `${API_URL}/api/v1/delivery/deliveries/${deliveryId}/update_status/`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({ status, ...data }),
      }
    );
    return this.handleResponse(response);
  }

  async pickupDelivery(deliveryId: string): Promise<any> {
    const response = await fetch(
      `${API_URL}/api/v1/delivery/deliveries/${deliveryId}/pickup/`,
      {
        method: 'POST',
        headers: this.getHeaders(),
      }
    );
    return this.handleResponse(response);
  }

  async startDelivery(deliveryId: string): Promise<any> {
    const response = await fetch(
      `${API_URL}/api/v1/delivery/deliveries/${deliveryId}/start_delivery/`,
      {
        method: 'POST',
        headers: this.getHeaders(),
      }
    );
    return this.handleResponse(response);
  }

  async confirmDelivery(
    deliveryId: string,
    proofType: 'photo' | 'signature',
    proofData: string,
    recipientName?: string
  ): Promise<any> {
    const response = await fetch(
      `${API_URL}/api/v1/delivery/deliveries/${deliveryId}/confirm/`,
      {
        method: 'POST',
        headers: this.getHeaders(),
        body: JSON.stringify({
          proof_type: proofType,
          proof_data: proofData,
          recipient_name: recipientName,
        }),
      }
    );
    return this.handleResponse(response);
  }
}

export const api = new ApiService();
