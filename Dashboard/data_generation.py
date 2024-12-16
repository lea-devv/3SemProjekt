#import paho.mqtt.client as mqtt
#import paho.mqtt.publish as publish
import datetime
import sqlite3
import threading

co2_value = None
co2_data_location = None
chair_rfid_uuid = None
chair_back_left = None
chair_back_right = None
chair_bottom_left = None
chair_bottom_right = None

##############################################################
#Callback functions for mqtt
def on_connect(client, userdata, flags, reason_code, properties):
    print(f"Connected with result code {reason_code}")
    client.subscribe("co2_data")
    client.subscribe("chair_data")


def on_message(client, userdata, msg):
    global co2_value, co2_data_location
    global chair_rfid_uuid, chair_back_left, chair_back_right, chair_bottom_left, chair_bottom_right
    
    if msg.topic == "co2_data":
        co2_data = str(msg.payload.decode())
        co2_data_location, co2_value = co2_data.split(", ")

    if msg.topic == "chair_data":
        chair_data = str(msg.payload.decode())
        chair_rfid_uuid, chair_back_left, chair_back_right, chair_bottom_left, chair_bottom_right = chair_data.split(", ")

    
##############################################################
#Takes the data recieved from mqtt and enters it into the databases
def get_chair_data(chair_rfid_uuid):

    table_name = f'"{chair_rfid_uuid}"'

    create_query = f"""CREATE TABLE IF NOT EXISTS {table_name} (
        datetime TEXT NOT NULL,
        chair_back_left REAL NOT NULL, 
        chair_back_right REAL NOT NULL,
        chair_bottom_left REAL NOT NULL,
        chair_bottom_right REAL NOT NULL);"""

    select_query = f"""SELECT * FROM {table_name} 
        ORDER BY datetime DESC;"""
    
    chair_data = []
    datetimes = []
    chair_back_left = []
    chair_back_right = []
    chair_bottom_left = []
    chair_bottom_right = []

    try:
        conn = sqlite3.connect("database/chair.sqlite")
        cur = conn.cursor()

        cur.execute(create_query)
        cur.execute(select_query)

        rows = cur.fetchmany(10)
        for row in reversed(rows):
            chair_data.append({
                'datetime': row[0],
                'chair_back_left': row[1],
                'chair_back_right': row[2],
                'chair_bottom_left': row[3],
                'chair_bottom_right': row[4],
            })
        return chair_data
    
    except sqlite3.Error as sql_e:
        print(f"sqlite error occured: {sql_e}")
        conn.rollback()
    except Exception as e:
        print(f"Error occured: {e}")
    finally:
        conn.close()
        
##############################################################
#Takes the data recieved from mqtt and enters it into the databases
def get_co2_data():
    create_query = f"""CREATE TABLE IF NOT EXISTS {co2_data_location} (
        datetime TEXT NOT NULL, 
        co2_value REAL NOT NULL);"""

    select_query = f"""SELECT * FROM {co2_data_location} 
        ORDER BY datetime DESC;"""
    
    datetimes = []
    co2_values = []

    try:
        conn = sqlite3.connect("/database/co2.sqlite")
        cur = conn.cursor()
        cur.execute(create_query)
        cur.execute(select_query)
        rows = cur.fetchmany(500) #Set to 500 values
        for row in reversed(rows):
            datetimes.append(row[0])
            co2_values.append(row[1])
        return datetimes, co2_values
        
    except sqlite3.Error as sql_e:
        print(f"sqlite error occured: {sql_e}")
        conn.rollback()
    except Exception as e:
        print(f"Error occured: {e}")
    finally:
        conn.close()

##############################################################

def log_data():
    global co2_value, co2_data_location
    global chair_user, chair_back_left, chair_back_right, chair_bottom_left, chair_bottom_right
    while True:
        now = datetime.now()
        now = now.strftime("%d/%m/%y %H:%M:%S")
        try:
            conn = sqlite3.connect("./database/co2.sqlite")
            cur = conn.cursor()
            console_query = f"""INSERT INTO {co2_data_location}(
                datetime, co2_data) VALUES(?, ?, ?)"""
            if co2_value and co2_data_location is not None:
                co2_data = (now, co2_value)
                cur.execute(console_query, co2_data)
                conn.commit()
        except sqlite3.Error as sql_e:
            print(f"sqlite error occured: {sql_e}")
            conn.rollback()
        except Exception as e:
            print(f"Error occured: {e}")
        finally:
            conn.close()


        try:
            conn = sqlite3.connect("./database/chair.sqlite")
            cur = conn.cursor()
            console_query = f"""INSERT INTO {co2_data_location}(
                datetime, co2_data) VALUES(?, ?, ?)"""
            if co2_value and co2_data_location is not None:
                co2_data = (now, co2_value)
                cur.execute(console_query, co2_data)
                conn.commit()
        except sqlite3.Error as sql_e:
            print(f"sqlite error occured: {sql_e}")
            conn.rollback()
        except Exception as e:
            print(f"Error occured: {e}")
        finally:
            conn.close()

    
##############################################################
def desicions():
    ...

##############################################################
"""
#Starts a non-blocking loop for mqtt and starts a thread for logging the data
mqttc = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqttc.on_connect = on_connect
mqttc.on_message = on_message

mqttc.connect("4.231.174.166", 1883, 60)

mqttc.loop_start()

log_thread = threading.Thread(target=log_data, daemon=True)

log_thread.start()
"""