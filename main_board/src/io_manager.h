#ifndef IO_MANAGER_H
#define IO_MANAGER_H

void setupSensor(int sensorPin);
int readPIRSensor(int pirPin);

void setupDHT11(int dhtPin);
float readDHT11Temperature(int dhtPin);
float readDHT11Humidity(int dhtPin);

void setupActuator(int actuatorPin);
void setActuatorState(int actuatorPin, int state);
int getActuatorState(int actuatorPin);

#endif // IO_MANAGER_H