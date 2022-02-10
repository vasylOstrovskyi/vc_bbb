# This file is part of the Indico plugins.
# Copyright (C) 2002 - 2020 CERN
#
# The Indico plugins are free software; you can redistribute
# them and/or modify them under the terms of the MIT License;
# see the LICENSE file for more details.

from flask import session

from wtforms import BooleanField, SelectField
from wtforms.fields import URLField
from wtforms.fields.simple import StringField, TextAreaField
from wtforms.validators import DataRequired

from indico.modules.vc import VCPluginSettingsFormBase
from indico.modules.vc.forms import VCRoomAttachFormBase, VCRoomFormBase
from indico.web.forms.widgets import SwitchWidget
from indico.web.forms.base import IndicoForm, generated_data

from indico.util.i18n import _
from indico.web.forms.fields import PrincipalListField, EditableFileField, IndicoPasswordField

from indico_vc_bbb.util import retrieve_principal, get_slides_metadata

class PluginSettingsForm(VCPluginSettingsFormBase):
    bbb_api_link = URLField(_('API endpoint'), [DataRequired()],
                                description=_('URL returned by "bbb-conf --secret", E.g., https://bbb.yourdomain.tld/bigbluebutton/'))
    bbb_secret = IndicoPasswordField(_('BBB Secret'), [DataRequired()],
                                description=_('Secret returned by "bbb-conf --secret"'))

class BBBAdvancedFormMixin(object):
    # Advanced options (per event)
    welcome = TextAreaField(_('Welcome message'), description=_('You can include keywords (%%CONFNAME%%, %%DIALNUM%%, %%CONFNUM%%) which will be substituted automatically.'))

    record = BooleanField(_('Record'),
                                widget=SwitchWidget(),
                                description=_("Enable recordings (disable if need privacy)"))

    auto_start_recording = BooleanField(_('Start recordings'),
                            widget=SwitchWidget(),
                            description=_("Start session recording automatically"))

    allow_start_stop_recording = BooleanField(_('Recording control'),
                                 widget=SwitchWidget(),
                                 description=_("Enable moderator to start and pause recording"))

    webcams_only_for_moderator = BooleanField(_('Webcams to moderator only'),
                                      widget=SwitchWidget(),
                                      description=_("Show webcams to moderator only"))

    mute_on_start = BooleanField(_('Mute on start'),
                                      widget=SwitchWidget(),
                                      description=_("Mute all users on session start"))

    allow_mods_to_unmute_users = BooleanField(_('Allow unmute'),
                                      widget=SwitchWidget(),
                                      description=_("Allow moderators to unmute users"))

    lock_settings_disable_cam = BooleanField(_('Lock disable cameras'),
                                      widget=SwitchWidget(),
                                      description=_("Prevent users from sharing their webcams"))

    lock_settings_disable_mic = BooleanField(_('Lock disable microphones'),
                                      widget=SwitchWidget(),
                                      description=_("Force users to join listen only"))

    lock_setiings_disable_private_chat = BooleanField(_('Lock disable private chats'),
                                      widget=SwitchWidget(),
                                      description=_("Disable private chats in the meeting"))

    lock_settings_disable_public_chat = BooleanField(_('Lock disable public chat'),
                                      widget=SwitchWidget(),
                                      description=_("Disable public chat in the meeting"))

    lock_settings_disable_note = BooleanField(_('Lock disable notes'),
                                      widget=SwitchWidget(),
                                      description=_("Disable notes in the meeting"))

    lock_settings_locked_layout = BooleanField(_('Lock layout'),
                                      widget=SwitchWidget(),
                                      description=_("Lock layout in the meeting"))

    guest_policy = SelectField(_('Guest policy'),
                                      choices=[('ALWAYS_ACCEPT', _('Accept')), ('ALWAYS_DENY', _('Deny')), ('ASK_MODERATOR', _('Ask moderator'))])

class VCRoomForm(VCRoomFormBase, BBBAdvancedFormMixin):
    advanced_fields = ['welcome', 
                        'record',
                        'auto_start_recording', 
                        'allow_start_stop_recording', 
                        'mute_on_start', 
                        'allow_mods_to_unmute_users', 
                        'webcams_only_for_moderator', 
                        'lock_settings_disable_cam', 
                        'lock_settings_disable_mic', 
                        'lock_setiings_disable_private_chat', 
                        'lock_settings_disable_public_chat', 
                        'lock_settings_disable_note', 
                        'lock_settings_locked_layout', 
                        'guest_policy', 
                        'show']
    skip_fields = set(advanced_fields) | VCRoomFormBase.conditional_fields

    mod_users = PrincipalListField(_('Moderators'), [DataRequired()])
    
    @generated_data
    def moderators(self):
        return list(mod_user.as_principal for mod_user in self.mod_users.data)

    def __init__(self, *args, **kwargs):
        defaults = kwargs['obj']
        if defaults.mod_users is None and defaults.moderators is not None:
            defaults.mod_users = set()
            for moderator in defaults.moderators:
                defaults.mod_users.add(retrieve_principal(moderator))
        if defaults.mod_users is None:
            defaults.mod_users = [session.user]
        super(VCRoomForm, self).__init__(*args, **kwargs)

class VCRoomAttachForm(VCRoomAttachFormBase):

    mod_users = PrincipalListField(_('Moderators'), [DataRequired()])

    @generated_data
    def moderators(self):
        return list(mod_user.as_principal for mod_user in self.mod_users.data)

    def __init__(self, *args, **kwargs):
        defaults = kwargs['obj']

        if defaults.mod_users is None and defaults.moderators is not None:
            defaults.mod_users = set()
            for moderator in defaults.moderators:
                defaults.mod_users.add(retrieve_principal(moderator))
        if defaults.mod_users is None:
            defaults.mod_users = [session.user]
        super(VCRoomAttachForm, self).__init__(*args, **kwargs)

class VCRoomPreloadForm(IndicoForm):
    slides = EditableFileField(_('slides'),  lightweight=True, 
    get_metadata=get_slides_metadata, 
    multiple_files=True,
    # max_file_size=2,
    accepted_file_types='.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx,.txt,.rtf,.odt,.ods,.odp,.odg,.odc,.odi,.jpg,.jpeg,.png',
    add_remove_links=True, 
    handle_flashes=True
    )

