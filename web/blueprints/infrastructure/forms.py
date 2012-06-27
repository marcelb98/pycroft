# -*- coding: utf-8 -*-
# Copyright (c) 2012 The Pycroft Authors. See the AUTHORS file.
# This file is part of the Pycroft project and licensed under the terms of
# the Apache License, Version 2.0. See the LICENSE file for details.


from flaskext.wtf import Form, TextField
from wtforms.validators import Required, Regexp
from pycroft.model.ports import Port

class SwitchPortForm(Form):
    name = TextField(u"Port Name",
                        [Required(message=u"Name?"),
                         Regexp(regex=Port.name_regex,
                             message=u"Richtig ist z.B. A2")])
