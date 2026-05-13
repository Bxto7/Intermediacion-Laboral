import { useState, useEffect, useRef, useCallback } from 'react'

export interface Notification {
  id: string
  type: string
  title: string
  body: string
  payload: Record<string, unknown>
  read: boolean
  received_at: string
}

export const useNotifications = (userId: string | null) => {
  const [notifications, setNotifications] = useState<Notification[]>([])
  const [connected, setConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimer = useRef<ReturnType<typeof setTimeout> | null>(null)

  const connect = useCallback(() => {
    if (!userId) return
    const token = localStorage.getItem('access_token')
    if (!token) return

    const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
    const host = window.location.hostname
    const port = import.meta.env.VITE_API_PORT || '8000'
    const url = `${proto}://${host}:${port}/api/v1/ws/notifications/${userId}?token=${encodeURIComponent(token)}`

    const ws = new WebSocket(url)
    wsRef.current = ws

    ws.onopen = () => {
      setConnected(true)
      // send ping every 25s to keep alive
      const ping = setInterval(() => ws.readyState === WebSocket.OPEN && ws.send('ping'), 25_000)
      ws.onclose = () => {
        setConnected(false)
        clearInterval(ping)
        reconnectTimer.current = setTimeout(connect, 5_000)
      }
    }

    ws.onmessage = (event) => {
      if (event.data === 'pong') return
      try {
        const msg = JSON.parse(event.data)
        const notif: Notification = {
          id: `${Date.now()}-${Math.random()}`,
          type: msg.type,
          title: msg.title,
          body: msg.body,
          payload: msg.payload ?? {},
          read: false,
          received_at: new Date().toISOString(),
        }
        setNotifications(prev => [notif, ...prev].slice(0, 50))
      } catch { /* ignore malformed */ }
    }

    ws.onerror = () => ws.close()
  }, [userId])

  useEffect(() => {
    connect()
    return () => {
      wsRef.current?.close()
      if (reconnectTimer.current) clearTimeout(reconnectTimer.current)
    }
  }, [connect])

  const markAllRead = () => setNotifications(prev => prev.map(n => ({ ...n, read: true })))
  const dismiss = (id: string) => setNotifications(prev => prev.filter(n => n.id !== id))
  const unreadCount = notifications.filter(n => !n.read).length

  return { notifications, unreadCount, connected, markAllRead, dismiss }
}
