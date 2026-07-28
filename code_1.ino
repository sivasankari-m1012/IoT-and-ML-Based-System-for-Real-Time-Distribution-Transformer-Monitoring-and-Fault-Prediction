#include <ESP8266WiFi.h>
#include <ESP8266HTTPClient.h>

const char* ssid = "Varshu";
const char* password = "13173024";

void setup() {
  Serial.begin(115200);
  WiFi.begin(ssid, password);

  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
  }
}

void loop() {

  if (Serial.available()) {

    String data = Serial.readStringUntil('\n');
    data.trim();

    Serial.println("Received: " + data); // DEBUG

    float temp = 0, voltage = 0, current = 0, oil = 0;

    int tIndex = data.indexOf("T=");
    int vIndex = data.indexOf("V=");
    int iIndex = data.indexOf("I=");
    int oIndex = data.indexOf("O=");

    // ✔ Check if all values exist
    if (tIndex != -1 && vIndex != -1 && iIndex != -1 && oIndex != -1) {

      temp = data.substring(tIndex + 2, vIndex).toFloat();
      voltage = data.substring(vIndex + 2, iIndex).toFloat();
      current = data.substring(iIndex + 2, oIndex).toFloat();
      oil = data.substring(oIndex + 2).toFloat();

      String url = "http://172.29.189.247:5000/data?";
      url += "temp=" + String(temp);
      url += "&voltage=" + String(voltage);
      url += "&current=" + String(current);
      url += "&oil=" + String(oil);

      Serial.println("Sending: " + url); // DEBUG

      WiFiClient client;
      HTTPClient http;

      http.begin(client, url);
      int httpCode = http.GET();

      Serial.println("Response: " + String(httpCode));

      http.end();
    }
  }

  delay(2000);
}