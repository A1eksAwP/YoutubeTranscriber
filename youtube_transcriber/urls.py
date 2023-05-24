from django.contrib import admin
from django.urls import path, include
from transcribe_app.views import main

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', main),
    path('transcribe/', include('transcribe_app.urls')),
]
''