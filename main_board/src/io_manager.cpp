#include "io_manager.h"
#include <Arduino.h>

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
