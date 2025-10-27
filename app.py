import streamlit as st
import random
import time
from datetime import datetime

# -----------------------
# PAGE CONFIGURATION
# -----------------------
st.set_page_config(page_title="Accident Prevention Sim", layout="wide")
st.title("🚨 Accident Prevention Simulation (ATOA)")
st.markdown("This simulation demonstrates how the ATOA system prevents chain-reaction accidents in low-visibility (fog) conditions.")

# -----------------------
# SIDEBAR CONTROLS
# -----------------------
st.sidebar.header("Simulation Controls")
num_cars = st.sidebar.slider("Number of Cars per Road", 2, 5, 3)
fog_level = st.sidebar.slider("Fog Level (Reduces Visibility)", 0, 90, 75)
run_button = st.sidebar.button("▶ Start Simulation")

# -----------------------
# SIMULATION CONSTANTS
# -----------------------
ROAD_LENGTH = 200  # <--- INCREASED FOR LONGER SIMULATION
NORMAL_SPEED = 2
BRAKING_SPEED = 1
# Fog reduces visibility. 0 fog = 50 visibility. 75 fog = 12.5 visibility.
VISIBILITY_DISTANCE = 50 * (1 - fog_level / 100.0)
# Minimum distance needed to stop
BRAKING_DISTANCE = 15 
# Probability of an accident per tick for the lead car
ACCIDENT_PROBABILITY = 0.03 # <--- DECREASED TO PREVENT EARLY ACCIDENT

# -----------------------
# HELPER FUNCTIONS
# -----------------------

def get_time():
    """Helper to get a simple timestamp for the log."""
    return datetime.now().strftime("%H:%M:%S")

def add_log_entry(log, message):
    """Adds a new entry to the top of a log list."""
    log.insert(0, f"[{get_time()}] {message}")

def initialize_cars(road_id):
    """Creates a list of car dictionaries for a road."""
    cars = []
    for i in range(num_cars):
        cars.append({
            'id': f"{road_id}-{i}",
            # Start spaced out further on the longer road
            'x': (num_cars - i - 1) * 40,  
            'speed': NORMAL_SPEED,
            'status': 'Normal', # Normal, Braking (Alert), Braking (Visual), Stopped, Crashed
            'alert': None,
            'log_alerted': False # Flag to prevent log spam
        })
    return cars

def update_road_logic(cars, accident_info, log):
    """
    Updates the logic for one road.
    Handles car movement, visual checks, and ATOA alerts.
    """
    for i in range(len(cars)):
        car = cars[i]
        
        # --- Skip cars that are stopped or crashed ---
        if car['status'] in ['Stopped', 'Crashed']:
            car['speed'] = 0
            continue

        # --- 1. ATOA ALERT LOGIC (Your Project's Feature) ---
        if accident_info and car['status'] != 'Braking (Alert)' and not car['log_alerted']:
            car['alert'] = f"🚨 ATOA Alert: Accident at {int(accident_info['x'])}! Slowing down."
            car['status'] = 'Braking (Alert)'
            # --- ADD TO VISUAL LOG ---
            add_log_entry(log, f"Car {car['id']}: Received broadcast! Braking immediately.")
            car['log_alerted'] = True # Mark as alerted

        # --- 2. DRIVER VISUAL LOGIC (Normal Human Driving) ---
        car_in_front = cars[i-1] if i > 0 else None
        
        if car_in_front:
            distance = car_in_front['x'] - car['x']

            # A. Check for visual on the car in front
            if distance <= VISIBILITY_DISTANCE:
                # If the car in front is crashed...
                if car_in_front['status'] == 'Crashed':
                    # ...is it too late to stop?
                    if distance <= BRAKING_DISTANCE:
                        car['status'] = 'Crashed' # 💥 Chain reaction!
                        car['alert'] = "Too close to stop! CRASHED."
                        if not car['log_alerted']:
                            add_log_entry(log, f"Car {car['id']}: CRASHED! (Too late to stop).")
                            car['log_alerted'] = True
                    else:
                        # ...no, driver can see it and brake.
                        if car['status'] != 'Braking (Visual)' and car['status'] != 'Braking (Alert)':
                            car['status'] = 'Braking (Visual)'
                            car['alert'] = "Driver View: Crash ahead! Braking."
                            if not car['log_alerted']:
                                add_log_entry(log, f"Car {car['id']}: Driver spotted crash. Braking.")
                                car['log_alerted'] = True
                
                # If car in front is just braking, driver should also brake.
                elif car_in_front['status'].startswith('Braking') and car['status'] == 'Normal':
                    car['status'] = 'Braking (Visual)'
                    car['alert'] = "Driver View: Car in front is braking."
            
            # B. If car is braking (from alert or visual), manage its speed
            if car['status'].startswith('Braking'):
                car['speed'] = BRAKING_SPEED
                # Logic to stop safely before the obstacle
                obstacle_x = accident_info['x'] if accident_info else (car_in_front['x'] if car_in_front else ROAD_LENGTH)
                if car['x'] >= (obstacle_x - BRAKING_DISTANCE - 5): # Stop 5 units behind
                    if car['status'] != 'Stopped':
                        car['status'] = 'Stopped'
                        car['alert'] = "Stopped safely."
                        add_log_entry(log, f"Car {car['id']}: Stopped safely.")
            
            # C. If no alerts and no visual, drive normally
            elif car['status'] == 'Normal':
                car['speed'] = NORMAL_SPEED
                car['alert'] = "All clear."
                # Simple follow logic to avoid bumping
                if distance < (BRAKING_DISTANCE + 5):
                    car['speed'] = BRAKING_SPEED


        # --- 3. Move the car ---
        car['x'] += car['speed']
        # Don't go off the road
        car['x'] = min(car['x'], ROAD_LENGTH)


def render_road(cars):
    """Creates a text-based string for the road."""
    # Create a road display with scale
    display_length = 100 # Keep display 100 chars
    road = ["-"] * display_length
    for car in reversed(cars): # Draw back-to-front
        # Scale car's position to the display length
        pos = int(car['x'] / ROAD_LENGTH * display_length)
        pos = min(pos, display_length - 1) # Ensure it's within bounds
        
        if 0 <= pos < display_length:
            if car['status'] == 'Crashed':
                road[pos] = "💥"
            elif car['status'] == 'Stopped':
                road[pos] = "■" # Stopped car
            elif car['status'].startswith('Braking'):
                road[pos] = "B" # Braking car
            else:
                road[pos] = "▶" # Normal car
    return "".join(road)

# -----------------------
# INITIALIZE SESSION STATE
# -----------------------
if 'simulation_running' not in st.session_state:
    st.session_state.simulation_running = False

if run_button:
    st.session_state.road_1_cars = initialize_cars("A")
    st.session_state.road_2_cars = initialize_cars("B")
    st.session_state.road_2_accident = None 
    st.session_state.simulation_running = True
    # --- NEW: Initialize alert logs ---
    st.session_state.road_1_alert_log = [f"[{get_time()}] Road 1 monitoring... All clear."]
    st.session_state.road_2_alert_log = [f"[{get_time()}] Road 2 monitoring... All clear."]

# -----------------------
# MAIN SIMULATION LOOP
# -----------------------
if st.session_state.simulation_running:
    
    # --- 1. Check for a new RANDOM accident on Road 2 ---
    if not st.session_state.road_2_accident: # If no accident has happened yet
        lead_car_2 = st.session_state.road_2_cars[0]
        # Check if lead car is on the road and a random event triggers
        if lead_car_2['x'] > 50 and lead_car_2['x'] < (ROAD_LENGTH - 20) and random.random() < ACCIDENT_PROBABILITY:
            lead_car_2['status'] = 'Crashed'
            st.session_state.road_2_accident = {'x': lead_car_2['x']}
            
            # --- ADD TO VISUAL LOG ---
            st.warning(f"💥 Accident Occurred on Road 2 at position {int(lead_car_2['x'])}!")
            add_log_entry(st.session_state.road_2_alert_log, 
                          f"CRITICAL: Accident detected at {int(lead_car_2['x'])}. Broadcasting ATOA alert to all nearby vehicles!")

    # --- 2. Update logic for both roads ---
    update_road_logic(st.session_state.road_1_cars, None, st.session_state.road_1_alert_log) 
    update_road_logic(st.session_state.road_2_cars, st.session_state.road_2_accident, st.session_state.road_2_alert_log)

    # --- 3. Render the simulation ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Road 1 (Control - No Alerts)")
        st.code(render_road(st.session_state.road_1_cars))
        # --- NEW: Visual Log Display ---
        with st.expander("Road 1: Voice Assistant Log"):
            st.write(st.session_state.road_1_alert_log)

    with col2:
        st.subheader("Road 2 (ATOA Protected)")
        st.code(render_road(st.session_state.road_2_cars))
        # --- NEW: Visual Log Display ---
        with st.expander("Road 2: Voice Assistant Log", expanded=True):
            st.write(st.session_state.road_2_alert_log)

    # --- 4. Render info boxes ---
    st.markdown("---")
    st.markdown(f"**Fog Visibility:** {VISIBILITY_DISTANCE:.1f} units | **Safe Braking Distance:** {BRAKING_DISTANCE} units")
    cols = st.columns(num_cars)
    for i in range(num_cars):
        car1 = st.session_state.road_1_cars[i]
        car2 = st.session_state.road_2_cars[i]
        
        with cols[i]:
            st.text(f"Car {car1['id']}")
            st.metric(f"Pos: {int(car1['x'])}", car1['status'])
            
            st.text(f"Car {car2['id']}")
            st.metric(f"Pos: {int(car2['x'])}", car2['status'])
            if car2['alert'] and car2['status'] != 'Normal':
                # Use different alert types based on status
                if car2['status'] == 'Crashed':
                    st.error(car2['alert'])
                elif car2['status'] == 'Braking (Alert)':
                    st.warning(car2['alert'])
                else:
                    st.info(car2['alert'])

    # --- 5. Check end condition ---
    road_1_finished = all(c['x'] >= ROAD_LENGTH or c['status'] in ['Stopped', 'Crashed'] for c in st.session_state.road_1_cars)
    road_2_finished = all(c['x'] >= ROAD_LENGTH or c['status'] in ['Stopped', 'Crashed'] for c in st.session_state.road_2_cars)

    if road_1_finished and road_2_finished:
        st.session_state.simulation_running = False
        st.success("Simulation Finished.")
        if any(c['status'] == 'Crashed' for c in st.session_state.road_2_cars[1:]):
            st.error("Result: Chain-reaction crash occurred on Road 2! (This shouldn't happen if ATOA is working)")
        else:
            st.success("Result: ATOA system successfully prevented a chain-reaction crash on Road 2!")
    else:
        # Rerun the script to create the animation loop
        time.sleep(0.3)
        st.rerun()
