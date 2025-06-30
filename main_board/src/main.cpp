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
  
  // Initialize sensors
  setupDHT11(DHT11_PIN);
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
    float temp = readDHT11Temperature(DHT11_PIN);
    float humidity = readDHT11Humidity(DHT11_PIN);
    int pirValue = readPIRSensor(PIR_PIN);
    
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