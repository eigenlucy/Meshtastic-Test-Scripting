# LoRa Power Consumption and Transmit Power Test Automation
See the <a href="https://lora-alliance.org/wp-content/uploads/2021/04/Gateway-Test-and-Measurement-Guidelines-Issue01.pdf">LoRa Gateway Test Guidelines</a> for reference

## Hardware Utilized:
<ul>Rigol DHO804 Oscilloscope</ul>
<ul>Keithly 2450 SMU</ul>
<ul>Minicircuits VAT-10A+ 10dB Attenuator</ul>
<ul>Minicircuits ZX30-9-4-S+ Directional Coupler</ul>
<ul>Minicircuits ZX47-40LN-S+ Power Sensor</ul>
<ul>ADF4351 PLL Wideband Synthesizer</ul>

## Requirements:
<ul>meshtastic</ul>
<ul>pyvisa</ul>

Bash Usage:
```$ meshtastic_power_sweep.py --port /dev/ttyUSB0 --min-power 0 --max-power 30 --step 2 --delay 10```
