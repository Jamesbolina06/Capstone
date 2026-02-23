import cv2
import time
import os

# Load face detector
face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("❌ Camera not found.")
    exit()

# --- TUNABLE PARAMETERS ---
TURN_THRESHOLD = 35       # pixels (lower = more sensitive)
TURN_DURATION = 5         # seconds the head must be turned to trigger
ALERT_DISPLAY_SECONDS = 12  # how long the "Cheating detected" message stays on screen
# ---------------------------

initial_x = None
turn_start_time = None
direction = None
last_direction = None

# New: track last alert time to keep message visible
last_alert_time = 0
alert_active = False

print("✅ Smart Exam Monitoring Started — press Q to quit.")

try:
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 4, minSize=(80, 80))

        # Default overlay area (you can change position/size)
        h, w = frame.shape[:2]

        if len(faces) > 0:
            (x, y, cw, ch) = faces[0]  # using first detected face for demo
            center_x = x + cw // 2

            # draw face box & center
            cv2.rectangle(frame, (x, y), (x + cw, y + ch), (0, 255, 0), 2)
            cv2.circle(frame, (center_x, y + ch//2), 4, (255, 0, 0), -1)

            if initial_x is None:
                initial_x = center_x
                print("🔹 Baseline set at:", initial_x)

            move_x = center_x - initial_x
            cv2.putText(frame, f"Movement: {move_x:+d}px", (20, 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 0), 2)

            # Determine direction
            if move_x > TURN_THRESHOLD:
                direction = "RIGHT"
            elif move_x < -TURN_THRESHOLD:
                direction = "LEFT"
            else:
                direction = "FORWARD"

            cv2.putText(frame, f"Direction: {direction}", (20, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)

            # Cheating detection timing (set alert when condition satisfied)
            if direction in ["LEFT", "RIGHT"]:
                if turn_start_time is None:
                    turn_start_time = time.time()
                elif (time.time() - turn_start_time) > TURN_DURATION and not alert_active:
                    # Trigger alert
                    last_alert_time = time.time()
                    alert_active = True
                    #snapshot
                    os.makedirs("snapshots", exist_ok=True)
                    ts = time.strftime("%Y%m%d_%H%M%S")
                    snapshot_path = os.path.join("snapshots", f"alert_{ts}.jpg")
                    cv2.imwrite(snapshot_path, frame)
                    print(f"[ALERT] Motion incident Detected ({direction}) — snapshot saved: {snapshot_path}")
            else:
                # reset turn timer when facing forward (but keep alert displayed until timeout)
                turn_start_time = None

            last_direction = direction

        # Draw persistent alert on screen for ALERT_DISPLAY_SECONDS after last_alert_time
        if alert_active and (time.time() - last_alert_time) < ALERT_DISPLAY_SECONDS:
            # Big red banner + message
            banner_height = 80
            cv2.rectangle(frame, (0, 0), (w, banner_height), (0, 0, 255), -1)  # filled red
            text = "⚠️  CHEATING DETECTED"
            cv2.putText(frame, text, (20, 50), cv2.FONT_HERSHEY_DUPLEX, 1.2, (255, 255, 255), 2)
        elif alert_active:
            # alert duration expired
            alert_active = False

        # show feed
        cv2.imshow("Smart Exam Monitoring", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except KeyboardInterrupt:
    print("\n🛑 Manually stopped.")

finally:
    cap.release()
    cv2.destroyAllWindows()
    print("✅ Program closed.")
