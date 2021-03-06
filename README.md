# SCADA
Project Kalman part 2, Supervisory Control And Data Acquisition written in python for the Lafayette FSAE Car

## Block Diagram
![](https://raw.githubusercontent.com/Lafayette-FSAE/scada/master/diagrams/data-aquisition.svg)


## Installation

```bash
git clone https://github.com/Lafayette-FSAE/scada.git
cd scada
sudo bash install
```
you will need to do setup for postgres manually, since it has not yet been added to the install script.
See [this link](https://linuxize.com/post/how-to-install-postgresql-on-debian-9/)

## Configuration
---

Config settings can be changed by editing config.yaml in the root directory

### Bus Setup

If you are running SCADA on a system without a CAN interface, set bustype to virtual.

Virtual CAN networking can also be acheived by using the vcan0 channel of socketcan.

As it is currently configured, the raspberry pi in the Dyno room talks to the rest of
the network on the can0 channel of socketcan with a bitrate of 125000

If bustype is set to virtual, channel and bitrate fields can be omitted

```yaml
bus_info:
  bustype: socketcan | virtual
  channel: can0 | vcan0 | (or any other socketcan channel)
  bitrate: 125000
```

### Emulation

SCADA offers the ability to emulate other nodes on the CAN network in order to simplify testing.
While the current behavior is crude, there is a lot of potential for improvement.

Turn this behavior on or off with the emulate_nodes field, or selectively enable or disable
each node with the node specific fields

It is not recommended to emulate nodes that are currently running on the bus

```yaml
emulate_nodes: yes

emulate_tsi: yes
emulate_packs: yes
emulate_cockpit: no
emulate_motorcontroller: no
```

### Data

Most data is sent over the bus in 8 byte CAN packets called Process Data Objects, or PDOs,
with each byte representing a different piece of from that node.

The process_data fields tells SCADA where to expect each piece of data in each packet

If the node listed is either SCADA itself, of one of the emulated nodes, this field will be used
to define the behavior of its PDO when it is generated.

```yaml
process_data:
  TSI:    [ COOLING_TEMP_1, COOLING_TEMP_2, FLOWRATE, STATE, TS_CURRENT, TS_VOLTAGE ]
  PACK1:  [ VOLTAGE, CURRENT, SOC_1, SOC_2, AMBIENT_TEMP, 'MIN_CELL_TEMP', AVG_CELL_TEMP, MAX_CELL_TEMP ]
  PACK2:  [ VOLTAGE, CURRENT, SOC_1, SOC_2, AMBIENT_TEMP, MIN_CELL_TEMP, AVG_CELL_TEMP, MAX_CELL_TEMP ]
  SCADA:  [ TS_POWER ]
```

Because not all data needs to be read at a high frequency, the CANopen standard defines a way to
read and write data at arbitrary times, called the Service Data Object.

Each piece of data has a unique two byte index and a one byte subindex, and can be read with a special CAN packet

The service_data field defines a list of data that needs be be manually polled in this way. Each piece of data needs
to have a node_id, index, subindex, and poll_rate

```yaml
service_data:

  Cell1Temp:
    node_id: 2
    index: 2011
    poll_rate: 10

  MotorTemp:
    node_id: 1
    index: 2010
    subindex: 0
    poll_rate: 0.5
```

NOTE: it is important to remember that not all nodes on the bus will support this,
but the Motor Controller definitely will.

A complete description of all data that can be accessed from the motor controller can be found
[here](https://docplayer.net/48431275-Emdrive-firmware-specifications.html)

Further reading on Service Data and Process Data can be found
[here](http://www.byteme.org.uk/canopenparent/canopen/sdo-service-data-objects-canopen/)
and
[here](http://www.byteme.org.uk/canopenparent/canopen/pdo-process-data-objects-canopen/)

### Calibration

Calibration is configured in a separate python file called user_cal.py in the calibration folder.
A Calibration function is defined using the `@cal_function` function decorator, which takes
two arguments:

- `target`: the name of the data being generated
- `requires`: a list of the data needed as arguments

All data is indexed as a tuple of its source node as a string and its name as defined in the
data section of the `config.yaml` file. The requires field will accept either a list such tuples,
or a list of strings with the structure `'<nodename>: <data_name>`, using a colon and space to delimit them


```python

# Converts ambient temp of pack1 to farenheit because
# we live in America god damn it
@cal_function(target='PackTemp_Farenheit', requires=['PACK1: AMBIENT_TEMP'])
def packtemp_farenheit(args):
	temp, *other = args

	temp_faranheit = temp * (9/5) + 32

	return temp_faranheit

# Calculates the current TS power draw in kW
@cal_function(target='TS_POWER', requires=[('TSI', 'TS_VOLTAGE'), ('TSI', 'TS_CURRENT')])
def ts_power(args):
	voltage, current, *other = args

	power = (voltage * current) / 100

	return power
```

Data generated by these functions will be outputed to the same data cache structure as the rest,
and will have an index of `('SCADA', '<data_name>')`, allowing it to be accessed by other
calibration functions or other parts of the program


### GUI

This section defines the structure of the GUI sensors tab, which displays live data as it is read by
the bus. Each key represents the name of the data being displayed, data_target describes the source of the data,
using the colon delimited inexing scheme described above.

oprange is a list of 4 values defining the operating range of the value.
values in between the middle two values are considered nominal and displayed in blue,
values outside of the middle two but inside the outer two are displayed in yellow,
values outside of the outer two are considered errors, and displayed in red.

```yaml
GUI:
  Sensors: # All sensors that will report to SCADA, divided into top-level groups
    GLV:
      Voltage:
          data_target: Null
          unit: 'V'
          oprange: [10, 15, 65, 70]
          open_sloop_out_of_range: no
    
    TSI:
      TS Voltage:
          data_target: 'TSI: TS_VOLTAGE'
          unit: 'V'
          oprange: [80, 90, 120, 150]
          open_sloop_out_of_range: no
      TS Current:
          data_target: 'TSI: TS_CURRENT'
          unit: 'A'
          oprange: [Null, Null, 250, 300]
          open_sloop_out_of_range: yes
      TS Power:
          data_target: 'SCADA: TS_POWER'
          unit: 'kW'
          oprange: [10, 15, 65, 70]
          open_sloop_out_of_range: no
```

