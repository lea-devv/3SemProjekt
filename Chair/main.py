from umqttsimple import MQTTClient
from machine import ADC, Pin, Timer, SoftSPI
from mfrc522 import MFRC522
from time import sleep
import ubinascii
import machine
import _thread
import json

vibr_timer_state = False

##############################################################
#MQTT Configuration
mqtt_server = '192.168.2.2'
mqtt_port = 1883
client_id = ubinascii.hexlify(machine.unique_id())
client = MQTTClient(client_id, mqtt_server, port=mqtt_port)

last_message = 0
message_interval = 5
counter = 0

##############################################################
#RFID Reader
sck = Pin(18, Pin.OUT)
copi = Pin(23, Pin.OUT) # Controller out, peripheral in
cipo = Pin(19, Pin.OUT) # Controller in, peripheral out
spi = SoftSPI(baudrate=100000, polarity=0, phase=0, sck=sck, mosi=copi, miso=cipo)
sda = Pin(5, Pin.OUT)
rfid_reader = MFRC522(spi, sda)
uuid = None

##############################################################
#Chair Functionality
vibration_pin = 2
vibr = Pin(vibration_pin, Pin.OUT)

vibr_timer = Timer(1)
vibr_timer_ms = 5000

chair_back_left_avg = 0
chair_back_right_avg = 0
chair_bottom_left_avg = 0
chair_bottom_right_avg = 0
battery_avg = 0

##############################################################
# Configure the ADC pins
#battery_pin = 25
#battery_adc = ADC(Pin(battery_pin))
#battery_adc.width(ADC.WIDTH_12BIT)
#battery_adc.atten(ADC.ATTN_11DB)

chair_back_left_pin = 36
chair_back_left_adc = ADC(Pin(chair_back_left_pin))
chair_back_left_adc.atten(ADC.ATTN_11DB)
chair_back_left_adc.width(ADC.WIDTH_12BIT)  

chair_back_right_pin = 39
chair_back_right_adc = ADC(Pin(chair_back_right_pin))
chair_back_right_adc.atten(ADC.ATTN_11DB)
chair_back_right_adc.width(ADC.WIDTH_12BIT)  

chair_bottom_left_pin = 34
chair_bottom_left_adc = ADC(Pin(chair_bottom_left_pin))
chair_bottom_left_adc.atten(ADC.ATTN_11DB)
chair_bottom_left_adc.width(ADC.WIDTH_12BIT)  

chair_bottom_right_pin = 35
chair_bottom_right_adc = ADC(Pin(chair_bottom_right_pin))
chair_bottom_right_adc.atten(ADC.ATTN_11DB)
chair_bottom_right_adc.width(ADC.WIDTH_12BIT)  

##############################################################
#MQTT

def connect_mqtt():
    try:
        client.connect()
        print("Connected to MQTT broker")
    except Exception as e:
        print("Failed to connect to MQTT broker:", e)
        sleep(10)
        machine.reset()
        raise
    return client

connect_mqtt()

##############################################################
#All these functions are called from within one thread thereby not disturbing the main loop
def read_average_adc(adc, num_samples=64):
    reading64 = 0
    for i in range(num_samples):
        reading64 += adc.read()
    average = reading64 >> 6
    return average

def vibrate_chair(vibr_timer):
    print("vibrrrrr")
    global vibr_timer_state
    vibr.value(1)  # Turn the pin on
    sleep(1)       # Wait for 1 second
    vibr.value(0)  # Turn the pin off
    vibr_timer_state = False
    client.publish(b'vibr_activated', str(1))


def data_logging():
    while True:
        global chair_back_left_avg, chair_back_right_avg, chair_bottom_left_avg, chair_bottom_right_avg, battery_avg, vibr_timer_state
        chair_back_left_avg = read_average_adc(chair_back_left_adc)
        chair_back_right_avg = read_average_adc(chair_back_right_adc)
        chair_bottom_left_avg = read_average_adc(chair_bottom_left_adc)
        chair_bottom_right_avg = read_average_adc(chair_bottom_right_adc)
        #battery_avg = read_average_adc(battery_adc)
        sleep(0.5)
        print(vibr_timer_state, chair_bottom_right_avg)
        if chair_bottom_right_avg > 3000 and vibr_timer_state is False:
            vibr_timer_state = True
            print("Waiting")
            vibr_timer.init(period=5000, mode=Timer.ONE_SHOT, callback=vibrate_chair)
        elif chair_bottom_right_avg < 3000:
            vibr_timer_state = False
            vibr_timer.deinit()

_thread.start_new_thread(data_logging, ())

##############################################################
#Publishes data to the server
while True:
    try:
        (status, _) = rfid_reader.request(rfid_reader.CARD_REQIDL)
        if status == rfid_reader.OK:
            (status, raw_uid) = rfid_reader.anticoll()
            if status == rfid_reader.OK:
                uuid = ''.join('%02x' % byte for byte in raw_uid)
                print(uuid)

        if uuid is not None:
            message = {
                "uuid": uuid,
                "chair_back_left_avg": chair_back_left_avg,
                "chair_back_right_avg": chair_back_right_avg,
                "chair_bottom_left_avg": chair_bottom_left_avg,
                "chair_bottom_right_avg": chair_bottom_right_avg
                }
            message_json = json.dumps(message)
            client.publish(b'chair_data', str(message_json))

        battery_pct = (battery_avg - 1590) / 7.3 # ADC1590 = 0% og 1% = ADC7.3
        client.publish(b'battery_data', str(battery_pct))
        sleep(0.5)

    except KeyboardInterrupt:
        break

