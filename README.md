# kostal_battery_mgr

Manage battery charging/discharging with Kostal Plenticore inverter with Modbus TCP. This script serves as a simple example that you can grow to your needs.

Make sure you have enabled external battery control with Modbus in the inverter web user interface before trying.

The Kostal Plenticore inverters can be set to external battery control. In this mode, they expect a command over Modbus/TCP every n seconds (where n can be configured in the web user interface of the inverter). With external battery control it is possible to discharge the battery (even to the grid) or force a charge of the battery (even from the grid). 

This comes useful if you have a varying electricity price. It is possible to charge the battery during the lower priced hours and discharge it when the prices are higher even when solar power is not available (e.g. in the winter time). Another use case is discharging the battery to the grid (selling energy) in the summer time during more expensive hours if there is no local need for the energy (e.g. in the summer nights when you don't consume much energy, but price might be higher). 

## Operation

This script reads a specified file (by default called kostal_battery_state) and based on the contents of this file it updates the state of the inverter with Modbus. The idea is that you have another process or piece of software that you run once per hour from cron. That piece of software makes the decisions on how the battery should be operated and writes the state into the state file. The kostal_battery_poll.py just reads the state file and performs actions accordingly.

I'm running a script that fetches the local electricity prices and schedules the usage of the battery accordingly. I call this script from cron every hour.
