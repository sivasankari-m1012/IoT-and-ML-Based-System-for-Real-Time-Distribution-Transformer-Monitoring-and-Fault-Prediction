// ESP32 -> Flask. Keep your existing sensor code; just fill the four read*() functions.
#include <WiFi.h>
#include <HTTPClient.h>

const char* WIFI_SSID = "YOUR_WIFI";
const char* WIFI_PASS = "YOUR_PASSWORD";
const char* SERVER    = "http://192.168.1.50:5000";   // PC running `python run.py` with HOST=0.0.0.0
const char* API_KEY   = "same-value-as-API_KEY-in-.env";
const int   TRANSFORMER_ID = 1;
const unsigned long INTERVAL_MS = 5000;

float readTemperature() { /* TODO: your temperature sensor, °C */ return 0; }
float readVoltage()     { /* TODO: your voltage sensor, V     */ return 0; }
float readCurrent()     { /* TODO: your current sensor, A     */ return 0; }
float readOilDistance() { /* TODO: ultrasonic distance to oil surface, cm */ return 0; }

void connectWifi() {
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  while (WiFi.status() != WL_CONNECTED) { delay(500); Serial.print("."); }
  Serial.println("\nWiFi connected");
}

void setup() { Serial.begin(115200); connectWifi(); }

void loop() {
  if (WiFi.status() != WL_CONNECTED) connectWifi();

  char body[128];
  snprintf(body, sizeof(body),
           "{\"temperature\":%.1f,\"voltage\":%.2f,\"current\":%.2f,\"oil\":%.1f}",
           readTemperature(), readVoltage(), readCurrent(), readOilDistance());

  HTTPClient http;
  http.begin(String(SERVER) + "/api/v1/transformers/" + TRANSFORMER_ID + "/readings");
  http.addHeader("Content-Type", "application/json");
  http.addHeader("X-API-Key", API_KEY);          // NEW in v2: shared secret
  int code = http.POST(body);
  Serial.printf("POST %s -> HTTP %d\n", body, code);
  http.end();

  delay(INTERVAL_MS);
}
