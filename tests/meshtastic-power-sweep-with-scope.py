#!/usr/bin/env python3
import subprocess
import time
import argparse
import pyvisa
import numpy as np
import os
from datetime import datetime

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

def init_oscilloscope(visa_resource):
    """Initialize connection to the oscilloscope."""
    try:
        rm = pyvisa.ResourceManager()
        scope = rm.open_resource(visa_resource)
        # Set timeout to a reasonable value for waveform transfers
        scope.timeout = 10000  # 10 seconds
        
        # Check if connection is successful
        idn = scope.query("*IDN?").strip()
        print(f"Connected to oscilloscope: {idn}")
        
        return scope
    except Exception as e:
        print(f"Error connecting to oscilloscope: {e}")
        return None

def configure_oscilloscope(scope, channel=1):
    """Configure the oscilloscope for measurements."""
    try:
        # Reset the oscilloscope
        scope.write("*RST")
        time.sleep(1)
        
        # Configure the specified channel
        scope.write(f":CHAN{channel}:DISP ON")
        scope.write(f":CHAN{channel}:COUP DC")
        scope.write(f":CHAN{channel}:SCAL 0.1")  # Adjust scale as needed
        
        # Configure the trigger for the expected signal
        scope.write(":TRIG:MODE EDGE")
        scope.write(f":TRIG:EDGE:SOUR CHAN{channel}")
        scope.write(":TRIG:EDGE:SLOP POS")
        scope.write(":TRIG:EDGE:LEV 0.1")  # Adjust level as needed
        
        # Configure the timebase
        scope.write(":TIM:SCAL 0.001")  # Adjust as needed
        
        print(f"Oscilloscope channel {channel} configured")
        return True
    except Exception as e:
        print(f"Error configuring oscilloscope: {e}")
        return False

def capture_waveform(scope, channel=1, output_dir="waveforms"):
    """Capture waveform data from the oscilloscope."""
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Force a trigger if waiting
        scope.write(":TRIG:FORC")
        time.sleep(0.5)
        
        # Wait for acquisition to complete
        scope.write(":STOP")
        
        # Get waveform data
        scope.write(f":WAV:SOUR CHAN{channel}")
        scope.write(":WAV:MODE RAW")
        scope.write(":WAV:FORM BYTE")
        
        # Get waveform parameters
        preamble = scope.query(":WAV:PRE?").strip().split(',')
        
        # Get the waveform data
        scope.write(":WAV:DATA?")
        raw_data = scope.read_raw()
        
        # Remove header and terminator
        header_len = int(raw_data[1]) + 2  # +2 for '#' and length digit
        data = raw_data[header_len:-1]
        
        # Convert to numpy array
        waveform = np.frombuffer(data, dtype=np.uint8)
        
        # Get scaling parameters from preamble
        x_increment = float(preamble[4])
        x_origin = float(preamble[5])
        y_increment = float(preamble[7])
        y_origin = float(preamble[8])
        y_reference = float(preamble[9])
        
        # Scale the waveform
        time_values = np.arange(0, len(waveform)) * x_increment + x_origin
        voltage_values = (waveform - y_reference) * y_increment + y_origin
        
        # Save the waveform to a file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        tx_power = scope.tx_power if hasattr(scope, 'tx_power') else "unknown"
        filename = f"{output_dir}/waveform_ch{channel}_power{tx_power}dBm_{timestamp}.csv"
        
        with open(filename, 'w') as f:
            f.write("Time(s),Voltage(V)\n")
            for t, v in zip(time_values, voltage_values):
                f.write(f"{t:.9e},{v:.6e}\n")
        
        # Calculate some basic measurements
        peak_to_peak = np.max(voltage_values) - np.min(voltage_values)
        rms = np.sqrt(np.mean(np.square(voltage_values)))
        
        print(f"Waveform captured and saved to {filename}")
        print(f"Peak-to-Peak: {peak_to_peak:.6f} V, RMS: {rms:.6f} V")
        
        # Restart acquisition for the next capture
        scope.write(":RUN")
        
        return {
            'filename': filename,
            'peak_to_peak': peak_to_peak,
            'rms': rms,
            'tx_power': tx_power
        }
    except Exception as e:
        print(f"Error capturing waveform: {e}")
        return None

def main():
    parser = argparse.ArgumentParser(description='Sweep through LoRa transmit power levels and capture oscilloscope measurements')
    parser.add_argument('--port', required=True, help='Serial port of the Meshtastic device')
    parser.add_argument('--visa-resource', required=True, help='VISA resource string for the oscilloscope (e.g., USB0::0x1AB1::0x04CE::DS1ZA123456789::INSTR)')
    parser.add_argument('--min-power', type=int, default=0, help='Minimum power level (dBm)')
    parser.add_argument('--max-power', type=int, default=30, help='Maximum power level (dBm)')
    parser.add_argument('--step', type=int, default=1, help='Power level increment')
    parser.add_argument('--delay', type=float, default=5.0, help='Delay between tests (seconds)')
    parser.add_argument('--dest', help='Destination node ID (optional)')
    parser.add_argument('--message', help='Custom message to send (optional)')
    parser.add_argument('--channel', type=int, default=1, help='Oscilloscope channel to capture')
    parser.add_argument('--output-dir', default='waveforms', help='Directory to save waveform data')
    args = parser.parse_args()
    
    # Verify device is connected
    print(f"Checking Meshtastic device on {args.port}...")
    if not get_current_tx_power(args.port):
        print("Could not get device info. Please check connection.")
        return
    
    # Initialize the oscilloscope
    scope = init_oscilloscope(args.visa_resource)
    if not scope:
        print("Failed to connect to oscilloscope. Exiting.")
        return
    
    # Configure the oscilloscope
    if not configure_oscilloscope(scope, channel=args.channel):
        print("Failed to configure oscilloscope. Exiting.")
        scope.close()
        return
    
    # Prepare output directory
    results_file = f"{args.output_dir}/power_sweep_results.csv"
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Create results file header
    with open(results_file, 'w') as f:
        f.write("TX Power (dBm),Peak-to-Peak (V),RMS (V),Waveform File\n")
    
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
                
                # Store the current power level as an attribute on the scope object for reference
                scope.tx_power = current_power
                
                # Send test message
                if send_test_message(args.port, args.dest, args.message):
                    print(f"Test message sent at {current_power} dBm")
                    
                    # Wait for the oscilloscope to trigger and stabilize
                    time.sleep(1)
                    
                    # Capture waveform
                    result = capture_waveform(scope, channel=args.channel, output_dir=args.output_dir)
                    if result:
                        # Save results to CSV
                        with open(results_file, 'a') as f:
                            f.write(f"{current_power},{result['peak_to_peak']:.6f},{result['rms']:.6f},{result['filename']}\n")
                    
                else:
                    print("Failed to send test message")
            else:
                print("Could not verify power setting")
        
        # Wait before next iteration
        print(f"Waiting {args.delay} seconds before next test...")
        time.sleep(args.delay)
    
    # Close connection to the oscilloscope
    scope.close()
    print("Power sweep completed!")
    print(f"Results saved to {results_file}")

if __name__ == "__main__":
    main()
