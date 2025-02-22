# Femtofox Power Consumption and Transmit Power Testing

See the <a href="https://lora-alliance.org/wp-content/uploads/2021/04/Gateway-Test-and-Measurement-Guidelines-Issue01.pdf">LoRa Gateway Test Guidelines</a> for reference
<a href="https://goughlui.com/2021/03/28/tutorial-introduction-to-scpi-automation-of-test-equipment-with-pyvisa/#google_vignette">An introduction to test automation with PyVisa</a>

## Hardware Utilized:
<ul>Rigol DHO804 Oscilloscope</ul>
<ul>Keithly 2450 SMU</ul>
<ul>NanoVNA V2</ul>
<ul>Minicircuits VAT-10A+ 10dB + VAT-20A+ 20dB Attenuators</ul>
<ul>Minicircuits ZX30-9-4-S+ Directional Coupler</ul>
<ul>Minicircuits ZX47-40LN-S+ Power Sensor</ul>

## Requirements:
<ul>meshtastic</ul>
<ul>pyvisa</ul>

## Procedure:
```
LoRa Gateway under test -IN-> 30dB attenuation -> ZX30-9-4-S+ directional coupler -OUT-> 50ohm RF dummy load
                                                          \
                                                           `-CPL-> ZX47-40LN-S+ Power Sensor -> 500Ohm Resistor -> SIGNAL_OUT -> 500Ohm Resistor -> gnd
```
```
1: Measure S21 Loss from IN to CPL with power sensor disconnected. Add this to the level measured at the power sensor. I got 38.9dB
2: Use a fixed dBm 900mhz reference signal to calibrate the power sensor RF power in / DC out if available.
3: Sweep through each applicable lora.tx_power setting and measure the level at SIGNAL_OUT with an oscilloscope.
