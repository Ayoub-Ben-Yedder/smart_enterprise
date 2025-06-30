#include "io_manager.h"
#include <Arduino.h>
#include <DHT.h>

DHT dht11(0, DHT11); // Will be reinitialized in setupDHT11

void setupSensor(int sensorPin) {
  pinMode(sensorPin, INPUT);
}

int readSensor(int sensorPin) {
  return analogRead(sensorPin);
}

void setupActuator(int actuatorPin) {
  pinMode(actuatorPin, OUTPUT);
}

void setActuatorState(int actuatorPin, int state) {
  digitalWrite(actuatorPin, state);
}
int getActuatorState(int actuatorPin) {
  return digitalRead(actuatorPin);
}

int readPIRSensor(int pirPin) {
  return digitalRead(pirPin);
}

void setupDHT11(int dhtPin) {
  dht11 = DHT(dhtPin, DHT11);
  dht11.begin();
}

float readDHT11Temperature(int dhtPin) {
  return dht11.readTemperature();
}

float readDHT11Humidity(int dhtPin) {
  return dht11.readHumidity();
}
