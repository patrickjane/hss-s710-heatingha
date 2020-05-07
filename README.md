# HSS + Homeassistant Heating

Skill zur Sprachsteuerung der Heizung / Climate-Komponente über Home Assistant (https://www.home-assistant.io/). Nutzt die Home Assistant REST API.

## Installation

#### 1) Home Assistant Access Token anlegen

Im Home Assistant Web-GUI auf das Profil klicken, und dort (siehe auch: https://www.home-assistant.io/docs/authentication/#your-account-profile) unter **Long-Lived Access Tokens** einen Token erstellen. Dieser wird als Konfigurationsparameter für den Skill benötigt.

#### 2) Installation des Skills im HSS

```
/home/s710 $> cd hss
/home/s710/hss $> source venv/bin/activate
(venv) /home/s710/hss $> hss-cli --install --url=https://github.com/patrickjane/hss-s710-heatingha
Installing 'hss-s710-heatingha' into '/home/pi/.config/hss_server/skills/hss-s710-heatingha'
Cloning repository ...
Creating venv ...
Installing dependencies ...
[...]
Initializing config.ini ...
Section 'skill'
Enter value for parameter 'hass_token': xxxxxx
Enter value for parameter 'entity_dict': {"arbeitszimmer": "climate.eurotronic_eur_spiritz_wall_radiator_thermostat_heat_2", "wohnzimmer": "climate.eurotronic_eur_spiritz_wall_radiator_thermostat_heat_4", "flur": "climate.eurotronic_eur_spiritz_wall_radiator_thermostat_heat_3", "schlafzimmer": "climate.eurotronic_eur_spiritz_wall_radiator_thermostat_heat"}

Skill 'hss-s710-heatingha' successfully installed.

(venv) /home/s710/hss $>
```

#### 3) HSS neu starten

Nach der Installation von Skills muss der Hermes Skill Server neu gestartet werden.

# Parameter

Die App bentöigt die folgenden Parameter:

- `entity_dict`: Ein JSON-Dictionary mit dem Mapping aus Raumname und Entity-ID (z.b. `{"wohnzimmer":"climate.eurotronic_eur_spiritz_wall_radiator_thermostat_heat_4"}`)
- `hass_host`: Hostname der Home Assistant Installation inkl. Protokoll und Port (z.b. `http://10.0.0.5:8123`)
- `hass_token`: Der Access-Token der in Schritt Installation/1) erstellt wurde

# Funktionen

Die App umfasst folgende Intents:

- `s710:isHeatingOn` - Abfrage ob die Heizung in einem Raum an oder aus ist
- `s710:enableHeating` - Einschalten der Heizung in einem Raum (optional mit Temperatur)
- `s710:disableHeating` - Ausschalten der Heizung in einem Raum
- `s710:setTemperature` - Setzen der Temperatur einer Heizung

Die App nutzt die Services `climate.turn_on`, `climate.turn_off`, `climate.set_temperature` sowie `GET:/api/states`. Es wird jeweils eine gültige Entity-ID der gewünschten Climate-Komponente benötigt, andernfalls funktioniert der Service-Call nicht.
