/*
  Proporciona una interfaz de alto nivel para el control de temperatura. El firmware 
  escanea el puerto serie en busca de comandos. Los comandos no distinguen entre 
  mayúsculas y minúsculas. Cualquier comando no reconocido da como resultado un 
  modelo de suspensión. Cada comando devuelve una cadena de resultado.
  Firmware modificado de TCLab: Sensor diferente (LM35) y solo un calefactor de uso
  A             reinicio de software. Devuelve "Inicio".
  LED float     ajusta el LED a un valor float por 10 seg. rango 0 to 100. retorna el valor del float
  Pot float     ajusta pwm para limitar la potencia del calentador, range 0 to 255. Retorna P1.
  Nivel float   establece Calentador, rango de 0 a 100. Devuelve el valor de nivel.
  R             obtiene el valor del Calentador, rango de 0 a 100
  SCAN          obtiene valores T1 nivel en valores delimitados por línea
  T             obtiene Temperatura T1. Devuelve valor de T1 en °C.
  VER           obtiene version del firmware
  X             para detener, entra en modo sleep. Devuelve "Stop"
  Los límites de la potencia del calentador se pueden configurar con las siguientes 
  constantes. El estado se indica mediante el LED1. Las condiciones de estado son:
      LED        LED
      Brillo     Estado
      ----------  -----
      tenue      continuo      Funcionamiento normal, calentador apagado
      brillante  continuo      Funcionamiento normal, calentador encendido
      tenue      parpadeando   alarma de temperatura alta encendida, calentador apagado
      brillante  parpadeando   alarma de temperatura alta encendida,  calentador encendido
  Se apaga el calefactor si no recibe comandos del host durante un período de tiempo de espera 
  (configure a continuación), recibe un comando "X" o recibe un comando no reconocido del host.
  Las constantes se utilizan para configurar el firmware. Registro de cambios ordenado por versión semántica
  
*/

#include "Arduino.h"

// determine board type
#if defined(__AVR_ATmega328P__) || defined(__AVR_ATmega168__)
  String boardType = "Arduino Uno";
#elif defined(__AVR_ATmega32U4__) || defined(__AVR_ATmega16U4__)
  String boardType = "Arduino Leonardo/Micro";
#elif defined(__AVR_ATmega1280__) || defined(__AVR_ATmega2560__)
  String boardType = "Arduino Mega";
#else 
  String boardType = "Unknown board";
#endif
//############################################################
// constantes
const String vers = "Drogon-TCLab";   // version del firmware
const long baud = 38400;              // radio serial baud
const char sp = ' ';                  // separador
const char nl = '\n';                 // fin de linea
const int OFF = 0;                    // Valor de apagado del calentador
// Habilitar depuracion
const bool DEBUG = false;
//############################################################
// numeros de pin usados
const int pinTemp = 0;         // T, conexion con el sensor LM35
const int pinNivel = 3;        // Nivel, conexion de accion con el transistor
const int pinLED = 9;          // LED

// temperatura para las alarmas
const int limTemp   = 40;       // Temperatura alarma de calor (°C)

// LED nivel
const int hiLED   =  60;       // brillo alto LED
const int loLED   = hiLED/16;  // brillo bajo LED

// variables globales
char Buffer[64];               // buffer de analisis de entrada serial
int buffer_index = 0;          // index de Buffer
String cmd;                    // comando
float val;                     // valor del comando
int ledStatus;                 // 1: loLED operacion normal, calefactor apagado
                               // 2: hiLED operacion normal, calefactor encendido
                               // 3: loLED parpadeo alarma de temperatura alta, calefactor apagado
                               // 4: hiLED parpadeo alarma de temperatura alta, alefactor encendido
long ledTimeout = 0;           // para configurar brillo de led por orden o en inicio
float LED = 100;               // LED brillo
float Pot = 204;               // 80 % límite de potencia del calentador en unidades de pwm. Rango 0 a 255
float Nivel = 0;               // último valor escrito en el calentador en unidades de porcentaje
int alarmStatus;               // estado de alarma de alta temperatura
boolean newData = false;       // bandera que indica un nuevo comando
int n =  10;                   // número de muestras para cada medición de temperatura

// lectura de comando. comunicacion E/S como el Monitor serial del IDE de arduino
void readCommand() {
  while (Serial && (Serial.available() > 0) && (newData == false)) {
    int byte = Serial.read();
    if ((byte != '\r') && (byte != nl) && (buffer_index < 64)) {
      Buffer[buffer_index] = byte;
      buffer_index++;
    }
    else {
      newData = true;
    }
  }   
}

// para debugging con el monitor serial del IDE Arduino
void echoCommand() {
  if (newData) {
    Serial.write("Comando recibido: ");
    Serial.write(Buffer, buffer_index);
    Serial.write(nl);
    Serial.flush();
  }
}

// retorno promedio de n lecturas de temperatura del termistor en °C
inline float readTemperature(int pin) {
  float degC = 0.0;
  for (int i = 0; i < n; i++) {
      degC += analogRead(pin) * 0.488758553;     // sensor LM35  { 5.0/1023.0)/0.01 }
  }
  return degC / float(n);
}
//analizador del comando
void parseCommand(void) {
  if (newData) {
    String read_ = String(Buffer);

    // separar el comando de los datos asociados
    int idx = read_.indexOf(sp);
    cmd = read_.substring(0, idx);
    cmd.trim();
    cmd.toUpperCase();

    // extrae data.toFloat() returna 0 si error
    String data = read_.substring(idx + 1);
    data.trim();
    val = data.toFloat();

    // restablecer parámetro para el siguiente comando
    memset(Buffer, 0, sizeof(Buffer));
    buffer_index = 0;
    newData = false;
  }
}

// respuestas despues de orden por comando
void sendResponse(String msg) {
  Serial.println(msg);
}
void sendFloatResponse(float val) {
  Serial.println(String(val, 3));
}

// Despacha el comando a funcion correspondiente
void dispatchCommand(void) {
  if (cmd == "A") {
    dracarys(OFF);
    sendResponse("Start");
  }
  else if (cmd == "LED") {
    ledTimeout = millis() + 10000;
    LED = max(0, min(100, val));
    sendResponse(String(LED));
  }
  else if (cmd == "P") {
    Pot = max(0, min(255, val));
    sendResponse(String(Pot));
  }
  else if (cmd == "Q") {
    dracarys(val);
    sendFloatResponse(Nivel);
  }
  else if (cmd == "R") {
    sendFloatResponse(Nivel);
  }
  else if (cmd == "SCAN") {
    sendFloatResponse(readTemperature(pinTemp));
    sendFloatResponse(Nivel);
  }
  else if (cmd == "T") {
    sendFloatResponse(readTemperature(pinTemp));
  }
  else if (cmd == "VER") {
    sendResponse("Firmware " + vers + " " + boardType);
  }
  else if (cmd == "X") {
    dracarys(OFF);
    sendResponse("Stop");
  }
  else if (cmd.length() > 0) {
    dracarys(OFF);
    sendResponse(cmd);
  }
  Serial.flush();
  cmd = "";
}

void checkAlarm(void) {
  if ((readTemperature(pinTemp) > limTemp)) {
    alarmStatus = 1;
  }
  else {
    alarmStatus = 0;
  }
}

void updateStatus(void) {
  // determina estado del led
  ledStatus = 1;
  if ((Nivel > 0)) {
    ledStatus = 2;
  }
  if (alarmStatus > 0) {
    ledStatus += 2;
  }
  // actualiza el led dependiendo de ledStatus
  if (millis() < ledTimeout) {        // funcionamiento del led de orden o inicio
    analogWrite(pinLED, LED);
  }
  else {
    switch (ledStatus) {
      case 1:  //  operacion normal, calefactor apagado. Led tenue y continuo
        analogWrite(pinLED, loLED);
        break;
      case 2:  // operacion normal, calefactor encendido. Led brillante y continuo
        analogWrite(pinLED, hiLED);
        break;
      case 3:  // alarma de temperatura alta, alefactor apagado. LED tenue y parpadeante
        if ((millis() % 2000) > 1000) {
          analogWrite(pinLED, loLED);
        } else {
          analogWrite(pinLED, loLED/4);
        }
        break;
      case 4:  // alarma de temperatura alta, calefactor encendido. LED brillante y parpadeante
        if ((millis() % 2000) > 1000) {
          analogWrite(pinLED, hiLED);
        } else {
          analogWrite(pinLED, loLED);
        }
        break;
    }   
  }
}

// alimentar calefactor
void dracarys(float qval) {
  Nivel = max(0., min(qval, 100.));
  analogWrite(pinNivel, (Nivel*Pot)/100);
}

// arduino startup
void setup() {
  while (!Serial) {
    ; // esperar conexion a puerto serial.
  }
  Serial.begin(baud);
  Serial.flush();
  dracarys(OFF);
  ledTimeout = millis() + 1000;
}

// arduino loop de eventos
void loop() {
  readCommand();
  //if (DEBUG) echoCommand();
  parseCommand();
  dispatchCommand();
  checkAlarm();
  updateStatus();
}
