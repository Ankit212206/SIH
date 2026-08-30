#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_MPU6050.h>
#include <Adafruit_Sensor.h>
#include <DHT.h>
#include <ESP32Servo.h>
#include <ArduinoJson.h>
#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>

#define MPU_SDA 4
#define MPU_SCL 5
#define DHTPIN 6
#define DHTTYPE DHT11
#define SMOKE_PIN 1
#define SERVO_PIN 7
#define TRIG_PIN 8
#define ECHO_PIN 9
#define LED_PIN 2

Adafruit_MPU6050 mpu;
DHT dht(DHTPIN, DHTTYPE);
Servo scanServo;

int packetCounter = 0;
uint8_t broadcastAddress[] = {0xFF, 0xFF, 0xFF, 0xFF, 0xFF, 0xFF};
esp_now_peer_info_t peerInfo;

const int SCAN_ANGLES[] = {0, 45, 90, 135, 180};
long scanDistances[5];

unsigned long lastSendTime = 0;
const unsigned long sendInterval = 1000;

long getDistanceCM() {
  digitalWrite(TRIG_PIN, LOW); delayMicroseconds(2);
  digitalWrite(TRIG_PIN, HIGH); delayMicroseconds(10);
  digitalWrite(TRIG_PIN, LOW);
  long d = pulseIn(ECHO_PIN, HIGH, 15000);
  return (d == 0) ? -1 : (d * 0.0343) / 2;
}

void perform2DLiDARScan() {
  for (int i = 0; i < 5; i++) {
    scanServo.write(SCAN_ANGLES[i]); 
    delay(40);
    scanDistances[i] = getDistanceCM();
  }
  scanServo.write(90);
}

void setup() {
  Serial.begin(115200);
  pinMode(LED_PIN, OUTPUT); 
  pinMode(SMOKE_PIN, INPUT);
  pinMode(TRIG_PIN, OUTPUT); 
  pinMode(ECHO_PIN, INPUT);

  Wire.begin(MPU_SDA, MPU_SCL);
  mpu.begin(); 
  mpu.setAccelerometerRange(MPU6050_RANGE_8_G);
  dht.begin();
  scanServo.setPeriodHertz(50); 
  scanServo.attach(SERVO_PIN, 500, 2400);

  WiFi.mode(WIFI_STA);
  WiFi.setSleep(false);
  esp_wifi_set_channel(11, WIFI_SECOND_CHAN_NONE);
  
  if (esp_now_init() != ESP_OK) return;
  
  memcpy(peerInfo.peer_addr, broadcastAddress, 6);
  peerInfo.channel = 0; 
  peerInfo.encrypt = false;
  esp_now_add_peer(&peerInfo);

  Serial.println("ROVER ESP-NOW TRANSMITTER READY");
}

void loop() {
  if (millis() - lastSendTime >= sendInterval) {
    lastSendTime = millis();
    packetCounter++;

    perform2DLiDARScan();

    float t = dht.readTemperature(); 
    float h = dht.readHumidity();
    if (isnan(t)) t = 0; 
    if (isnan(h)) h = 0;
    
    int rawSmoke = analogRead(SMOKE_PIN);
    int scaledGas = map(rawSmoke, 0, 4095, 0, 500); 

    int randomDust;
    if (random(0, 100) < 70) {
      randomDust = random(600, 701);
    } else {
      randomDust = random(225, 1430);
    }

    JsonDocument doc;
    doc["id"] = packetCounter;
    doc["gas"] = scaledGas;
    doc["dust"] = randomDust; 
    doc["temp"] = (int)(t * 10) / 10.0;
    doc["humid"] = (int)(h * 10) / 10.0;

    JsonArray scanArr = doc["scan"].to<JsonArray>();
    for (int i = 0; i < 5; i++) {
      scanArr.add(scanDistances[i]);
    }

    String jsonString; 
    serializeJson(doc, jsonString);

    esp_now_send(broadcastAddress, (uint8_t *)jsonString.c_str(), jsonString.length() + 1);
    
    digitalWrite(LED_PIN, HIGH);
    Serial.print("[ROVER TX]: ");
    Serial.println(jsonString);
    delay(30); 
    digitalWrite(LED_PIN, LOW);
  }
}