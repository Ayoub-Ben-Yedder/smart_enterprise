#include <Arduino.h>
#include <DHT.h>
#include <WiFi.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include "config.h"

void initWiFi(const char* ssid, const char* password);
void printWiFiStatus();
void setupWebSocket();
void handle_received_msg(String message);
void send_msg(String msg);
void websocketCleanup();

AsyncWebServer server(80);
AsyncWebSocket ws("/ws");

DHT dht11 = DHT(DHT11_PIN, DHT11);

unsigned long lastTime = 0;
unsigned long timerDelay = SENSOR_READ_DELAY;

void setup()
{
  Serial.begin(115200);
  
  // Initialize WiFi
  initWiFi(ENTREPRISE_SSID, ENTREPRISE_PASSWORD);
  
  // Setup WebSocket server
  setupWebSocket();
  
  // Initialize sensors
  dht11.begin();
  pinMode(PIR_PIN, INPUT);

  // Initialize actuators
  pinMode(RELAI_DOOR, OUTPUT);
  pinMode(RELAI_LAMP, OUTPUT);
  pinMode(RELAI_PRISE, OUTPUT);

  Serial.println("Setup complete. Ready to read sensors and send data over WebSocket.");
}

void loop()
{
  if ((millis() - lastTime) > timerDelay) {
    float temp = dht11.readTemperature();
    float humidity = dht11.readHumidity();
    int pirValue = digitalRead(PIR_PIN);
    
    String sensorTemp = "temp:" + String(temp);
    String sensorHumd = "humidity:" + String(humidity);
    String sensorPIR = "pir:" + String(pirValue);
    send_msg(sensorTemp);
    send_msg(sensorHumd);
    send_msg(sensorPIR);
    
    lastTime = millis();
  }
  websocketCleanup();
}


void handle_received_msg(String message){
  Serial.print("Received message: ");
  Serial.println(message);

  if(message == "open_door") {
    digitalWrite(RELAI_DOOR, HIGH);
  } else if(message == "close_door") {
    digitalWrite(RELAI_DOOR, LOW);
  } else if(message == "turn_on_lamp") {
    digitalWrite(RELAI_LAMP, HIGH);
  } else if(message == "turn_off_lamp") {
    digitalWrite(RELAI_LAMP, LOW);
  } else if(message == "turn_on_pris") {
    digitalWrite(RELAI_PRISE, HIGH);
  } else if(message == "turn_off_pris") {
    digitalWrite(RELAI_PRISE, LOW);
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

void initWiFi(const char* ssid, const char* password) {
  WiFi.mode(WIFI_STA);

  if (!WiFi.config(STATIC_IP_ADDRESS, GATEWAY_IP, SUBNET_MASK, DNS_SERVER)) {
    Serial.println("Static IP configuration failed!");
  }
  
  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi with static IP ..");
  while (WiFi.status() != WL_CONNECTED) {
    Serial.print('.');
    delay(1000);
  }
  Serial.println();
  printWiFiStatus();
}

void printWiFiStatus() {
  Serial.println("=== WiFi Connection Status ===");
  Serial.print("Connected to network: ");
  Serial.println(WiFi.SSID());
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());
  Serial.print("Gateway: ");
  Serial.println(WiFi.gatewayIP());
  Serial.print("Subnet Mask: ");
  Serial.println(WiFi.subnetMask());
  Serial.print("DNS Server: ");
  Serial.println(WiFi.dnsIP());
  Serial.print("Signal Strength (RSSI): ");
  Serial.print(WiFi.RSSI());
  Serial.println(" dBm");
  Serial.println("==============================");
}