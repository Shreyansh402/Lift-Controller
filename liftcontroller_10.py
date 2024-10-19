from time import sleep_ms 
from machine import Pin, SoftI2C
from i2c_lcd import I2cLcd 
import time
from utime import sleep
######## Definitions ########

# Define LCD params
AddressOfLcd = 0x27
i2c = SoftI2C(scl=Pin(22), sda=Pin(21), freq=400000) # connect scl to GPIO 22, sda to GPIO 21
lcd = I2cLcd(i2c, AddressOfLcd, 4, 20)
led = Pin(15, Pin.OUT)

#Assumptions
No_of_floors = 10
floor_floor_delay = 10
floor_opening_delay = 2
floor_closing_delay = 2
floor_stay_delay = 5
floors = []
for i in range(0, No_of_floors,1):
    floors.append(str(i))
print(floors)
initial_pos = 5 

# Define keypad layout

# O -- Fast Open
# C -- Fast Close
# A -- Alarm
# E -- Emergency Stop
# * && / -- Undefined states
# 0,1,2,3,4,5, 6,7,8,9 -- Floor States

keypad = [
    ['1', '2', '3', 'O' ],
    ['4', '5', '6', 'C' ],
    ['7', '8', '9', '*' ],
    ['A', '0', 'E', '/' ]
]

# Define the row and column pins
row_pins = [Pin(13, Pin.OUT), Pin(12, Pin.OUT), Pin(14, Pin.OUT), Pin(27, Pin.OUT)]
col_pins = [Pin(26, Pin.IN, Pin.PULL_UP), Pin(25, Pin.IN, Pin.PULL_UP), Pin(33, Pin.IN, Pin.PULL_UP), Pin(32, Pin.IN, Pin.PULL_UP)]

# Initialize the row pins to HIGH
for row_pin in row_pins:
    row_pin.value(1)

# Initialize the col pins to LOW
for col_pin in col_pins:
    col_pin.value(0)

# Variables to store user input and calculation
user_input = ""
result = None
math_sign = ""
sign_applied = False    # When sign button has not been clicked

######## Methods ########
# Pad String
def pad_string(input_string, desired_length = 15):
    current_length = len(input_string)
    if current_length >= desired_length:
        return input_string  # No need to pad if it's long enough

    # Calculate the number of spaces needed
    spaces_needed = desired_length - current_length

    # Append the required spaces to the string
    padded_string = input_string + " " * spaces_needed

    return padded_string

# Print user input
def lcd_print(row, value, start_col = 1, space_padding = True):
    print("move to : " + str(row))
    lcd.move_to(start_col,row)
    if space_padding:
        lcd.putstr(pad_string(str(value)))
    else:
        lcd.putstr(str(value))

# Get Key Pressed value
def get_key():
    keys_detected = []
    for i, row_pin in enumerate(row_pins):
        # Drive the current row LOW
        row_pin.value(0)

        for j, col_pin in enumerate(col_pins):
            if col_pin.value() == 0:
                keys_detected.append(keypad[i][j])
                # Key is pressed, return the corresponding character
                return keypad[i][j]


        # Release the row
        row_pin.value(1)

    return None

disk_size = 200
def SCAN(arr, head, direction):
    seek_count = 0
    distance , cur_track = 0, 0
    left = []
    right = []
    seek_sequence = []

    # if(direction == "left"):
    #     left.append(0)
    # elif(direction == "right"):
    #     right.append(disk_size-1)
    for i in range(len(arr)):
        if(arr[i] <= head):
            left.append(arr[i])
        if(arr[i] > head):
            right.append(arr[i])
    
    left.sort()
    right.sort()

    run = 2
    while(run !=0):
        if(direction == "left"):
            for i in range(len(left)-1, -1 ,-1):
                cur_track = left[i]
                seek_sequence.append(cur_track)
                distance = abs(cur_track - head)
                seek_count += distance

                head = cur_track
            direction = "right"
        elif(direction == "right"):
            for i in range(len(right)):
                cur_track = right[i]
                seek_sequence.append(cur_track)
                distance = abs(cur_track - head)
                seek_count += distance
                head = cur_track
            direction = "left"
        run -= 1
    arr.clear()
    for i in range(len(seek_sequence)):
        arr.append(seek_sequence[i])
        if( i != 0 and seek_sequence[i] == seek_sequence[i-1]):
            arr.pop()
arr = []
head = initial_pos
direction = "left"




# Run keyboard scan
def keyboard_scan():
    global user_input
    global result
    global math_sign
    global sign_applied

    key = get_key()
    if key is not None:
        if key in floors:
            arr.append(int(key))
            SCAN(arr, head, direction)
            for i in range(len(arr)):
                print(arr[i])
        elif key == "E":
            arr.clear()
            lcd.clear()
            lcd_print(2, "Emergency Stop", 0, False)
        elif key == "A":
            led.on()
            sleep(2)
            led.off()
        elif key == "O":
            print("Fast Open Initiated")
        elif key == "C":
            print("Fast Close Initiated")
        else:
            print("Invalid Button Pressed")
    # Add a small delay to debounce the keypad
    sleep_ms(100)
    return key

lcd_print(2, "Floor 5 closing Door", 0, False)



while True:
    while(len(arr) != 0):
        if(arr[0] - head  > 0):
            head +=1 
            
            lcd.clear()
            lcd_print(2, "Moving to floor: " + str((head)), 0, False)
            start_time = time.time()
            while time.time() - start_time <floor_floor_delay:
                key = keyboard_scan()
                if(key == "E"):
                    continue
                sleep_ms(100)
        elif(arr[0] - head < 0):
            head -=1
            
            lcd.clear()
            lcd_print(2, "Moving to floor: " + str((head)), 0, False)
            start_time = time.time()
            while time.time() - start_time <floor_floor_delay:
                key = keyboard_scan()
                if(key == "E"):
                    continue
                sleep_ms(100)
        else:
            lcd.clear()
            lcd_print(2, "FLoor "+ str((head)) + " Opening Door", 0, False)
            start_time = time.time()
            key = '-'
            while time.time() - start_time <floor_opening_delay:
                keyboard_scan()
                sleep_ms(100)
            start_time = time.time()
            lcd.clear()
            lcd_print(2, "Floor " + str((head)) + " Reached", 0, False)
            while time.time() - start_time <floor_stay_delay:
                key = keyboard_scan()
                if(key == "C" or key == "O"):
                    break

                sleep_ms(100)
            if(key != "O"):
                lcd.clear()
                lcd_print(2, "FLoor "+ str((head)) + " Closing Door", 0, False)    
            start_time = time.time()
            while time.time() - start_time <floor_closing_delay:
                key = keyboard_scan()
                if(key  == "O"):
                    break
                sleep_ms(100)
            if(key != "O"):
                arr.pop(0)
            
            
    keyboard_scan()
    sleep_ms(100)


    