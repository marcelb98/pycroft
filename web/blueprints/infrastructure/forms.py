# -*- coding: utf-8 -*-


from flask.ext.wtf import Form, TextField, SelectField, QuerySelectField
from wtforms.validators import Required, Regexp
from pycroft.model.port import Port
from web.form.fields import ReadonlyTextField
from pycroft.model.host import ARecord


def arecords_query(host_id):
    return ARecord.q.filter(
        ARecord.host_id == host_id
    ).order_by(ARecord.id)


class SwitchPortForm(Form):
    name = TextField(u"Port Name",
        [Required(message=u"Name?"),
         Regexp(regex=Port.name_regex,
             message=u"Richtig ist z.B. A2")])


class CNameRecordEditForm(Form):
    name = TextField(u"Alias Name", [Required(message=u"Alias?")])
    alias_for = ReadonlyTextField(u"für")


class RecordCreateForm(Form):
    type = SelectField(u"Type",
        choices=[('arecord', 'ARecord'), ('aaaarecord', 'AAAARecord'),
                 ('cnamerecord', 'CNameRecord'), ('mxrecord', 'MXRecord'),
                 ('nsrecord', 'NSRecord'), ('srvrecord', 'SRVRecord')])


class CNameRecordCreateForm(Form):
    name = TextField(u"Alias Name", [Required(message=u"Alias?")])
    alias_for = QuerySelectField(u"für", get_label='name')