import json
from fastapi import WebSocket


class ConnectionManager:
    """
    Керує WebSocket з'єднаннями.
    Один юзер може мати декілька вкладок (список сокетів на user_id).
    """

    def __init__(self):
        # { user_id: [WebSocket, ...] }
        self.active: dict[int, list[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
        # Увага: accept() виконується в ендпоїнті ДО виклику connect()
        if user_id not in self.active:
            self.active[user_id] = []
        self.active[user_id].append(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket):
        if user_id in self.active:
            self.active[user_id].remove(websocket)
            if not self.active[user_id]:
                del self.active[user_id]

    async def broadcast_to_user(self, user_id: int, message: dict):
        """Надсилає повідомлення всім відкритим вкладкам юзера."""
        connections = self.active.get(user_id, [])
        dead: list[WebSocket] = []

        for ws in connections:
            try:
                await ws.send_text(json.dumps(message))
            except Exception:
                dead.append(ws)

        for ws in dead:
            self.disconnect(user_id, ws)
