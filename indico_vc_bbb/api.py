# This file is part of the Indico plugins.
# Copyright (C) 2002 - 2020 CERN
#
# The Indico plugins are free software; you can redistribute
# them and/or modify them under the terms of the MIT License;
# see the LICENSE file for more details.

from __future__ import unicode_literals

from hashlib import sha1
from flask import session
from urllib import quote_plus
import requests
import xml.etree.ElementTree as ET
from indico.web.flask.util import url_for

def get_url(command, params):
    from indico_vc_bbb.plugin import BigBlueButtonPlugin
    secret = BigBlueButtonPlugin.settings.get('bbb_secret')
    api_link = BigBlueButtonPlugin.settings.get('bbb_api_link')
    request = command + params + secret
    checksum = sha1(request)
    url = api_link + '/api/' + command + '?' + params + '&checksum=' + checksum.hexdigest()
    return url

def get_create_meeting_url(vc_room, event_vc_room):
    logout_url = url_for('vc.event_videoconference', event_vc_room.event, {'_external':True})
    command = 'create'
    
    room_params = ''
    room_params +=  'name=' + quote_plus(vc_room.name.encode('utf-8')) 
    room_params += '&meetingID=' + quote_plus(vc_room.data['room_id']) 
    room_params += '&moderatorPW=' + quote_plus(vc_room.data['moderator_password']) 
    room_params += '&attendeePW=' +  quote_plus(vc_room.data['attendee_password']) 
    room_params += '&logoutURL=' + quote_plus(logout_url)
    
    event_room_params = ''
    
    if event_vc_room.data['welcome']:
	event_room_params += '&welcome=' + quote_plus(event_vc_room.data['welcome'].encode('utf-8'))

    event_room_params += '&record=' + str(event_vc_room.data['record']).lower() 
    event_room_params += '&autoStartRecording=' + str(event_vc_room.data['auto_start_recording']).lower()
    event_room_params += '&allowStartStopRecording=' + str(event_vc_room.data['allow_start_stop_recording']).lower()
    event_room_params += '&muteOnStart=' + str(event_vc_room.data['mute_on_start']).lower()
    event_room_params += '&allowModsToUnmuteUsers=' + str(event_vc_room.data['allow_mods_to_unmute_users']).lower()
    event_room_params += '&webcamsOnlyForModerator=' + str(event_vc_room.data['webcams_only_for_moderator']).lower()
    event_room_params += '&lockSettingsDisableCam=' + str(event_vc_room.data['lock_settings_disable_cam']).lower()
    event_room_params += '&lockSettingsDisableMic=' + str(event_vc_room.data['lock_settings_disable_mic']).lower()
    event_room_params += '&lockSettingsDisablePrivateChat=' + str(event_vc_room.data['lock_setiings_disable_private_chat']).lower()
    event_room_params += '&lockSettingsDisablePublicChat=' + str(event_vc_room.data['lock_settings_disable_public_chat']).lower()
    event_room_params += '&lockSettingsDisableNote=' + str(event_vc_room.data['lock_settings_disable_note']).lower()
    event_room_params += '&lockSettingsLockedLayout=' + str(event_vc_room.data['lock_settings_locked_layout']).lower()
    event_room_params += '&lockSettingsLockOnJoinConfigurable=' + 'true'
    event_room_params += '&lockSettingsLockOnJoin=' + 'true'
    event_room_params += '&guestPolicy=' + quote_plus(event_vc_room.data['guest_policy'])
#    event_room_params += '&bannerText=' + quote_plus('Big Brother is watching!!!')
#    event_room_params += '&bannerColor=' + quote_plus('#FF0000')

    request_data = room_params + event_room_params
    return get_url(command, request_data)
    
def get_join_url(vc_room, is_moderator):
    password = vc_room.data['attendee_password']
    if is_moderator:
	password = vc_room.data['moderator_password']
    command = 'join'
    params = 'fullName=' + quote_plus(session.user.name.encode('utf-8'))
    params = params + '&meetingID=' + quote_plus(vc_room.data['room_id'])
    params = params + '&password=' + quote_plus(password)
    return get_url(command, params)

def get_end_meeting_url(vc_room):
    command = 'end'
    params = 'meetingID=' + quote_plus(vc_room.data['room_id'])
    params = params + '&password=' + quote_plus(vc_room.data['moderator_password'])
    return get_url(command, params)

def is_meeting_running(vc_room):
    command = 'getMeetingInfo'
    params = 'meetingID=' + quote_plus(vc_room.data['room_id'])
    request = get_url(command, params)
    r = requests.get(request)
    root = ET.fromstring(r.content)
    status = root.find('returncode').text
    if status == 'SUCCESS':
	return True
    else:
	return False

def get_meeting_info(vc_room):
    command = 'getMeetingInfo'
    params = 'meetingID=' + quote_plus(vc_room.data['room_id'])
    request = command + params + secret
    checksum = sha1(request)
    request = get_url(command, params)
    r = requests.get(request)
    return r.content

def get_recordings(event_vc_room, state='any'):
    command = 'getRecordings'
    try:
	internal_id_list = event_vc_room.data['internal_id_list']
    except KeyError:
	internal_id_list = ['nothing']
    params = 'recordID=' + ','.join(internal_id_list)
    request = get_url(command, params)
    r = requests.get(request)
    return r.content

def set_publish_recording_url(id, publish):
    command = 'publishRecordings'
    params = 'recoredId=' + id + 'publish=' + publish
    return get_url(command, params)

def get_delete_recording_url(id):
    command = 'deleteRecordings'
    params = 'recordID=' + id
    return get_url(command, params)
    

