# -*- coding: utf-8 -*-
__author__ = 'Florian Österreich'

from tests import OldPythonTestCase
from pycroft.lib.finance import create_semester
from pycroft import model
from pycroft.model import session
from datetime import datetime

class Test_010_Create_Semester(OldPythonTestCase):

    @classmethod
    def setUpClass(cls):
        session.reinit_session("sqlite://")
        model.drop_db_model()
        model.create_db_model()

    def tearDown(self):
        session.session.remove()

    def test_010_new_semester(self):
        new_semester = create_semester("Testsemester", "2500", "1500", datetime.now(), datetime.now())
        self.assertEqual(new_semester.registration_fee,2500)
        self.assertEqual(new_semester.semester_fee,1500)