// Lampu genset untuk demo Pos Jaga Siber.
// ESP32 menerima '1' (nyalakan) atau '0' (matikan) lewat kabel USB dari
// lab/genset_tiruan.py --serial <port>, lalu menggerakkan modul relay.
//
// Rangkaian (pakai lampu 12V, JANGAN listrik rumah 220V):
//   ESP32 GPIO26 -> IN modul relay
//   ESP32 5V/VIN -> VCC modul relay, ESP32 GND -> GND modul relay
//   Adaptor 12V (+) -> COM relay, NO relay -> (+) lampu, (-) lampu -> (-) adaptor
// Lampu kecil di papan ESP32 (GPIO2) ikut menyala sebagai tanda.

const int PIN_RELAY = 26;
const int PIN_LED = 2;
const bool RELAY_AKTIF_LOW = true;  // kebanyakan modul relay murah menyala saat sinyal LOW

void setGenset(bool on) {
  digitalWrite(PIN_RELAY, (on ^ RELAY_AKTIF_LOW) ? HIGH : LOW);
  digitalWrite(PIN_LED, on ? HIGH : LOW);
}

void setup() {
  Serial.begin(115200);
  pinMode(PIN_RELAY, OUTPUT);
  pinMode(PIN_LED, OUTPUT);
  setGenset(true);  // genset dianggap menyala saat demo dimulai
}

void loop() {
  if (Serial.available()) {
    char c = Serial.read();
    if (c == '1') setGenset(true);
    if (c == '0') setGenset(false);
  }
}
