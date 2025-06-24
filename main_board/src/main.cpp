#include <Arduino.h>
#include "config.h"
#include "wifi_manager.h"
#include "websocket_manager.h"
#include "io_manager.h"

unsigned long lastTime = 0;
unsigned long timerDelay = SENSOR_READ_DELAY;

void setup()
{
  Serial.begin(115200);
  
  // Initialize WiFi
  initWiFi(ENTREPRISE_SSID, ENTREPRISE_PASSWORD);
  
  // Setup WebSocket server
  setupWebSocket();
  
  // Initialize sensor
  setupSensor(DHT11_PIN);
  setupSensor(PIR_PIN);

  // Initialize actuators
  setupActuator(RELAI_DOOR);
  setupActuator(RELAI_LAMP);
  setupActuator(RELAI_PRISE);

  Serial.println("Setup complete. Ready to read sensors and send data over WebSocket.");
}

void loop()
{
  if ((millis() - lastTime) > timerDelay) {
    send_msg(String(readSensor(DHT11_PIN)));
    //send_msg(String(readSensor(PIR_PIN)));
    lastTime = millis();
  }
  websocketCleanup();
}