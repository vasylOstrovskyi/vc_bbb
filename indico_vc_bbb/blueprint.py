# This file is part of the Indico plugins.
# Copyright (C) 2002 - 2020 CERN
#
# The Indico plugins are free software; you can redistribute
# them and/or modify them under the terms of the MIT License;
# see the LICENSE file for more details.


from indico.core.plugins import IndicoPluginBlueprint

from indico_vc_bbb.controllers import RHStartAndJoin, RHVCManageEventSlides, RHVCManageEventRecordings, RHVCViewEventRecordings


blueprint = IndicoPluginBlueprint('vc_bbb', 'indico_vc_bbb')

blueprint.add_url_rule('/event/<int:event_id>/videoconference/<any(bbb):service>/<int:event_vc_room_id>/start',
                       'start_and_join', RHStartAndJoin, methods=('POST', 'GET'))
blueprint.add_url_rule('/event/<int:event_id>/manage/videoconference/<any(bbb):service>/<int:event_vc_room_id>/slides',
                       'slides', RHVCManageEventSlides, methods=('POST', 'GET'))
blueprint.add_url_rule('/event/<int:event_id>/manage/videoconference/<any(bbb):service>/<int:event_vc_room_id>/recordings',
                       'recordings', RHVCManageEventRecordings)
blueprint.add_url_rule('/event/<int:event_id>/manage/videoconference/<any(bbb):service>/<int:event_vc_room_id>/view_recordings',
                       'view_recordings', RHVCViewEventRecordings)

