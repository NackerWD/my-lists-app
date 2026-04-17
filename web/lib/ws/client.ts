export interface WsMessage {
  type: string;
  payload: Record<string, unknown>;
  user_id?: string;
}

type WsCallback = (msg: WsMessage) => void;

const BACKOFF_DELAYS = [1000, 2000, 4000, 8000, 30000];

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private listId: string | null = null;
  private token: string | null = null;
  private attempt = 0;
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private intentionalClose = false;

  onMessage: WsCallback | null = null;
  onConnect: (() => void) | null = null;
  onDisconnect: (() => void) | null = null;
  onError: ((event: Event) => void) | null = null;

  connect(listId: string, token: string): void {
    this.listId = listId;
    this.token = token;
    this.intentionalClose = false;
    this.attempt = 0;
    this._connect();
  }

  private _connect(): void {
    if (!this.listId || !this.token) return;

    const wsBase = (process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000")
      .replace(/^http/, "ws");

    this.ws = new WebSocket(`${wsBase}/ws/lists/${this.listId}?token=${this.token}`);

    this.ws.onopen = () => {
      this.attempt = 0;
      this.onConnect?.();
    };

    this.ws.onmessage = (event) => {
      try {
        const msg: WsMessage = JSON.parse(event.data as string);
        this.onMessage?.(msg);
      } catch {
        // ignore malformed messages
      }
    };

    this.ws.onerror = (event) => {
      this.onError?.(event);
    };

    this.ws.onclose = () => {
      this.onDisconnect?.();
      if (!this.intentionalClose) {
        this._scheduleReconnect();
      }
    };
  }

  private _scheduleReconnect(): void {
    const delay = BACKOFF_DELAYS[Math.min(this.attempt, BACKOFF_DELAYS.length - 1)];
    this.attempt++;
    this.reconnectTimer = setTimeout(() => this._connect(), delay);
  }

  send(message: WsMessage): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    }
  }

  disconnect(): void {
    this.intentionalClose = true;
    if (this.reconnectTimer) clearTimeout(this.reconnectTimer);
    this.ws?.close();
    this.ws = null;
  }
}
