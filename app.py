import streamlit as st
import random
import time
import math

# -----------------------
# PAGE CONFIGURATION
# -----------------------
st.set_page_config(page_title="Traffic Optimizer", layout="wide")
st.title("🚦 Traffic Optimizer & Assistant - Objective 2 Simulation")
st.markdown("This simulation suggests smart speed adjustments to help a vehicle pass traffic signals efficiently.")

# -----------------------
# SIDEBAR CONTROLS
# -----------------------
st.sidebar.header("Simulation Controls")
initial_speed = st.sidebar.slider("Initial Speed (km/h)", 10, 60, 25)
max_speed = st.sidebar.slider("Max Speed", 10, 60, 60)
min_speed = st.sidebar.slider("Min Speed", 10, 60, 10)
run_button = st.sidebar.button("▶ Start Simulation")

# -----------------------
# INITIAL SIMULATION STATE
# -----------------------
signal_positions = [150, 350, 550, 750, 950]
signal_labels = ['B', 'C', 'D', 'E', 'F']
signal_states = {}

def init_traffic_lights():
    for label, x in zip(signal_labels, signal_positions):
        phase = random.choice(['red', 'green', 'yellow'])
        timer = random.randint(10, 45) if phase != 'yellow' else 5
        signal_states[label] = {'x': x, 'phase': phase, 'timer': timer}

init_traffic_lights()

car_x = 0
car_speed = initial_speed
waiting_at = None

# -----------------------
# SIMULATION LOOP
# -----------------------
if run_button:
    info_box = st.empty()
    signal_box = st.empty()
    road_box = st.empty()
    
    while car_x <= 1100:
        # --- Update signal timers ---
        for sig in signal_states.values():
            sig['timer'] -= 1
            if sig['timer'] <= 0:
                if sig['phase'] == 'red':
                    sig['phase'] = 'green'
                    sig['timer'] = 45
                elif sig['phase'] == 'green':
                    sig['phase'] = 'yellow'
                    sig['timer'] = 5
                elif sig['phase'] == 'yellow':
                    sig['phase'] = 'red'
                    sig['timer'] = random.randint(30, 60)

        # --- Find next signal ---
        next_signal = None
        for lbl in signal_labels:
            if signal_states[lbl]['x'] > car_x:
                next_signal = lbl
                break

        suggestion = "Maintain"
        eta = float('inf')
        distance = 0
        predicted_phase = "-"
        current_phase = "-"

        if next_signal:
            signal = signal_states[next_signal]
            distance = signal['x'] - car_x
            current_phase = signal['phase']
            if car_speed > 0:
                eta = distance / (car_speed * 0.1)
            else:
                eta = float('inf')

            # Predict phase
            rem = eta
            phase = current_phase
            time_left = signal['timer']
            if rem <= time_left:
                predicted_phase = phase
            elif phase == "red":
                rem -= time_left
                if rem <= 45:
                    predicted_phase = "green"
                elif rem <= 50:
                    predicted_phase = "yellow"
                else:
                    predicted_phase = "red"
            elif phase == "green":
                rem -= time_left
                if rem <= 5:
                    predicted_phase = "yellow"
                elif rem <= 5 + 40:
                    predicted_phase = "red"
                else:
                    predicted_phase = "green"
            elif phase == "yellow":
                rem -= time_left
                if rem <= 40:
                    predicted_phase = "red"
                elif rem <= 40 + 45:
                    predicted_phase = "green"
                else:
                    predicted_phase = "yellow"

            # Suggest speed
            if current_phase == 'red' and distance <= 40:
                suggestion = 'Slow Down'
                car_speed = 0
                waiting_at = next_signal
            elif current_phase == 'green':
                if car_speed < max_speed:
                    suggestion = 'Speed Up'
                    if random.random() < 0.7:
                        car_speed += 5
                        car_speed = min(car_speed, max_speed)
                elif car_speed > min_speed:
                    suggestion = 'Slow Down'
                    if random.random() < 0.7:
                        car_speed -= 5
                        car_speed = max(car_speed, min_speed)

        # Resume after red
        if waiting_at and signal_states[waiting_at]['phase'] == 'green':
            waiting_at = None
            car_speed = 15

        # Move car forward
        car_x += car_speed * 0.1

        eta_str = "N/A" if math.isinf(eta) else f"{int(eta)}s"
        info_box.markdown(
            f"""
            ### 🚘 Vehicle Info  
            - **Speed:** {int(car_speed)} km/h  
            - **Next Signal:** `{next_signal}`  
            - **Distance to Signal:** `{int(distance)} px`  
            - **Current Phase:** `{current_phase}`  
            - **ETA:** `{eta_str}`  
            - **Predicted Phase:** `{predicted_phase}`  
            - **Advice:** 🚘 `{suggestion}`
            """
        )

        # Voice Alert (Browser TTS)
        voice = ""
        if suggestion == "Speed Up":
            voice = "Signal is green. You can speed up."
        elif suggestion == "Slow Down":
            voice = "Red signal ahead. Please slow down."
        elif suggestion == "Maintain":
            voice = "Maintain your current speed."

        st.markdown(
            f"""
            <script>
            var msg = new SpeechSynthesisUtterance("{voice}");
            window.speechSynthesis.cancel();
            window.speechSynthesis.speak(msg);
            </script>
            """,
            unsafe_allow_html=True
        )

        # -------------------------
        # ROAD VISUALIZATION
        # -------------------------
        road_display = ["-"] * 120

        # Traffic light positions
        for lbl in signal_labels:
            pos = int(signal_states[lbl]["x"] / 10)
            phase = signal_states[lbl]["phase"]
            if phase == "red":
                road_display[pos] = "🟥"
            elif phase == "green":
                road_display[pos] = "🟩"
            elif phase == "yellow":
                road_display[pos] = "🟨"

        # Car position
        car_pos_index = int(car_x / 10)
        if 0 <= car_pos_index < len(road_display):
            road_display[car_pos_index] = "🔵"

        road_box.markdown("### 🛣️ Road View")
        road_box.code("".join(road_display))

        # Signal Timers
        cols = st.columns(len(signal_labels))
        for i, lbl in enumerate(signal_labels):
            sig = signal_states[lbl]
            with cols[i]:
                st.metric(label=f"Signal {lbl}", value=sig['phase'].capitalize(), delta=f"{sig['timer']}s")

        time.sleep(1)
