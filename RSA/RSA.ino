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
  const char* private_key = R"(
  -----BEGIN RSA PRIVATE KEY-----
  MIIEowIBAAKCAQEAyN+uFRL6ZuEX8dX+JNZ4KLiItmGt4t3g/JbJxLFuSoMnyXDm
  C8BNa8v2D8N6ZSt1BTX6LTaLczH5RhpDvt5JtpTUcyK9alcddzA2+s3WCc5A9W2K
  azHfeEu0riS67UJCzF7DznxOb02QHPH93fUm//gu3A5LszHiDdtZ/TMjF4Rn7sg+
  Ii4qN11Xs5HQ0lgHrbWGZobkLHDheGSHMjEKy9LGES3U+ATrzMkzMeQdbpNSE1uB
  3URfF+kyR2UWFQwtyaODdn6S8K4uUyn9ndUo5ehSX/0e1PYRFuTJACOqHgR+7or1
  0tcfZYZ+Bm+X1iTkP6kZRuA6YTTErBTT9eq9HwIDAQABAoIBAAqWRao4ri07C6Yk
  WfV+aZf1nXGpI58nElpBSn6l91vQ5ZeZYAhTMDpQV/2Plyxlpklfd0FLdFLCEr2e
  IInwODKWTb2IoYgwuMa8KiRSh2P26fBwMXEa5bNMLp3HeusYxQxK4sdHzwy0RmD3
  R7ENNbI5HTHPtqF0n0ONQb3uebVWurRMRcWL/lah8lS+8/3f2hqOY8YT9DJODORS
  D7LEFPwYpBHOexlT/h2hzItphJcYbBgFnI3PYny6icLR9wmqGG8UFoHBuMIpo6py
  KxmLf0HIrMdFw9FNBPjXYpGFsQPFJvPqsGHbYtt2u+rD+sZi7+hkZMJQCqjetZR3
  j4VpB9ECgYEA4FY01J+plD45kshuF3BQ+OqvLnMSv0I0qPPsQ+ty+7BxrLVxc7RC
  VO07GTUD4DpcKULenbs4/HxnvnRSDbgkJTxWJPtCCoxSISvAg7XKOWuZ2T32nngI
  VetQlKVeI4SAGT9JWvUSawCfNRuq8NK6mZl9X1n/0aZ3SnJFLkLJFCcCgYEA5Tmz
  4J37f7NeWN2jS3ehlpNKlj0LgctYFvlFA+m2QzRb4/iN8RoxB0I/xApX+71zNg5l
  NtJkbrI5WiEtsQaYHTeP+J5IsMjpbOED9NezleTBsBrpSykLRj6EfqpZ9DbAUZxk
  T0DvM6S/FAlNhLh3LIi/62XhGlbY9x7bHpMU0kkCgYB000/l3lPAWHtA/lGesSXp
  ysV5ygFcSo0D4ysJ38ZcXfGEwGSZnajhcz1QjjQ7hAjUj/dAauxtSBf6rbbBYECq
  h3ZRAevNdG+cyJ0TugraxjczU7pnohitLcMj9c5Fbs4K19NKo894m7VNQeBOU19L
  eAw7KLI5Kph603FFexAeBwKBgG0RMpxqrzMI1ph0BPGwn2s09CVeMG52oZh0zLja
  6EU70Yk8R9Vzf+aTSCHwRgLbFsmeudwG6ZCeLpnK9aGooJIuUMucDLxJLIAI5MgI
  JkPpD5vKgjyn79xhfMuEJL8FmiZ6wmPPYsFw3xYagw7mcpX3D1JjLGNK9XtH7Dy1
  ARA5AoGBAMzg68jYE9px3RGILk43MYRqSZFtlxmCPws67kY2eFD2z5Tf8YY2Zjs5
  34FHl45QF1jtVzukxC3TeCPFB6sfNebe6yAG9CD00d6x8Kq6bQ3hL/M5KWbU1rNd
  qd0ejqAm01yq4/VJEriZFODeRBEpfSQ4PWVT0wgQj+TiUt7c0Q3e
  -----END RSA PRIVATE KEY-----)";

  Serial.println(private_key);
  Serial.println("Private key sent.");
}

