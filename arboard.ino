#include <LiquidCrystal.h> #include <Adafruit_Sensor.h> #include "DHT.h"
#include <math.h>

//	LCD
LiquidCrystal lcd(13, 12, 11, 10, 9, 8);

//	Ultrasonic
const int trigPin = 7; const int echoPin = 6; long duration;
int distanceCm;

//	Current Sensor const int sensorIn = A1;
int mVperAmp = 185;	// adjust based on sensor double CurrentVoltage = 0;
double VRMS = 0; double AmpsRMS = 0;

//	DC Voltage Sensor
#define VOLTAGE_SENSOR A3	// 12V input through voltage divider

//	DHT11
#define DHTPIN 4
#define DHTTYPE DHT11 DHT dht(DHTPIN, DHTTYPE);

//	Variables
int temp_signal = 0; int Oil_signal = 0; int theft;
int t; int v;

//	Setup
void setup()
{
dht.begin();
lcd.begin(16, 2); Serial.begin(9600);

pinMode(trigPin, OUTPUT); pinMode(echoPin, INPUT);

pinMode(2, INPUT);	// Fire sensor pinMode(3, OUTPUT);	// Buzzer pinMode(5, OUTPUT);	// Buzzer pinMode(A5, OUTPUT); // Relay

pinMode(A0, INPUT); pinMode(A1, INPUT); pinMode(A2, INPUT); pinMode(A3, INPUT);

lcd.setCursor(0, 0); lcd.print("Transfor TX Line"); lcd.setCursor(0, 1);
lcd.print(" Monitor System "); delay(2000);
lcd.clear();
}

//	Loop
void loop()
{
// -------- Current Sensor --------CurrentVoltage = getVPP();
VRMS = (CurrentVoltage / 2.0) * 0.707; AmpsRMS = (VRMS * 1000) / mVperAmp;

// -------- 12V DC Voltage Reading --------
int value = analogRead(VOLTAGE_SENSOR);
float voltage = (value * 5.0 / 1023.0) * 3.0; // adjust multiplier v = (int)voltage;

// -------- LCD Display --------
lcd.setCursor(0, 0); lcd.print("V:"); lcd.print(v); lcd.print(" ");

lcd.setCursor(8, 0); lcd.print("C:"); lcd.print(AmpsRMS, 1);

//	Serial
Serial.print('V'); Serial.print(v); delay(10);

Serial.print('C'); Serial.print(AmpsRMS, 1); delay(100);

// -------- Overload prediction --------if (AmpsRMS > 0.35)
{
lcd.setCursor(0, 1); lcd.print("OL "); digitalWrite(3, HIGH); theft = 1;
}
else
{
lcd.setCursor(0, 1); lcd.print("NL "); digitalWrite(3, LOW);

theft = 0;
}

//	Sensors dht11(); ultrasonic();

//	Buzzer
if ((Oil_signal == 1) || (temp_signal == 1) || (theft == 1))
{
digitalWrite(5, HIGH);
}
else
{
digitalWrite(5, LOW);
}

// -------- Serial Data --------Serial.print('T'); Serial.print(t);
delay(10);

Serial.print('O'); Serial.print(distanceCm); delay(10);
}

//	Ultrasonic
void ultrasonic()
{
digitalWrite(trigPin, LOW); delayMicroseconds(2);

digitalWrite(trigPin, HIGH); delayMicroseconds(10);

digitalWrite(trigPin, LOW);

duration = pulseIn(echoPin, HIGH);

distanceCm = duration * 0.034 / 2;

lcd.setCursor(4, 1); lcd.print("OL:"); lcd.print(distanceCm);

if (distanceCm < 7)
{
lcd.setCursor(12, 1); lcd.print("F");
Oil_signal = 1;	// LOW oil → alert
}
else
{
lcd.setCursor(12, 1); lcd.print("L"); Oil_signal = 0;
}
}

//	DHT11
void dht11()
{
int h = dht.readHumidity(); t = dht.readTemperature();

if (isnan(h) || isnan(t))
{
return;
}

lcd.setCursor(0, 1); lcd.print("T:"); lcd.print(t); lcd.print((char)223);

lcd.print("C ");

if (t > 40)
{
temp_signal = 1;
}
else
{
temp_signal = 0;
}
}

//	Current Sensor float getVPP()
{
float result; int readValue;
int maxValue = 0;
int minValue = 1024;

uint32_t start_time = millis();
while ((millis() - start_time) < 1000)
{
readValue = analogRead(sensorIn);

if (readValue > maxValue) maxValue = readValue;

if (readValue < minValue) minValue = readValue;
}

result = ((maxValue - minValue) * 5.0) / 1024.0; return result;
}

