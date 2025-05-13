class WebSocketService {
  constructor(url, sessionId = null) {
    this.url = `${url}/ws/${sessionId}`;
    this.sessionId = sessionId;
    this.ws = null;
    this.onMessageCallback = null;
    this.onConnectionChangeCallback = null;
  }

  connect() {
    this.ws = new WebSocket(this.url);

    this.ws.onopen = () => {
      if (this.onConnectionChangeCallback) {
        this.onConnectionChangeCallback(true);
      }
      console.log("Connected to WebSocket server");
    };

    this.ws.onclose = () => {
      if (this.onConnectionChangeCallback) {
        this.onConnectionChangeCallback(false);
      }
      console.log("Disconnected from WebSocket server");
    };

    this.ws.onmessage = (event) => {
      if (this.onMessageCallback) {
        const data = JSON.parse(event.data);
        this.onMessageCallback(data);
      }
    };
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
    }
  }

  sendMessage(message) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(
        JSON.stringify({
          message,
        })
      );
    }
  }

  setOnMessageCallback(callback) {
    this.onMessageCallback = callback;
  }

  setOnConnectionChangeCallback(callback) {
    this.onConnectionChangeCallback = callback;
  }
}

export default WebSocketService;
