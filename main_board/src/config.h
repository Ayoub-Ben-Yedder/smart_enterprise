#ifndef CONFIG_H
#define CONFIG_H

// WiFi credentials
#define ENTREPRISE_SSID  "TOPNET_VSKC"
#define ENTREPRISE_PASSWORD "a47qhmlwxy"

// Sensor pins
#define DHT11_PIN 33
#define PIR_PIN 32

// Actuator pins
#define RELAI_DOOR 5
#define RELAI_LAMP 18
#define RELAI_PRISE 19

// Timing constants
#define SENSOR_READ_DELAY 1000  // milliseconds

#endif // CONFIG_H