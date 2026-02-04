/**
 * Hook for WebSocket connections with auto-reconnect.
 */
import { useEffect, useState, useCallback, useRef } from 'react';
import { useAuthStore } from '../stores/auth';

const WS_URL = process.env.EXPO_PUBLIC_WS_URL || 'ws://localhost:8000';

interface UseWebSocketOptions {
  url: string;
  onMessage?: (data: unknown) => void;
  autoReconnect?: boolean;
  enabled?: boolean;
}

interface UseWebSocketReturn {
  isConnected: boolean;
  lastMessage: unknown;
  send: (data: unknown) => void;
  disconnect: () => void;
  reconnect: () => void;
}

export function useWebSocket({
  url,
  onMessage,
  autoReconnect = true,
  enabled = true,
}: UseWebSocketOptions): UseWebSocketReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [lastMessage, setLastMessage] = useState<unknown>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>();
  const reconnectAttempts = useRef(0);

  const { accessToken } = useAuthStore();

  const connect = useCallback(() => {
    if (!accessToken || !enabled) return;

    // Close existing connection
    if (wsRef.current) {
      wsRef.current.close();
    }

    const fullUrl = `${WS_URL}${url}?token=${accessToken}`;
    const ws = new WebSocket(fullUrl);

    ws.onopen = () => {
      setIsConnected(true);
      reconnectAttempts.current = 0;
    };

    ws.onclose = () => {
      setIsConnected(false);
      wsRef.current = null;

      if (autoReconnect && enabled) {
        // Exponential backoff: 1s, 2s, 4s, 8s, 16s, max 30s
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 30000);
        reconnectAttempts.current++;

        reconnectTimeoutRef.current = setTimeout(connect, delay);
      }
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLastMessage(data);
        onMessage?.(data);
      } catch {
        console.error('Failed to parse WebSocket message');
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    wsRef.current = ws;
  }, [url, accessToken, onMessage, autoReconnect, enabled]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    wsRef.current?.close();
    wsRef.current = null;
    setIsConnected(false);
  }, []);

  const send = useCallback((data: unknown) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    }
  }, []);

  useEffect(() => {
    if (enabled) {
      connect();
    } else {
      disconnect();
    }
    return () => disconnect();
  }, [connect, disconnect, enabled]);

  return {
    isConnected,
    lastMessage,
    send,
    disconnect,
    reconnect: connect,
  };
}
