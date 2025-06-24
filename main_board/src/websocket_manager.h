#ifndef WEBSOCKET_MANAGER_H
#define WEBSOCKET_MANAGER_H

#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>

extern AsyncWebServer server;
extern AsyncWebSocket ws;

void setupWebSocket();
void handle_received_msg(String message);
void send_msg(String msg);
void websocketCleanup();

#endif // WEBSOCKET_MANAGER_H