from django.utils import timezone
from django.db import models
from django.contrib import admin
from django import forms
from django.contrib.auth.hashers import make_password

from hospital.admin1.user_admin import *
from hospital.admin1.prescription_admin import *
from hospital.admin1.payment_detail_admin import *
from hospital.admin1.payment_admin import *
from hospital.admin1.patient_test_admin import *
from hospital.admin1.medication_admin import *
from hospital.admin1.medical_record_admin import *
from hospital.admin1.lab_test_admin import *
from hospital.admin1.appointment_admin import *
from hospital.admin1.prescription_detail_admin import *
admin.site.site_header = "Quản lý bệnh viện LHM"

