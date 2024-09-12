void setup() {
  Serial.begin(115200);  // 初始化 USB 串口，设置波特率

  uint64_t chipid = ESP.getEfuseMac(); // The chip ID is essentially its MAC address
  Serial.printf("ESP32 Chip ID = %04X%08X\n", (uint16_t)(chipid>>32), (uint32_t)chipid);
  Serial.println("等待序列埠");
  while (!Serial) {
    Serial.print("."); 
  }

  Serial.println("ESP32 準備讀取序列埠");
}

void loop() {
  if (Serial.available()) {
    String command = Serial.readStringUntil('\n');
    command.trim(); 

    if (command == "/getprivate") {
      sendPrivateKey();
    } else {
      Serial.println("Unknown command received: " + command);
    }
  }
}

void sendPrivateKey() {
  const char* private_key = "Place your RSA Private_key";

  Serial.println(private_key);
  Serial.println("Private key sent.");
}

