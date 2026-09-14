/*
 * Marine Caravan - Arduino Sensor Reader
 * Handles low-level sensor reading and motor control
 * Communicates with Raspberry Pi via UART (JSON format)
 */

#include <Wire.h>
#include <SPI.h>
#include <OneWire.h>
#include <DallasTemperature.h>

// One-Wire for Seawater Temperature
const int SEAWATER_TEMP_PIN = A7;
OneWire oneWire(SEAWATER_TEMP_PIN);
DallasTemperature seawaterSensor(&oneWire);

// Pin Definitions
const int MOTOR1_PWM_PIN = 9;
const int MOTOR2_PWM_PIN = 10;
const int MOTOR1_CURRENT_PIN = A0;
const int MOTOR2_CURRENT_PIN = A1;
const int MOTOR1_RPM_PIN = 2;
const int MOTOR2_RPM_PIN = 3;
const int LDR_PIN = A2;

// Water Level Sensors
const int FRESHWATER_PIN = A3;
const int GREYWATER_PIN = A4;

// Door/Window Sensors
const int FRONT_DOOR_PIN = 4;
const int REAR_DOOR_PIN = 5;
const int WINDOW1_PIN = 6;
const int WINDOW2_PIN = 7;
const int WINDOW3_PIN = 8;

// LED Strip Control
const int LED_STRIP1_PIN = 11;
const int LED_STRIP2_PIN = 12;

// Leak Sensors
const int LEAK1_PIN = A5;
const int LEAK2_PIN = A6;

// Variables
volatile long motor1Pulses = 0;
volatile long motor2Pulses = 0;
unsigned long lastReadTime = 0;
const unsigned long READ_INTERVAL = 1000; // 1 second

void setup() {
  Serial.begin(115200);
  
  // Initialize seawater temperature sensor
  seawaterSensor.begin();
  
  // Configure pins
  pinMode(MOTOR1_PWM_PIN, OUTPUT);
  pinMode(MOTOR2_PWM_PIN, OUTPUT);
  pinMode(MOTOR1_RPM_PIN, INPUT);
  pinMode(MOTOR2_RPM_PIN, INPUT);
  pinMode(LDR_PIN, INPUT);
  pinMode(FRONT_DOOR_PIN, INPUT_PULLUP);
  pinMode(REAR_DOOR_PIN, INPUT_PULLUP);
  pinMode(WINDOW1_PIN, INPUT_PULLUP);
  pinMode(WINDOW2_PIN, INPUT_PULLUP);
  pinMode(WINDOW3_PIN, INPUT_PULLUP);
  pinMode(LED_STRIP1_PIN, OUTPUT);
  pinMode(LED_STRIP2_PIN, OUTPUT);
  pinMode(LEAK1_PIN, INPUT);
  pinMode(LEAK2_PIN, INPUT);
  
  // Attach interrupts for RPM counters
  attachInterrupt(digitalPinToInterrupt(MOTOR1_RPM_PIN), countMotor1, RISING);
  attachInterrupt(digitalPinToInterrupt(MOTOR2_RPM_PIN), countMotor2, RISING);
  
  // Initialize I2C for sensors
  Wire.begin();
  
  Serial.println("{\"type\":\"init\",\"status\":\"ready\",\"seawater_sensor\":\"active\"}");
  delay(1000);
}

void loop() {
  if (millis() - lastReadTime >= READ_INTERVAL) {
    lastReadTime = millis();
    readAllSensors();
  }
  
  // Check for commands from Raspberry Pi
  if (Serial.available()) {
    processCommand();
  }
  
  delay(10);
}

void readAllSensors() {
  // Read seawater temperature
  seawaterSensor.requestTemperatures();
  float seawaterTemp = seawaterSensor.getTempCByIndex(0);
  
  // Read motor currents
  int motor1Current = analogRead(MOTOR1_CURRENT_PIN);
  int motor2Current = analogRead(MOTOR2_CURRENT_PIN);
  
  // Read RPM (pulses per second)
  int motor1RPM = motor1Pulses;
  int motor2RPM = motor2Pulses;
  motor1Pulses = 0;
  motor2Pulses = 0;
  
  // Read light sensor
  int lightLevel = analogRead(LDR_PIN);
  
  // Read water levels
  int freshwaterLevel = analogRead(FRESHWATER_PIN);
  int greywaterLevel = analogRead(GREYWATER_PIN);
  
  // Read door/window status
  bool frontDoor = digitalRead(FRONT_DOOR_PIN);
  bool rearDoor = digitalRead(REAR_DOOR_PIN);
  bool window1 = digitalRead(WINDOW1_PIN);
  bool window2 = digitalRead(WINDOW2_PIN);
  bool window3 = digitalRead(WINDOW3_PIN);
  
  // Read leak sensors
  bool leak1 = digitalRead(LEAK1_PIN);
  bool leak2 = digitalRead(LEAK2_PIN);
  
  // Build JSON response
  String jsonResponse = "{\"type\":\"sensors\",\"data\":{\"seawater\":{\"temperature\":";
  jsonResponse += seawaterTemp;
  jsonResponse += "},\"motors\":{\"motor1_current\":";
  jsonResponse += motor1Current;
  jsonResponse += ",\"motor1_rpm\":";
  jsonResponse += motor1RPM;
  jsonResponse += ",\"motor2_current\":";
  jsonResponse += motor2Current;
  jsonResponse += ",\"motor2_rpm\":";
  jsonResponse += motor2RPM;
  jsonResponse += "},\"environment\":{\"light\":";
  jsonResponse += lightLevel;
  jsonResponse += "},\"water\":{\"freshwater\":";
  jsonResponse += freshwaterLevel;
  jsonResponse += ",\"greywater\":";
  jsonResponse += greywaterLevel;
  jsonResponse += "},\"doors_windows\":{\"front_door\":\"";
  jsonResponse += (frontDoor ? "open" : "closed");
  jsonResponse += "\",\"rear_door\":\"";
  jsonResponse += (rearDoor ? "open" : "closed");
  jsonResponse += "\",\"window1\":\"";
  jsonResponse += (window1 ? "open" : "closed");
  jsonResponse += "\"},\"leaks\":{\"leak1\":";
  jsonResponse += leak1;
  jsonResponse += ",\"leak2\":";
  jsonResponse += leak2;
  jsonResponse += "}}}";
  
  Serial.println(jsonResponse);
}

void processCommand() {
  String command = Serial.readStringUntil('\n');
  
  if (command.indexOf("motor") >= 0) {
    parseMotorCommand(command);
  } else if (command.indexOf("led") >= 0) {
    parseLEDCommand(command);
  }
}

void parseMotorCommand(String cmd) {
  if (cmd.indexOf("1") >= 0) {
    int speed = extractValue(cmd, "speed");
    analogWrite(MOTOR1_PWM_PIN, speed);
  } else if (cmd.indexOf("2") >= 0) {
    int speed = extractValue(cmd, "speed");
    analogWrite(MOTOR2_PWM_PIN, speed);
  }
}

void parseLEDCommand(String cmd) {
  int brightness = extractValue(cmd, "brightness");
  analogWrite(LED_STRIP1_PIN, brightness);
}

int extractValue(String str, String key) {
  int startIdx = str.indexOf(key) + key.length() + 2;
  int endIdx = str.indexOf(",", startIdx);
  if (endIdx == -1) endIdx = str.indexOf("}", startIdx);
  return str.substring(startIdx, endIdx).toInt();
}

void countMotor1() {
  motor1Pulses++;
}

void countMotor2() {
  motor2Pulses++;
}
