/*
 * Global variables
 */
// Acceleration values recorded from the readAccelSensor() function
int ax = 0; int ay = 0; int az = 0;
int ppg = 0;        // PPG from readPhotoSensor() (in Photodetector tab)
int sampleTime = 0; // Time of last sample (in Sampling tab)
bool sending;
const int LED_PIN = 14;
// Define pin for firing button
const int BUTTON_PIN = 13;
bool lastButtonState = HIGH;
bool currentButton = HIGH;
bool firing = false;
unsigned long pressTime = 0;

void setup() {
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  pinMode(LED_PIN, OUTPUT);
  setupAccelSensor();
  setupCommunication();
  setupDisplay();
  setupPhotoSensor();
  sending = false;

  writeDisplay("Ready...", 1, true);
  writeDisplay("Set...", 2, false);
  writeDisplay("Play!", 3, false);
}

/*
 * The main processing loop
 */
void loop() {
  // Parse command coming from Python (either "stop" or "start")
  readPhotoSensor();
  currentButton = digitalRead(BUTTON_PIN);
  String command = receiveMessage();
  if(command == "stop") {
    sending = false;
    writeDisplay("Controller: Off", 0, true);
  }
  else if(command == "start") {
    sending = true;
    writeDisplay("Controller: On", 0, true);
  }

  // Send the orientation of the board
  if(sending && sampleSensors()) {
    sendMessage(String(getOrientation()));
  }
  if(command == "died once") {
    analogWrite(LED_PIN, 30);
  }
  else if(command == "died twice") {
    analogWrite(LED_PIN, 90);
  }
  else if(command == "died thrice") {
    analogWrite(LED_PIN, 200);
  }
  else if(command == "dead") {
    analogWrite(LED_PIN, 0);
  }
  else if(command == "reset") {
    analogWrite(LED_PIN, 0);
  }
  if (command.startsWith("Score: ")) {
  String scoreValue = command.substring(7); // Extract numeric score
  String scoreCount = "Your Score: " + scoreValue;
  writeDisplay(scoreCount.c_str(), 2, true);
  }

  if (command.startsWith("Highest Score: ")) {
  String scoreValue = command.substring(15); // Extract numeric score
  String highscoreCount = "Top Score: " + scoreValue;
  writeDisplay(highscoreCount.c_str(), 1, true);
  }
  // Check for button press (fires once per press)
  if (currentButton == LOW && lastButtonState == HIGH) {  
    sendMessage("2"); // Fire once when pressed
    pressTime = millis();
  }
  if (currentButton == LOW && millis() - pressTime >= 300) {
    sendMessage("2"); // Fire repeatedly if held
    pressTime = millis();
  }
  lastButtonState = currentButton;  // Update last button state

}

