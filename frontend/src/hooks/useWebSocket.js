import { useEffect, useRef, useState, useCallback } from 'react';

function wsUrlFromBackendUrl(backendUrl) {
  try {
    const parsed = new URL(backendUrl);
    const protocol = parsed.protocol === 'https:' ? 'wss:' : 'ws:';
    let path = parsed.pathname.replace(/\/+$/, '');
    if (path.endsWith('/api')) {
      path = path.slice(0, -4);
    }
    return `${protocol}//${parsed.host}${path}/ws`;
  } catch {
    return '';
  }
}

function resolveWebSocketUrl() {
  const envUrl = import.meta.env.VITE_WS_URL;
  if (envUrl) return envUrl;

  const backendUrl = import.meta.env.VITE_BACKEND_URL;
  if (backendUrl) {
    const derived = wsUrlFromBackendUrl(backendUrl);
    if (derived) return derived;
  }

  const { protocol, host } = window.location;
  if (!host) return 'ws://127.0.0.1:8000/ws';

  const wsProtocol = protocol === 'https:' ? 'wss:' : 'ws:';
  return `${wsProtocol}//${host}/ws`;
}

const WS_URL = resolveWebSocketUrl();

export function useWebSocket() {
  const [widgetData, setWidgetData] = useState({});
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);
  const reconnectTimer = useRef(null);
  const shouldReconnect = useRef(true);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    let ws;
    try {
      ws = new WebSocket(WS_URL);
    } catch {
      setConnected(false);
      reconnectTimer.current = setTimeout(connect, 2000);
      return;
    }

    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      if (reconnectTimer.current) {
        clearTimeout(reconnectTimer.current);
        reconnectTimer.current = null;
      }
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type) {
          setWidgetData(prev => ({ ...prev, [msg.type]: msg.data }));
        }
      } catch {
        // ignore malformed messages
      }
    };

    ws.onclose = () => {
      setConnected(false);
      if (shouldReconnect.current) {
        reconnectTimer.current = setTimeout(connect, 2000);
      }
    };

    ws.onerror = () => {
      ws.close();
    };
  }, []);

  useEffect(() => {
    shouldReconnect.current = true;
    connect();
    return () => {
      shouldReconnect.current = false;
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  return { widgetData, connected };
}
