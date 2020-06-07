#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# -----------------------------------------------------------------------------
# Snips Heizung + Homeassistant
# -----------------------------------------------------------------------------
# Copyright 2019 Patrick Fial
# -----------------------------------------------------------------------------
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial
# portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT
# LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
# IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY,
# WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

# -----------------------------------------------------------------------------
# Imports
# -----------------------------------------------------------------------------

import requests
import logging
import json
from os import environ

from hss_skill import hss

# -----------------------------------------------------------------------------
# global definitions (home assistant service URLs)
# -----------------------------------------------------------------------------

HASS_GET_STATE_SVC = "/api/states/"
HASS_HEAT_ON_SVC = "/api/services/climate/turn_on"
HASS_HEAT_OFF_SVC = "/api/services/climate/turn_off"
HASS_SET_TEMP_SVC = "/api/services/climate/set_temperature"

SKILL_ID = "s710-heating"

# -----------------------------------------------------------------------------
# class Skill
# -----------------------------------------------------------------------------

class Skill(hss.BaseSkill):

    # -------------------------------------------------------------------------
    # ctor

    def __init__(self):
        super().__init__()

        # parameters

        self.hass_host = None
        self.hass_token = None

        self.my_intents = ['s710:isHeatingOn','s710:enableHeating','s710:disableHeating','s710:setTemperature']

        # try to use HASSIO token via environment variable & internal API URL in case no config.ini parameters are given

        if 'hass_token' in self.config['skill']:
            self.hass_token = self.config['skill']['hass_token']
        elif 'HASSIO_TOKEN' in environ:
            self.hass_token = environ['HASSIO_TOKEN']

        if 'hass_host' in self.config['skill']:
            self.hass_host = self.config['skill']['hass_host']
        elif self.hass_token is not None and 'HASSIO_TOKEN' in environ:
            self.hass_host = 'http://hassio/homeassistant/api'

        self.hass_headers = { 'Content-Type': 'application/json', 'Authorization': "Bearer " + self.hass_token }

        if 'entity_dict' in self.config['skill']:
            try:
                self.entity_dict = json.loads(self.config['skill']['entity_dict'])
            except Exception as e:
                self.logger.error('Failed to parse entity-dictionary ({})'.format(e))
                self.entity_dict = {}
        else:
            self.entity_dict = {}

    # --------------------------------------------------------------------------
    # get_intentlist (overwrites BaseSkill.get_intentlist)
    # --------------------------------------------------------------------------

    async def get_intentlist(self):
        return self.my_intents

    # --------------------------------------------------------------------------
    # handle (overwrites BaseSkill.handle)
    # --------------------------------------------------------------------------

    async def handle(self, request, session_id, site_id, intent_name, slots):
        room_id = slots["room_id"] if "room_id" in slots else None
        temperature = int(slots["temperature"]) if "temperature" in slots else None

        if room_id:
            room_id = room_id.lower().replace('ä', 'ae').replace('ü','ue').replace('ö', 'oe')

        # ignore unknown/unexpected intents

        if intent_name not in self.my_intents:
            return None

        try:
            response_message = self.process(intent_name, room_id, temperature)
        except Exception as e:
            self.log.error("Failed to execute action ({})".format(e))
            response_message = 'Aktion konnte nicht durchgeführt werden'

        return self.answer(session_id, site_id, response_message, "de_DE")

    # -------------------------------------------------------------------------
    # process

    def process(self, intent_name, room_id, temperature):
        if room_id not in self.entity_dict:
            self.logger.error('Room "{}" not known, cannot determine entity_id. Must skip request.'.format(room_id))
            return 'Unbekannter Raum'

        entity_id = self.entity_dict[room_id]

        if intent_name == 's710:isHeatingOn':
            r = requests.get(self.hass_host + HASS_GET_STATE_SVC + entity_id, headers = self.hass_headers)

            # evaluate service response & send snips reply

            if r.status_code != 200:
                self.logger.error('REST API call failed ({}/{})'.format(r.status_code, r.content.decode('utf-8')[:80]))
                return 'Aktion konnte nicht durchgeführt werden'
            else:
                try:
                    response = json.loads(r.content.decode('utf-8'))
                except Exception as e:
                    self.logger.error('Failed to parse REST API response ({}/{})'.format(e, r.content.decode('utf-8')[:80]))
                    return 'Aktion konnte nicht durchgeführt werden'

                if 'state' not in response or response['state'] == 'off':
                    return 'Nein, die Heizung ist aus.'

                temp = None

                if 'attributes' in response and 'temperature' in response['attributes']:
                    temp = str(response['attributes']['temperature'])
                    return 'Ja, die Heizung ist an auf ' + temp + ' Grad.'

                return 'Ja, die Heizung ist an.'
        else:
            r = None
            data = { "entity_id": entity_id }
            text = None

            if intent_name == 's710:enableHeating':
                r = requests.post(self.hass_host + HASS_HEAT_ON_SVC, json = data, headers = self.hass_headers)
                text = 'Heizung eingeschaltet.'

                if r.status_code == 200 and temperature:
                    data['temperature'] = temperature
                    r = requests.post(self.hass_host + HASS_SET_TEMP_SVC, json = data, headers = self.hass_headers)
                    text = 'Heizung eingeschaltet auf ' + str(temperature) + ' Grad.'

            elif intent_name == 's710:disableHeating':
                r = requests.post(self.hass_host + HASS_HEAT_OFF_SVC, json = data, headers = self.hass_headers)
                text = 'Heizung ausgeschaltet.'
            elif intent_name == 's710:setTemperature':
                data['temperature'] = temperature
                r = requests.post(self.hass_host + HASS_SET_TEMP_SVC, json = data, headers = self.hass_headers)
                text = 'Temperatur auf ' + str(temperature) + ' gestellt.'
            else:
                print("Intent {}/parameters not recognized, ignoring".format(intent_name))
                return 'Aktion konnte nicht durchgeführt werden'

            # evaluate service response & send snips reply

            if r.status_code != 200:
                self.logger.error('REST API call failed ({}/{})'.format(r.status_code, r.content.decode('utf-8')[:80]))
                return 'Aktion konnte nicht durchgeführt werden'

            return text

