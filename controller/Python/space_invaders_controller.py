import ECE16Lib.DSP as filt
from ECE16Lib.Communication import Communication
from time import sleep
import socket, pygame
import time
import numpy as np
# Setup the Socket connection to the Space Invaders game
host = "127.0.0.1"
port = 65432
mySocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
mySocket.connect((host, port))
mySocket.setblocking(False)
# Set file to scores
scorefile = "scores.csv"

# Save data to file
def save_score(filename, data):
  np.savetxt(filename, data, delimiter=",")

# Load data from file
def load_score(filename):
    try:
        data = np.genfromtxt(filename, delimiter=",")
        return int(data) if data.size > 0 else 0
    except:
        return 0  # Default to 0 if file is empty or missing


class PygameController:
    def __init__(self, serial_name, baud_rate):
        self.comms = Communication(serial_name, baud_rate)
        self.movement_avg = 0  # Moving average for smoother movement

    def smooth_movement(self, movement):
        # Use exponential moving average for movement smoothing
        self.movement_avg = (0.1 * self.movement_avg) + (0.9 * movement)
        return self.movement_avg

    def run(self):
      # 1. Stop any previous data streaming
      self.comms.send_message("stop")
      self.comms.clear()

      # 2. Start streaming orientation data
      input("Ready to start? Hit enter to begin.\n")
      self.comms.send_message("start")

      # 3. Collect orientation and send to PyGame until user exits
      print("Use <CTRL+C> to exit the program.\n")
      top_score = load_score(scorefile)

      while True:
          try:
              msg, _ = mySocket.recvfrom(1024)  # Receive 1024 bytes
              msg = msg.decode('utf-8')
              # Check message from game
              if msg == "DIEDONCE":
                  self.comms.send_message("died once")
              elif msg == "DIEDTWICE":
                  self.comms.send_message("died twice")
              elif msg == "DIEDTHRICE":
                  self.comms.send_message("died thrice")
              elif msg == "DEAD":
                  self.comms.send_message("dead")
                  # Replace top score if player score is higher
                  if score > int(top_score):
                        top_score = score
                        save_score(scorefile, np.array([top_score]))
                  # Send highest score
                  self.comms.send_message(f"Highest Score: {top_score}")

              # Send score and save score for top score when game over
              if msg.startswith("Score: "):
                  self.comms.send_message(msg)
                  score = int(msg.split(":")[1].strip())
                  
                  
          except BlockingIOError:
              # No data available, continue loop
              pass

          message = self.comms.receive_message()
          if message is not None:
              message = int(message)

              # Handle Movement
              move_value = 0
              if message == 3:  # Left
                  move_value = -1
              elif message == 4:  # Right
                  move_value = 1
              # Find the move value after smooting
              move_value = self.smooth_movement(move_value)
              if abs(move_value) > 0.05:  # Apply deadzone
                  if move_value < 0:
                      mySocket.send("LEFT".encode("UTF-8"))
                  else:
                      mySocket.send("RIGHT".encode("UTF-8"))

              # Handle Firing Separately
              if message == 2:  # Fire button press detected
                  mySocket.send("FIRE".encode("UTF-8"))


if __name__ == "__main__":
    serial_name = "/dev/cu.usbserial-10"
    baud_rate = 115200
    controller = PygameController(serial_name, baud_rate)

    try:
        controller.run()
    except (Exception, KeyboardInterrupt) as e:
        print(e)
    finally:
        print("Exiting the program.")
        controller.comms.send_message("stop")
        controller.comms.close()
        mySocket.send("QUIT".encode("UTF-8"))
        mySocket.close()

    input("[Press ENTER to finish.]")