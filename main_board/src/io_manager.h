#ifndef IO_MANAGER_H
#define IO_MANAGER_H

void setupSensor(int sensorPin);
int readSensor(int sensorPin);

void setupActuator(int actuatorPin);
void setActuatorState(int actuatorPin, int state);
int getActuatorState(int actuatorPin);

#endif // IO_MANAGER_H