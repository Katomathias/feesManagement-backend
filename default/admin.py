from django.contrib import admin
from . models import *

# Register your models here.
admin.site.register([
 Students,
 Levels,
 AmountPaid,
 PasswordResets,
 UserProfile,
 Content
])
#REGISTER THE MODELS 
