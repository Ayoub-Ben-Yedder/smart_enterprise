#include "websocket_manager.h"
#include "config.h"
#include "io_manager.h"


AsyncWebServer server(80);
AsyncWebSocket ws("/ws");

void handle_received_msg(String message){
  Serial.print("Received message: ");
  Serial.println(message);

  if(message == "open_door") {
    setActuatorState(RELAI_DOOR, HIGH);
  } else if(message == "close_door") {
    setActuatorState(RELAI_DOOR, LOW);
  } else if(message == "turn_on_lamp") {
    setActuatorState(RELAI_LAMP, HIGH);
  } else if(message == "turn_off_lamp") {
    setActuatorState(RELAI_LAMP, LOW);
  } else if(message == "turn_on_pris") {
    setActuatorState(RELAI_PRISE, HIGH);
  } else if(message == "turn_off_pris") {
    setActuatorState(RELAI_PRISE, LOW);
  } else {
    Serial.println("Unknown command received.");
  }

}

void onEvent(AsyncWebSocket *server, AsyncWebSocketClient *client, AwsEventType type, void *arg, uint8_t *data, size_t len){
  switch (type)
  {
  case WS_EVT_CONNECT:
    Serial.printf("WebSocket client #%u connected\n", client->id());
    break;
  case WS_EVT_DISCONNECT:
    Serial.printf("WebSocket client #%u disconnected\n", client->id());
    break;
  case WS_EVT_DATA:
    AwsFrameInfo *info = (AwsFrameInfo *)arg;
    if (info->final && info->index == 0 && info->len == len && info->opcode == WS_TEXT)
    {
      data[len] = 0;
      String message = (char*)data;
      handle_received_msg(message);
    }
    break;
  }
}

void setupWebSocket() {
  ws.onEvent(onEvent);
  server.addHandler(&ws);
  server.begin();
}

void send_msg(String msg){
  ws.textAll(msg);
}

void websocketCleanup() {
  ws.cleanupClients();
}