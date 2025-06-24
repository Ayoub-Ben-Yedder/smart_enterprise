#ifndef WIFI_MANAGER_H
#define WIFI_MANAGER_H

#include <WiFi.h>

void initWiFi(const char* ssid, const char* password);
void printWiFiStatus();

#endif // WIFI_MANAGER_H