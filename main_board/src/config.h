#ifndef CONFIG_H
#define CONFIG_H

// WiFi credentials
#define ENTREPRISE_SSID  "TOPNET_VSKC"
#define ENTREPRISE_PASSWORD "a47qhmlwxy"

// Static IP configuration
#define STATIC_IP_ADDRESS IPAddress(192, 168, 1, 100)  // Choose an available IP in your network
#define GATEWAY_IP        IPAddress(192, 168, 1, 1)    // Usually your router's IP
#define SUBNET_MASK       IPAddress(255, 255, 255, 0)  // Common subnet mask
#define DNS_SERVER        IPAddress(8, 8, 8, 8)        // Google DNS or your preferred DNS

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