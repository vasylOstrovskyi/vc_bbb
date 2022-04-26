# This file is part of the Indico plugins.
# Copyright (C) 2002 - 2020 CERN
#
# The Indico plugins are free software; you can redistribute
# them and/or modify them under the terms of the MIT License;
# see the LICENSE file for more details.


from datetime import datetime
from base64 import b64encode
from io import BytesIO
import xml.etree.ElementTree as ET
import requests
from flask import session, request, redirect, flash, jsonify
from sqlalchemy.orm.attributes import flag_modified
from flask_pluginengine import render_plugin_template


from indico.util.string import crc32
from indico.util.fs import secure_filename
from indico.web.forms.base import FormDefaults


from indico.web.util import _pop_injected_js, jsonify_data, jsonify_template
from indico.core.plugins import url_for_plugin
from indico.web.flask.util import url_for
from indico.util.i18n import _


from indico.modules.auth.util import redirect_to_login
from indico.modules.events.controllers.base import RHDisplayEventBase 
from indico.modules.vc.controllers import RHEventVCRoomMixin, RHVCSystemEventBase
from indico.modules.vc.exceptions import VCRoomError

from indico.modules.vc.models.vc_rooms import VCRoomEventAssociation

from indico_vc_bbb.api import get_create_meeting_url, get_join_url, is_meeting_running, get_recordings, get_delete_recording_url, set_publish_recording_url

class RHStartAndJoin(RHDisplayEventBase):
    def _process_args(self):
        self.event_vc_room = VCRoomEventAssociation.get(request.view_args['event_vc_room_id'])
        self.vc_room = self.event_vc_room.vc_room
        self.event = self.event_vc_room.event
    def _process(self):
        if not session.user:
            return redirect_to_login(next_url=url_for_plugin('vc_bbb.start_and_join', self.event_vc_room), reason='Please, identify yourself')
        create_url = get_create_meeting_url(self.vc_room, self.event_vc_room)
        is_moderator = list(session.user.as_principal) in self.event_vc_room.data['moderators']
        join_url = get_join_url(self.vc_room, is_moderator)
        if is_meeting_running(self.vc_room):
            return redirect(join_url)
        if not is_moderator:
            return redirect(url_for('vc.event_videoconference', self.event))
        try:
            files = self.event_vc_room.data['file']
        except KeyError:
            files = None
        if files and len(files):
            xml = "<?xml version='1.0' encoding='UTF-8'?><modules>"
            for f in files:
                xml += "<module name=\"presentation\"><document name=\"" + f['filename'] + "\">" + f['content'] + "</document></module>"
            xml += "</modules>"
            r = requests.post(create_url, data=xml, headers={'Content-type': 'application/xml'})
        else:
            r = requests.get(create_url)
        root = ET.fromstring(r.content)
        status = root.find('returncode').text
        if status == 'SUCCESS':
            internal_id = root.find('internalMeetingID').text
            try:
                running = internal_id in self.event_vc_room.data['internal_id_list']
            except KeyError:
                self.event_vc_room.data['internal_id_list'] = [ internal_id ]
                running = False
            else:
                if not running:
                    self.event_vc_room.data['internal_id_list'].append(internal_id)
            flag_modified(self.event_vc_room, 'data')
            return redirect(join_url)
        else:
            raise VCRoomError(_("Cannot create room"))
            return jsonify_data(flash=False)

class RHVCManageEventSlides(RHVCSystemEventBase):
    """Preloads slides for an existing VC room"""

    def _process(self):
        if not self.plugin.can_manage_vc_rooms(session.user, self.event):
            flash(_('You are not allowed to modify {} rooms for this event.').format(self.plugin.friendly_name),
                  'error')
            return redirect(url_for('vc.manage_vc_rooms', self.event))

        try:
            slides = self.event_vc_room.data['file']
        except KeyError:
            slides = []
        deb_info = len(slides)
        defaults = FormDefaults(slides=slides)
        form = self.plugin.vc_room_preload_form(prefix='bbb-', obj=defaults, event_vc_room=self.event_vc_room)

        if form.validate_on_submit():
            added = form.slides.data['added']
            deleted = form.slides.data['deleted']
            try:
                file_data = self.event_vc_room.data['file']
            except KeyError:
                file_data=[]

            try:
                file_data = [ d for d in file_data if d['id'] not in deleted ]
            except KeyError:
                pass

            try:
                counter = file_data[-1]['id']
            except IndexError:
                counter = 0

            for f in added:
                counter += 1
                slides_bytes = BytesIO()
                f.save(slides_bytes)
                slides_bytes.seek(0)
                content = slides_bytes.read()
                encoded_content = b64encode(content)
                if len(encoded_content) > 2048000:
                    flash(_('File too large'), 'error')
                    return jsonify_data(flash=False)
                size = len(content)
                filename = secure_filename(f.filename, 'presentation')
                file_data.append({'id': counter, 'content': encoded_content.decode('ascii'), 'size': size, 'filename': filename})
            self.event_vc_room.data.update({'file': file_data})
            flag_modified(self.event_vc_room, 'data')
            flash(_('File list updated'), 'success')
            return jsonify_data(flash=False)

        form_html = self.plugin.render_preload_form(plugin=self.plugin, form=form, event_vc_room=self.event_vc_room)
        return jsonify(html=form_html, js=_pop_injected_js())

class RHVCManageEventRecordings(RHVCSystemEventBase):
    """Manage recordings for VC room: publish, unpublish, delete"""
    def _process(self):
        if not self.plugin.can_manage_vc_rooms(session.user, self.event):
            flash(_('You are not allowed to modify {} rooms for this event.').format(self.plugin.friendly_name),
                  'error')
            return redirect(url_for('vc.manage_vc_rooms', self.event))

        try:
            id = request.args['id']
        except KeyError:
            id = ''
        else:
            r = requests.get(get_delete_recording_url(id))
            root = ET.fromstring(r.content)
            status = root.find('returncode').text
            if status == 'SUCCESS':
                flash(_("Recording deleted"), 'success')
            else:
                flash(_("Recording not deleted"), 'error')

        recordings_xml = get_recordings(self.event_vc_room)
        root = ET.fromstring(recordings_xml)
        data = []
        for rec in root.iter('recording'):
            recording_data={ 
                            'start_date': datetime.fromtimestamp(float(rec.find('startTime').text)/1000).strftime('%x %X'),
                            'end_date': datetime.fromtimestamp(float(rec.find('startTime').text)/1000).strftime('%X'),
                            'state': rec.find('state').text,
                            'record_id': rec.find('recordID').text,
                            'remove_url': get_delete_recording_url(rec.find('recordID').text)
                             }
            for format in rec.iter('format'):
                if format.find('type').text == 'presentation':
                    recording_data.update({'url': format.find('url').text, 'length': format.find('length').text})
                    previews = []
                    for image in format.iter('image'):
                        previews.append({'src': image.text, 'alt': image.attrib['alt'], 'width': image.attrib['width'], 'height': image.attrib['height']})
                    recording_data.update({'previews': previews})
            data.append(recording_data)
        return jsonify_template('manage_recordings.html', render_plugin_template, text=data, event_vc_room=self.event_vc_room, id=id)

class RHVCViewEventRecordings(RHDisplayEventBase):
    """View recordings for VC room"""
    def _process_args(self):
        self.event_vc_room = VCRoomEventAssociation.get(request.view_args['event_vc_room_id'])
#        self.vc_room = self.event_vc_room.vc_room
        self.event = self.event_vc_room.event
    def _process(self):
        recordings_xml = get_recordings(self.event_vc_room)
        root = ET.fromstring(recordings_xml)
        data = []
        for rec in root.iter('recording'):
            recording_data={ 
                            'start_date': datetime.fromtimestamp(float(rec.find('startTime').text)/1000).strftime('%Y-%M-%d %X'),
                            'end_date': datetime.fromtimestamp(float(rec.find('startTime').text)/1000).strftime('%X'),
                            'state': rec.find('state').text,
                            'record_id': rec.find('recordID').text,
                            'participants': rec.find('participants').text
                             }
            for format in rec.iter('format'):
                if format.find('type').text == 'presentation':
                    recording_data.update({'url': format.find('url').text, 'length': format.find('length').text})
                    previews = []
                    for image in format.iter('image'):
                        previews.append({'src': image.text, 'alt': image.attrib['alt'], 'width': image.attrib['width'], 'height': image.attrib['height']})
                    recording_data.update({'previews': previews})
            data.append(recording_data)
        return jsonify_template('list_recordings.html', render_plugin_template, recordings=data, event_vc_room=self.event_vc_room)
