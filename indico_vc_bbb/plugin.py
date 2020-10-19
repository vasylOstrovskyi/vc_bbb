# This file is part of the Indico plugins.
# Copyright (C) 2002 - 2020 CERN
#
# The Indico plugins are free software; you can redistribute
# them and/or modify them under the terms of the MIT License;
# see the LICENSE file for more details.

from __future__ import unicode_literals
import uuid
import xml.etree.ElementTree as ET
import requests
from datetime import datetime
from flask import session
from flask import render_template
from flask_pluginengine import render_plugin_template


from sqlalchemy.orm.attributes import flag_modified
from wtforms.fields import IntegerField, TextAreaField
from wtforms.fields.core import BooleanField, SelectField
from wtforms.fields.html5 import EmailField, URLField
from wtforms.fields.simple import StringField, TextAreaField
from wtforms.validators import DataRequired, NumberRange

from indico.core.plugins import IndicoPlugin, IndicoPluginBlueprint, url_for_plugin
from indico.modules.vc import VCPluginMixin, VCPluginSettingsFormBase
from indico.web.forms.widgets import SwitchWidget
from indico.web.forms.base import generated_data, FormDefaults
from indico.web.forms.fields import IndicoPasswordField, PrincipalListField, FileField

from indico.util.i18n import _

from indico.modules.events.views import WPSimpleEventDisplay
from indico.modules.vc.views import WPVCEventPage, WPVCManageEvent
from indico.modules.vc.forms import VCRoomAttachFormBase, VCRoomFormBase

from indico_vc_bbb.util import retrieve_principal
from indico_vc_bbb.api import is_meeting_running, get_recordings
from indico_vc_bbb.blueprint import blueprint
from indico_vc_bbb.forms import PluginSettingsForm, VCRoomForm, VCRoomAttachForm, VCRoomPreloadForm


class BigBlueButtonPlugin(VCPluginMixin, IndicoPlugin):
    """BigBlueButton

    BigBlueButton videoconferencing plugin
    """
    configurable = True
    settings_form = PluginSettingsForm
    vc_room_form = VCRoomForm
    vc_room_attach_form = VCRoomAttachForm
    vc_room_preload_form = VCRoomPreloadForm
    friendly_name = "BigBlueButton"

    @property
    def default_settings(self):
        return dict(VCPluginMixin.default_settings, **{
            'bbb_api_link': 'https://bbb.yourdomain.tld/bigbluebutton',
            'bbb_secret': ''
        })

    @property
    def logo_url(self):
        return url_for_plugin(self.name + '.static', filename='images/bbb_logo.png')

    @property
    def icon_url(self):
        return url_for_plugin(self.name + '.static', filename='images/bbb_icon.png')

    def get_blueprints(self):
        return blueprint

    def create_room(self, vc_room, event):
	room_id = str(uuid.uuid4())
	moderator_password = 'mp'
	attendee_password = 'ap'
        vc_room.data = { 
    		'room_id': room_id, 
    		'moderator_password': moderator_password, 
    		'attendee_password': attendee_password 
    	}

        flag_modified(vc_room, 'data')
        

    def delete_room(self, vc_room, event):
        pass

    def update_room(self, vc_room, event):
        pass


    def refresh_room(self, vc_room, event):
        pass
        

    def update_data_association(self, event, vc_room, event_vc_room, data):
        super(BigBlueButtonPlugin, self).update_data_association(event, vc_room, event_vc_room, data)
        event_vc_room.data.update(self.get_vc_room_form_defaults(event))
        event_vc_room.data.update({key: data.pop(key) for key in list(set(data.keys()) & {
            'moderators',
	    'record',
	    'welcome', 
            'auto_start_recording', 
            'allow_start_stop_recording', 
	    'webcams_only_for_moderator', 
	    'mute_on_start', 
	    'allow_mods_to_unmute_users', 
	    'lock_settings_disable_cam', 
	    'lock_settings_disable_mic', 
	    'lock_setiings_disable_private_chat', 
	    'lock_settings_disable_public_chat', 
	    'lock_settings_disable_note', 
	    'lock_settings_locked_layout', 
	    'guest_policy'
        })
        })

        flag_modified(event_vc_room, 'data')

    def render_manage_event_info_box(self, vc_room, event_vc_room, event, **kwargs):
        moderators_names = []
        for moderator in event_vc_room.data['moderators']:
                moderators_names.append(retrieve_principal(moderator).get_full_name(last_name_upper=False, last_name_first=False, abbrev_first_name=False))
 
        kwargs = {'moderators': ', '.join(moderators_names)}
        return super(BigBlueButtonPlugin, self).render_manage_event_info_box(vc_room, event_vc_room, event, **kwargs)

    def render_info_box(self, vc_room, event_vc_room, event, **kwargs):
        moderators_names = []
        for moderator in event_vc_room.data['moderators']:
                moderators_names.append(retrieve_principal(moderator).get_full_name(last_name_upper=False, last_name_first=False, abbrev_first_name=False))
        kwargs = { 'moderators': ', '.join(moderators_names) }
        return super(BigBlueButtonPlugin, self).render_info_box(vc_room, event_vc_room, event, **kwargs)

    def render_event_buttons(self, vc_room, event_vc_room, **kwargs):
        event = event_vc_room.event
        if session.user:
    	    is_moderator = list(session.user.as_principal) in event_vc_room.data['moderators']
    	else:
    	    is_moderator=False
        is_running = is_meeting_running(vc_room)
        ended = False
        recordings_xml = get_recordings(event_vc_room)
        root = ET.fromstring(recordings_xml)
        try:
    	    rec = root.iter('recording').next()
    	except:
	    recorded = False
    	else:
    	    recorded = True
        if event.end_dt < datetime.now(event.tzinfo):
	    ended = True
	
	kwargs = { 'is_running': is_running, 'ended': ended, 'is_moderator': is_moderator, 'recorded': recorded }
        return super(BigBlueButtonPlugin, self).render_event_buttons(vc_room, event_vc_room, **kwargs)
    
    def get_vc_room_form_defaults(self, event):
        defaults = super(BigBlueButtonPlugin, self).get_vc_room_form_defaults(event)
        defaults.update({
	    'record': True,
	    'welcome': '',
            'auto_start_recording': False, 
            'allow_start_stop_recording': True, 
	    'webcams_only_for_moderator': False, 
	    'mute_on_start': True, 
	    'allow_mods_to_unmute_users': False, 
	    'lock_settings_disable_cam': False, 
	    'lock_settings_disable_mic': False, 
	    'lock_setiings_disable_private_chat': False, 
	    'lock_settings_disable_public_chat': False, 
	    'lock_settings_disable_note': False, 
	    'lock_settings_locked_layout': False, 
	    'guest_policy': 'ALWAYS_ACCEPT',
        })

        return defaults

    def render_preload_form(self, **kwargs):
        return render_plugin_template('manage_event_preload_slides.html', **kwargs)
