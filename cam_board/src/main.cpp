#include <Arduino.h>
#include "esp_camera.h"
#include <WiFi.h>
#include <HTTPClient.h>
#include "camera_pins.h"

// Wifi credentials
const char* ssid = "TOPNET_VSKC";
const char* password = "a47qhmlwxy";

// Server configuration
const char* serverURL = "http://192.168.1.17:5000/upload"; 
const unsigned long sendInterval = 10000; // Send image every 10 seconds
unsigned long lastSendTime = 0;

camera_config_t config;

void camera_configurations(){
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sscb_sda = SIOD_GPIO_NUM;
  config.pin_sscb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  
  // if PSRAM IC present, init with UXGA resolution and higher JPEG quality
  //                      for larger pre-allocated frame buffer.
  if(psramFound()){
    config.frame_size = FRAMESIZE_UXGA;
    config.jpeg_quality = 10;
    config.fb_count = 2;
  } else {
    config.frame_size = FRAMESIZE_SVGA;
    config.jpeg_quality = 12;
    config.fb_count = 1;
  }
}

bool sendImageToServer() {
  digitalWrite(FLASH_GPIO_NUM, HIGH); // Turn on flash
  delay(100); // Allow flash to stabilize
  // Capture image
  camera_fb_t * fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed");
    return false;
  } 
  digitalWrite(FLASH_GPIO_NUM, LOW); // Turn off flash

  WiFiClient client;
  HTTPClient http;
  http.begin(client, serverURL);
  
  // Generate boundary for multipart form data
  String boundary = "----ESP32CAMFormBoundary" + String(random(1000000, 9999999));
  
  // Calculate content length
  String timestamp = String(millis());
  String filename = "image_" + timestamp + ".jpg";
  
  String formStart = "--" + boundary + "\r\n";
  formStart += "Content-Disposition: form-data; name=\"file\"; filename=\"" + filename + "\"\r\n";
  formStart += "Content-Type: image/jpeg\r\n\r\n";
  String formEnd = "\r\n--" + boundary + "--\r\n";
  
  size_t totalLength = formStart.length() + fb->len + formEnd.length();
  
  // Set headers
  http.addHeader("Content-Type", "multipart/form-data; boundary=" + boundary);
  http.addHeader("Content-Length", String(totalLength));
  
  Serial.printf("Sending image of size: %d bytes as multipart form data\n", fb->len);
  Serial.printf("Total form data size: %d bytes\n", totalLength);
  
  // Create the complete form data
  uint8_t* formData = (uint8_t*)malloc(totalLength);
  if (!formData) {
    Serial.println("Failed to allocate memory for form data");
    esp_camera_fb_return(fb);
    return false;
  }
  
  // Copy form start
  memcpy(formData, formStart.c_str(), formStart.length());
  size_t offset = formStart.length();
  
  // Copy image data
  memcpy(formData + offset, fb->buf, fb->len);
  offset += fb->len;
  
  // Copy form end
  memcpy(formData + offset, formEnd.c_str(), formEnd.length());
  
  // Send POST request
  int httpResponseCode = http.POST(formData, totalLength);
  
  bool success = false;
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.printf("HTTP Response: %d\n", httpResponseCode);
    if (response.length() < 500) {  // Only print short responses
      Serial.println("Response: " + response);
    } else {
      Serial.println("Response received (too long to print)");
    }
    success = (httpResponseCode == 200);
  } else {
    Serial.printf("HTTP Error: %d\n", httpResponseCode);
    String error = http.errorToString(httpResponseCode);
    Serial.println("Error details: " + error);
  }
  
  // Cleanup
  free(formData);
  http.end();
  esp_camera_fb_return(fb);
  return success;
}

void setup() {
  pinMode(FLASH_GPIO_NUM, OUTPUT);
  digitalWrite(FLASH_GPIO_NUM, LOW); // Ensure flash is off initially
  Serial.begin(115200);
  Serial.setDebugOutput(true);
  Serial.println();

  camera_configurations();

  // camera init
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }

  sensor_t * s = esp_camera_sensor_get();

  s->set_framesize(s, FRAMESIZE_QVGA);

  WiFi.begin(ssid, password);
  Serial.print("Connecting to WiFi");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("IP address: ");
  Serial.println(WiFi.localIP());
  
  Serial.print("Will send images to: ");
  Serial.println(serverURL);
}

void loop() {
  // Check if it's time to send an image
  if (millis() - lastSendTime > sendInterval) {
    if (sendImageToServer()) {
      Serial.println("Image sent successfully");
    } else {
      Serial.println("Failed to send image");
    }
    lastSendTime = millis();
  }
  
  delay(100);
}


