#include <SPI.h>
#include <MFRC522.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

#define SS_PIN 5
#define RST_PIN 22

#define OLED_SDA 16
#define OLED_SCL 17

#define TAMPER_PIN 15
#define BUTTON_PIN 12
// Removed LED_PIN as requested

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64

MFRC522 rfid(SS_PIN, RST_PIN);
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

int checkpoint = 1;
bool lastButtonState = HIGH;

void showCheckpoint() {
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(2);
  display.setCursor(0, 0);
  display.println("Checkpoint");
  display.setTextSize(4);
  display.setCursor(52, 25);
  display.println(checkpoint);
  display.display();
}

void setup() {
  Serial.begin(115200);

  pinMode(TAMPER_PIN, INPUT_PULLDOWN);
  pinMode(BUTTON_PIN, INPUT_PULLUP);

  SPI.begin();
  rfid.PCD_Init();

  Wire.begin(OLED_SDA, OLED_SCL);
  display.begin(SSD1306_SWITCHCAPVCC, 0x3C);

  showCheckpoint();
}

void loop() {
  bool isTampered = (digitalRead(TAMPER_PIN) == LOW);

  // Handle Button Press
  bool buttonState = digitalRead(BUTTON_PIN);
  if (lastButtonState == HIGH && buttonState == LOW) {
    checkpoint++;
    if (checkpoint > 4)
      checkpoint = 1;
    
    // Only show checkpoint if not tampered
    if (!isTampered) {
      showCheckpoint();
    }
    delay(250);
  }
  lastButtonState = buttonState;

  // Read RFID Card
  if (!rfid.PICC_IsNewCardPresent() || !rfid.PICC_ReadCardSerial()) {
    // Continuous Display Update if no card is actively being scanned
    if (isTampered) {
      display.clearDisplay();
      display.setTextColor(SSD1306_WHITE);
      display.setTextSize(2);
      display.setCursor(15, 25);
      display.println("TAMPERED");
      display.display();
    } else {
      // Small optimization: normally you wouldn't redraw every loop, 
      // but it's fine for this demo if we just keep showing the checkpoint
      // when not tampered.
    }
    return;
  }

  // Card is present! Read UID
  String uid = "";
  for (byte i = 0; i < rfid.uid.size; i++) {
    if (rfid.uid.uidByte[i] < 0x10)
      uid += "0";
    uid += String(rfid.uid.uidByte[i], HEX);
    if (i < rfid.uid.size - 1)
      uid += " ";
  }
  uid.toUpperCase();

  // Print format: UID, Checkpoint, TamperStatus
  // e.g., A1 B2 C3 D4, 2, 1
  Serial.print(uid);
  Serial.print(", ");
  Serial.print(checkpoint);
  Serial.print(", ");
  Serial.println(isTampered ? "1" : "0");

  // Show scan result on OLED
  display.clearDisplay();
  display.setTextColor(SSD1306_WHITE);
  display.setTextSize(1);
  display.setCursor(0, 0);
  display.println(isTampered ? "UID (TAMPERED!):" : "UID:");
  display.setTextSize(2);
  display.setCursor(0, 15);
  display.println(uid);
  display.setCursor(0, 45);
  display.print("CP: ");
  display.println(checkpoint);
  display.display();

  rfid.PICC_HaltA();
  rfid.PCD_StopCrypto1();

  delay(500);
  
  // Re-draw normal checkpoint screen after scan if not tampered
  if (!isTampered) {
    showCheckpoint();
  }
}
