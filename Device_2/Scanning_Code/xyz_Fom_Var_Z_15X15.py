import gpiod
import time
import os
import io
import numpy as np
import cv2
from picamera2 import Picamera2, Preview
from PIL import Image
from datetime import datetime

"""
x translation x axis -12 stepsize 
y axis Translastion y axis 
x axis 5 backlash
y axis 6 backlash
10x objective


"""

"""
21_November
14 gpio enable pin low while running z 
"""



# Get current timestamp
timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
back_x=5
back_y=6

class StepperMotorController:
    def __init__(self):
        # Define the control pins for all stepper motors
        self.ControlPinX = [18, 23, 24, 25]  # Pins for the X-axis motor
        self.ControlPinY = [5, 6, 13, 19]    # Pins for the Y-axis motor
        self.ControlPinZ = [21, 20, 2, 12]   # Pins for the Z-axis motor

        # Define the endstop pins
        self.EndstopPinX = 26
        self.EndstopPinY = 8
        self.EndstopPinZ = 7
      

        # Constants
        self.STEPS_PER_MM_X = 10
        self.STEPS_PER_MM_Y = 10
        self.STEPS_PER_MM_Z = 10
        self.delay = 0.0008
        self.delay2 = 0.000000000008 # Control the speed of the Z motor 0.0000000008

        # Position tracking
        self.x_position = 0
        self.y_position = 0
        self.z_position = 0

        # Define the segment patterns
        
        self.seg_right = [
            [1, 0, 0, 0], [1, 1, 0, 0], [0, 1, 0, 0], [0, 1, 1, 0],
            [0, 0, 1, 0], [0, 0, 1, 1], [0, 0, 0, 1], [1, 0, 0, 1]
        ]
        self.seg_left = self.seg_right[::-1]
        """
        self.seg_right = [
            [1, 0, 0, 0],
            [1, 1, 0, 0],
            [0, 1, 0, 0],
            [0, 1, 1, 0],
            [0, 0, 1, 0],
            [0, 0, 1, 1],
            [0, 0, 0, 1],
            [1, 0, 0, 1]
        ]

        self.seg_left = [
            [0, 0, 0, 1],
            [0, 0, 1, 1],
            [0, 0, 1, 0],
            [0, 1, 1, 0],
            [0, 1, 0, 0],
            [1, 1, 0, 0],
            [1, 0, 0, 0],
            [1, 0, 0, 1]
        ]
        """

        # Initialize GPIO and Camera
        self.setup_gpio()
        self.setup_camera()
        
        # Create output file with timestamp
        self.setup_output_file()

    def setup_output_file(self):
        """Create output file with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = f"measurement_data_{timestamp}.txt"
        
        # Write header to the file
        with open(self.output_file, "w") as f:
            f.write("Timestamp,X_Position,Y_Position,Z_Position,FOM,Variance\n")

    def setup_camera(self):
        """Initialize the camera system."""
        self.picam2 = Picamera2()
        self.picam2.start_preview(Preview.QTGL)
        self.picam2.start()
        time.sleep(2)  # Allow camera to warm up

    def setup_gpio(self):
        """Initialize all GPIO pins."""
        self.chip = gpiod.Chip('gpiochip0')
        
        # Initialize motor control lines
        self.lines_x = [self.chip.get_line(pin) for pin in self.ControlPinX]
        self.lines_y = [self.chip.get_line(pin) for pin in self.ControlPinY]
        self.lines_z = [self.chip.get_line(pin) for pin in self.ControlPinZ]
        
        # Initialize endstop lines
        self.endstop_x = self.chip.get_line(self.EndstopPinX)
        self.endstop_y = self.chip.get_line(self.EndstopPinY)
        self.endstop_z = self.chip.get_line(self.EndstopPinZ)
        
        # Initialize microstep line
        self.ms_line = self.chip.get_line(17)
         # Initialize Enable Pin (Pin 14)
        self.enable_pin = self.chip.get_line(16)
        self.enable_pin.request(consumer='stepper', type=gpiod.LINE_REQ_DIR_OUT)
        self.enable_pin.set_value(1)  # Set to high (disabled) initially
        
        
        
        #self.enable_pin.set_value(1) 
        
        # Configure all lines
        self.ms_line.request(consumer='stepper', type=gpiod.LINE_REQ_DIR_OUT)
        self.ms_line.set_value(0)
        
        # Configure motor control lines
        for line in self.lines_x + self.lines_y + self.lines_z:
            line.request('stepper_motor', gpiod.LINE_REQ_DIR_OUT, 0)
            
        # Configure endstop lines
        for endstop in [self.endstop_x, self.endstop_y, self.endstop_z]:
            endstop.request('endstop', gpiod.LINE_REQ_DIR_IN)

    def capture_image(self):
        """Capture an image and convert to grayscale."""
        stream = io.BytesIO()
        self.picam2.capture_file(stream, format='jpeg')
        stream.seek(0)
        image = np.frombuffer(stream.getvalue(), dtype=np.uint8)
        return cv2.imdecode(image, cv2.IMREAD_GRAYSCALE)

    def calculate_variance(self, image):
        """Calculate the variance of an image."""
        return cv2.Laplacian(image, cv2.CV_64F).var()

    def capture_fom(self):
        """Capture the Figure of Merit value."""
        metadata = self.picam2.capture_metadata()
        return metadata.get('FocusFoM', 0)
    
    def move_axis_back(self, axis, steps, forward=True):
        direction = self.seg_right if forward else self.seg_left
        if axis == 'x':
            self.run_motor(self.lines_x, direction, steps)
        elif axis == 'y':
            self.run_motor(self.lines_y, direction, steps)  
       
            # self.x_position += steps if forward else -steps
    """
    def move_axis_back(self, axis, steps, forward=True):
        direction = self.seg_right if forward else self.seg_left
       """   
        
        

    def move_axis(self, axis, steps, forward=True):
        """Generic function to move any axis."""
        direction = self.seg_right if forward else self.seg_left
        if axis == 'x':
            self.run_motor(self.lines_x, direction, steps)
            self.x_position += steps if forward else -steps
        elif axis == 'y':
            self.run_motor(self.lines_y, direction, steps)
            self.y_position -= steps if forward else +steps
        elif axis == 'z':
            self.run_motor_z(self.lines_z, direction, steps)
            self.z_position += steps if forward else -steps

    def run_motor(self, lines, direction, steps):
        """Run a stepper motor for the specified steps."""
        steps = int(steps)
        for _ in range(steps):
            for halfstep in range(8):
                for pin in range(4):
                    lines[pin].set_value(direction[halfstep][pin])
                time.sleep(self.delay)
        self.set_all_pins_low()
    
    def run_motor_z(self, lines, direction, steps):
        """Run the stepper motor for the given number of steps in the specified direction."""
        steps = int(steps)  # Convert steps to integer
        steps=steps*8
        step_counter = 0
        self.enable_pin.set_value(0) ## run the Motor 
        while step_counter < steps:
            for halfstep in range(8):
                for pin in range(4):
                    lines[pin].set_value(direction[halfstep][pin])
                time.sleep(self.delay2)
            step_counter += 1

        self.enable_pin.set_value(1) ## stoping Motor

    def set_all_pins_low(self):
        """Set all control pins to low."""
        for line in self.lines_x + self.lines_y + self.lines_z:
            line.set_value(0)
        """
        for line in self.lines_x + self.lines_y:
             line.set_value(0) 
        for line in self.lines_z:
            line.set_value(1)
        """

    def home_axis(self, axis_name):
        print(f"Homing {axis_name}-axis...")
    
    # Map axis to lines and endstop
        axis_map = {
        'x': (self.lines_x, self.endstop_x),
        'y': (self.lines_y, self.endstop_y),
        'z': (self.lines_z, self.endstop_z)
          }
    
        lines, endstop = axis_map[axis_name]
    
    # Determine the direction based on the axis being homed
        direction = self.seg_left if axis_name in ['x', 'z'] else self.seg_right
    
    # Check if endstop has been reached; if not, run the motor
        while not self.check_endstop(endstop):
            if axis_name == 'z':
                self.run_motor_z(lines, direction, 1)  # Use run_motor_z specifically for the Z-axis
            else:
                self.run_motor(lines, direction, 1)     # Use run_motor for X and Y axes
    
    # Reset the axis position to 0 once homed
        if axis_name == 'x':
            self.x_position = 0
        elif axis_name == 'y':
            self.y_position = 0
        elif axis_name == 'z':
            self.z_position = 0
    
        print(f"{axis_name}-axis homed successfully")


    def check_endstop(self, endstop_line):
        """Check if an endstop is triggered."""
        return endstop_line.get_value() == 1

    def init(self):
        """Initialize all axes to their home positions."""
        print("Initializing all axes...")
        self.home_axis('x')
        self.home_axis('y')
        self.home_axis('z')
        print("All axes initialized to home position")

    def move_to_starting_position(self):
        """Move to the specified starting position after initialization."""
        print("Moving to starting position...")
        self.move_axis('x', 320, True)  # xcclk,280 coordinates
        self.move_axis('y', 190, False)  # ycclk,230
        print(f"Reached starting position: X={self.x_position}, Y={self.y_position}, Z={self.z_position}")

    def perform_z_scan(self):
        """Perform Z-axis scan with measurements every 25 steps."""
        print("Starting Z-axis scan First 2000  ...")
        
        current_z = 0
        while current_z < 2100:
            # Move Z axis by 25 steps
            self.move_axis('z', 50, True)  # zcclk,25
            current_z += 50
            
            # Capture measurements
            image = self.capture_image()
            variance = self.calculate_variance(image)
            fom = self.capture_fom()
            
            # Get current timestamp
            #timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            # Log data
            data_line = f"{timestamp},{self.x_position},{self.y_position},{self.z_position},{fom},{variance}"
            with open(self.output_file, "a") as f:
                f.write(data_line + "\n")
            
            # Print current measurements
            print(f"Z={self.z_position}, FOM={fom:.2f}, Variance={variance:.2f}")
            
            # Small delay to ensure stable measurements
            time.sleep(0.1)
            
    def perform_z_scan_below(self,max_z=3150):
        """Perform Z-axis scan with measurements every 25 steps."""
        print("Starting Z-axis scan Below...")
        
        current_z = 2100
        while current_z < max_z:
            # Move Z axis by 25 steps
            self.move_axis('z', 25, True)  # zcclk,25
            current_z += 25
            
            # Capture measurements
            image = self.capture_image()
            variance = self.calculate_variance(image)
            fom = self.capture_fom()
            
            
            
            # Log data
            data_line = f"{self.x_position},{self.y_position},{self.z_position},{fom},{variance}"
            with open(self.output_file, "a") as f:
                f.write(data_line + "\n")
            
            # Print current measurements
            print(f"Z={self.z_position}, FOM={fom:.2f}, Variance={variance:.2f}")
            
            # Small delay to ensure stable measurements
            time.sleep(0.1)
            
    def perform_z_scan_above(self):
        """Perform Z-axis scan with measurements every 25 steps."""
        print("Starting Z-axis scan Above ...")
        
        current_z = 3150
        while current_z > 2100:
            # Move Z axis by 25 steps
            self.move_axis('z', 25, False)  # zcclk,25
            current_z -= 25
            
            # Capture measurements
            image = self.capture_image()
            variance = self.calculate_variance(image)
            fom = self.capture_fom()
            
            
            
            # Log data
            data_line = f"{self.x_position},{self.y_position},{self.z_position},{fom},{variance}"
            with open(self.output_file, "a") as f:
                f.write(data_line + "\n\n")
            
            # Print current measurements
            print(f"Z={self.z_position}, FOM={fom:.2f}, Variance={variance:.2f}")
            
            # Small delay to ensure stable measurements
            time.sleep(0.1)


    def cleanup(self):
        """Clean up all resources."""
        print("Cleaning up...")
        for line in self.lines_x + self.lines_y + self.lines_z:
            try:
                line.release()
            except Exception as e:
                print(f"Error releasing line: {e}")
        self.picam2.stop_preview()
        self.picam2.stop()
        print("Cleanup complete.")
        
    def b1(self):
        print("entering Block B1")
        
        for i in range(8):
            self.move_axis('x', 12, True)
            self.perform_z_scan_below()
            
            self.move_axis('x', 12, True)
            self.perform_z_scan_above()
            
            
        #self.move_axis('y', 6, True) ##y axis Backlash
        self.move_axis_back('y',back_y, True)
        self.move_axis('y', 9, True)
        self.perform_z_scan_below()
        
        #self.move_axis('x',back_x, False) ## x axis Backlash 
        self.move_axis_back('x',back_x, False)
        ### 19_Nov
      
            
        for i in range(8):
            self.perform_z_scan_above()
            
            self.move_axis('x', 12, False)
            self.perform_z_scan_below()
           
            self.move_axis('x', 12, False)
            
        #### Block 1,2 Ends#####    
        
    def b2(self):
        print("Entering Block B2")
        self.move_axis('y', 9, True)
        self.perform_z_scan_above()
        #self.move_axis('x', 5, True)# x axis Back_lash 
        self.move_axis_back('x',back_x, True)
        for i in range(8):
            self.move_axis('x', 12,True) # x axis Translation
            self.perform_z_scan_below()
            self.move_axis('x', 12, True)# x axis Translation
            self.perform_z_scan_above()
        
        self.move_axis('y', 9, True)
        self.perform_z_scan_below()
        #self.move_axis('x', back_x, False)# x axis Back lash 
        self.move_axis_back('x',back_x, False)
            
            
        for i in range(8):
            self.perform_z_scan_above()
            self.move_axis('x', 12, False)
            self.perform_z_scan_below()
            self.move_axis('x', 12, False)
            
        ### block 3,4 Ends    
        
        #### b2 Block start
        
        
        
        
    def b3(self):
        print("entering Block B3")
        #19_November add y axis 
        self.move_axis('y', 9, True)
        for i in range(8):
            self.move_axis('x', 12, True)
            self.perform_z_scan_above()
            self.move_axis('x', 12, True)
            self.perform_z_scan_below()
            
        #self.move_axis('y', 5, True) ##y axis backlash
        self.move_axis('y', 9, True)
        self.perform_z_scan_above()
        #self.move_axis('x', back_x, False) ## x axis Backlashs
        self.move_axis_back('x',back_x, False)
            
            
        for i in range(8):
            self.perform_z_scan_below()
            self.move_axis('x', 12, False)
            self.perform_z_scan_above()
            self.move_axis('x', 12, False)
            
        ### block 3,4 Ends    
    def b4(self):  # New block to complete the 16x16 matrix
        print("entering Block B4")
        self.move_axis('y', 9, True)
        self.perform_z_scan_below()
        self.move_axis_back('x', back_x, True)
        
        for i in range(8):
            self.move_axis('x', 12, True)
            self.perform_z_scan_above()
            self.move_axis('x', 12, True)
            self.perform_z_scan_below()
            
        self.move_axis('y', 9, True)
        self.perform_z_scan_above()
        self.move_axis_back('x', back_x, False)
            
        for i in range(8):
            self.perform_z_scan_below()
            self.move_axis('x', 12, False)
            self.perform_z_scan_above()
            self.move_axis('x', 12, False)
        self.move_axis('y', 9, True)# when you goto b1 function it has to move y axis 
     
        

def main():
    try:
        controller = StepperMotorController()
        print("Starting measurement sequence...")
        
        # Initialize all axes
        controller.init()
        
        # Move to starting position
        controller.move_to_starting_position()
        
        # Perform Z-axis scan
        controller.perform_z_scan()
        
        #######Block 1,2 Starts#####
        for j in range(4):
            if (j%2 ==0):
                print("Entering the if part ")
                controller.b1() ### run block 1
                controller.b2() ### run block 2
            else:
                print("Entering the else part ")
                controller.b3() ### run block 3
                controller.b4() ### run block 4
            
            
              
        ### block 3,4 starts
        
            
            
             
        
      
        print("Measurement sequence completed successfully")
        
    except Exception as e:
        print(f"Error occurred: {e}")
    finally:
        controller.cleanup()

if __name__ == "__main__":
    main()
