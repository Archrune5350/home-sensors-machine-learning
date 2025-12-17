#include <Arduino.h>
#include <DHT.h>
#include <ArduinoJson.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <HTTPClient.h>

// ---------------- WiFi ----------------

const char* ssid = "ZenphoneWifi";
const char* password = "Cxg57rn@vch68tms";

// ---------------- DHT11 ----------------
#define DHT11_PIN 4
DHT dht(DHT11_PIN, DHT11);

// ---------------- MQ7 ----------------
#define MQ7_PIN 5   // ADC pin, vælg en, der ikke konflikter med WiFi
const int samples = 100;
float RsR0_MQ7_air = 11.8;
float RL_MQ7 = 0.74;
float R0_MQ7 = 0.10;

// ---------------- Funktionsprototyper ----------------
float readValueMQ(int MQ_PIN, float RL, float R0);
float kalibrerMQSensor(int PIN, float RL, float RsR0_air, float R0);

// ---------------- Setup ----------------
void setup() {
  Serial.begin(115200);
  delay(1000);

  dht.begin();

  // ---------------- WiFi ----------------
  Serial.println("Connecting to WiFi...");
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi connected!");
  Serial.print("IP: "); Serial.println(WiFi.localIP());

  // ---------------- Kalibrer MQ7 ----------------
  R0_MQ7 = kalibrerMQSensor(MQ7_PIN, RL_MQ7, RsR0_MQ7_air, R0_MQ7);
}

// ---------------- Loop ----------------
void loop() {
  // Reconnect WiFi hvis tabt
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("WiFi disconnected! Reconnecting...");
    WiFi.begin(ssid, password);
    while (WiFi.status() != WL_CONNECTED) {
      delay(500);
      Serial.print(".");
    }
    Serial.println("\nWiFi reconnected!");
  }

  // ---------------- Læs DHT11 ----------------
  float temp = dht.readTemperature();
  float hum  = dht.readHumidity();
  if (isnan(temp) || isnan(hum)) {
    Serial.println("DHT fejl");
    delay(2000);
    return;
  }

  // ---------------- Læs MQ7 ----------------
  float ratio = readValueMQ(MQ7_PIN, RL_MQ7, R0_MQ7);

  // ---------------- JSON ----------------
  StaticJsonDocument<200> doc;
  doc["temp"]  = temp;
  doc["hum"]   = hum;
  doc["ratio"] = ratio;
  String json;
  serializeJson(doc, json);

  // ---------------- HTTPS POST ----------------
  WiFiClientSecure client;
  client.setInsecure(); // spring certifikat check over

  HTTPClient https;
  String url = "https://a783198ff194.ngrok-free.app/upload";
  https.begin(client, url);
  https.addHeader("Content-Type", "application/json");

  // Retry mekanisme
  int retries = 3;
  int httpCode = -1;
  while(retries-- > 0) {
    httpCode = https.POST(json);
    if(httpCode > 0) break;
    Serial.println("POST failed, retrying...");
    delay(1000);
  }

  if(httpCode > 0) {
    Serial.println("POST success, code: " + String(httpCode));
    Serial.println("Response: " + https.getString());
  } else {
    Serial.println("POST failed after retries: " + https.errorToString(httpCode));
  }

  https.end();

  delay(10000); // 10 sekunders interval mellem posts
}

// ---------------- MQ7 funktioner ----------------
float readValueMQ(int MQ_PIN, float RL, float R0) {
  int raw_adc = analogRead(MQ_PIN);
  float voltage_divider = raw_adc * (3.3 / 4095.0);
  float voltage_sensor = voltage_divider * (1000 + 2000) / 2000;
  float rs = (3.3 - voltage_sensor) * RL / voltage_sensor;
  float ratio = rs / R0;
  return ratio;
}

float kalibrerMQSensor(int PIN, float RL, float RsR0_air, float R0) {
  float rs_sum = 0.0;
  for (int i = 0; i < samples; i++) {
    int raw_adc = analogRead(PIN);
    float voltage_divider = raw_adc * (3.3 / 4095.0);
    float voltage_sensor = voltage_divider * (1000 + 2000) / 2000;
    float rs = (3.3 - voltage_sensor) * RL / voltage_sensor;
    rs_sum += rs;
    delay(100);
  }

  float rs_avg = rs_sum / samples;
  R0 = rs_avg / RsR0_air;
  Serial.print("Kalibreret R0: ");
  Serial.println(R0);
  delay(1000);
  return R0;
}