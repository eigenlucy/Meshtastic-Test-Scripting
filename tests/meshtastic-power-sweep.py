#!/usr/bin/env python3
import subprocess
import time
import argparse

def set_tx_power(device_port, power_level):
    """Set the transmit power level of the Meshtastic device."""
    cmd = ["meshtastic", "--port", device_port, "--set", f"lora.tx_power={power_level}"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error setting tx_power to {power_level}: {result.stderr}")
        return False
    return True

def send_test_message(device_port, destination=None, message=None):
    """Send a test message using the Meshtastic device."""
    cmd = ["meshtastic", "--port", device_port, "--sendtext"]
    
    if destination:
        cmd.extend(["--dest", destination])
    
    if message:
        cmd.append(message)
    else:
        cmd.append(f"Test message at power level: {get_current_tx_power(device_port)}")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error sending message: {result.stderr}")
        return False
    return True

def get_current_tx_power(device_port):
    """Get the current transmit power setting."""
    cmd = ["meshtastic", "--port", device_port, "--info"]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error getting device info: {result.stderr}")
        return None
    
    # Parse the output to find tx_power
    for line in result.stdout.split('\n'):
        if "tx_power" in line:
            try:
                return int(line.split('=')[1].strip())
            except (IndexError, ValueError):
                return None
    return None

def main():
    parser = argparse.ArgumentParser(description='Sweep through LoRa transmit power levels')
    parser.add_argument('--port', required=True, help='Serial port of the Meshtastic device')
    parser.add_argument('--min-power', type=int, default=0, help='Minimum power level (dBm)')
    parser.add_argument('--max-power', type=int, default=30, help='Maximum power level (dBm)')
    parser.add_argument('--step', type=int, default=1, help='Power level increment')
    parser.add_argument('--delay', type=float, default=5.0, help='Delay between tests (seconds)')
    parser.add_argument('--dest', help='Destination node ID (optional)')
    parser.add_argument('--message', help='Custom message to send (optional)')
    args = parser.parse_args()
    
    # Verify device is connected
    print(f"Checking device on {args.port}...")
    if not get_current_tx_power(args.port):
        print("Could not get device info. Please check connection.")
        return
    
    print(f"Starting power sweep from {args.min_power} to {args.max_power} dBm...")
    
    for power in range(args.min_power, args.max_power + 1, args.step):
        print(f"Setting transmit power to {power} dBm...")
        if set_tx_power(args.port, power):
            # Delay to ensure setting is applied
            time.sleep(1)
            
            # Verify the setting was applied
            current_power = get_current_tx_power(args.port)
            if current_power is not None:
                print(f"Confirmed power level: {current_power} dBm")
                
                # Send test message
                if send_test_message(args.port, args.dest, args.message):
                    print(f"Test message sent at {current_power} dBm")
                else:
                    print("Failed to send test message")
            else:
                print("Could not verify power setting")
        
        # Wait before next iteration
        print(f"Waiting {args.delay} seconds before next test...")
        time.sleep(args.delay)
    
    print("Power sweep completed!")

if __name__ == "__main__":
    main()
