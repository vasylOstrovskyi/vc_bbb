# This file is part of the Indico plugins.
# Copyright (C) 2002 - 2020 CERN
#
# The Indico plugins are free software; you can redistribute
# them and/or modify them under the terms of the MIT License;
# see the LICENSE file for more details.


#import re

#from flask_multipass import IdentityRetrievalFailed

#from indico.core.auth import multipass
#from indico.core.db import db
#from indico.modules.auth import Identity
from indico.modules.users import User


def retrieve_principal(principal):
    type_, id_ = principal
    if type_ in {'Avatar', 'User'}:
        return User.get(int(id_))
    else:
        raise ValueError(f'Unexpected type: {type_}')

def get_slides_metadata(file_):
    return {'id': file_['id'], 'filename': file_['filename'], 'size': file_['size'], 'content_type': 'pdf'}
