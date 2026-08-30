#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <ArduinoJson.h>
#include <WiFi.h>
#include <esp_now.h>
#include <esp_wifi.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define OLED_RESET -1
#define OLED_SDA 5
#define OLED_SCL 6
#define STATUS_LED_PIN 7

Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

volatile bool newData = false;
char payloadBuffer[256];
int totalPackets = 0;

int latestPkt = 0;
float latestTemp = 0;
float latestHum = 0;
int latestSmoke = 0;
float latestAz = 0;
long latestD0 = 0, latestD90 = 0, latestD180 = 0;

unsigned long lastOledUpdate = 0;
const unsigned long oledInterval = 500;

void OnDataRecv(const uint8_t *mac_addr, const uint8_t *incomingData, int len) {
  memset(payloadBuffer, 0, sizeof(payloadBuffer));
  memcpy(payloadBuffer, incomingData, len);
  newData = true;
}

void setup() {
  Serial.begin(115200);
  delay(2000); // Allow USB serial to initialize
  pinMode(STATUS_LED_PIN, OUTPUT);

  Wire.begin(OLED_SDA, OLED_SCL);
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) display.begin(SSD1306_SWITCHCAPVCC, 0x3D);

  display.clearDisplay(); display.setTextSize(1); display.setTextColor(SSD1306_WHITE);
  display.setCursor(0, 10); display.println("BASE STATION READY");
  display.display();

  WiFi.mode(WIFI_STA);
  esp_wifi_set_channel(11, WIFI_SECOND_CHAN_NONE);

  esp_now_init();
  esp_now_register_recv_cb(OnDataRecv);
}

void loop() {
  // 1. FAST PATH: Catch ESP-NOW packets instantly and forward down USB Serial
  if (newData) {
    newData = false;
    totalPackets++;
    digitalWrite(STATUS_LED_PIN, HIGH);
    
    String payload = String(payloadBuffer);
    
    JsonDocument doc;
    DeserializationError error = deserializeJson(doc, payload);

    if (!error) {
      latestPkt = doc["_id"] | totalPackets;
      latestTemp = doc["temp"] | 0.0f; 
      latestHum = doc["humid"] | 0.0f;
      latestSmoke = doc["gas"] | 0;
      latestAz = doc["az"] | 0.0f;
      
      JsonArray scanArr = doc["scan"];
      if (!scanArr.isNull()) {
        latestD0 = scanArr[0] | -1; 
        latestD90 = scanArr[2] | -1; 
        latestD180 = scanArr[4] | -1;
      }

      // PRINT JSON DIRECTLY TO HOST PC VIA USB SERIAL
      Serial.println(payload);
    }
    digitalWrite(STATUS_LED_PIN, LOW);
  }

  // 2. SLOW PATH: Refresh OLED display safely
  if (millis() - lastOledUpdate >= oledInterval) {
    lastOledUpdate = millis();

    display.clearDisplay();
    display.setCursor(0, 0); display.printf("RX #%d | T:%.0fC H:%.0f%%", latestPkt, latestTemp, latestHum);
    display.drawLine(0, 9, 128, 9, SSD1306_WHITE);
    display.setCursor(0, 14); display.printf("Gas:%d | Z:%.1f", latestSmoke, latestAz);
    display.setCursor(0, 26); display.printf("Fwd(90): %ld cm", latestD90);
    display.setCursor(0, 38); display.printf("L:%ld | R:%ld cm", latestD180, latestD0);
    display.drawLine(0, 52, 128, 52, SSD1306_WHITE);
    display.setCursor(0, 55); display.println("STATUS: USB BRIDGE [OK]");
    display.display();
  }
}