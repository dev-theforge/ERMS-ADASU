from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from apps.accounts import views as acc_views

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', acc_views.landing_view, name='landing'),
    path('dashboard/', acc_views.dashboard_redirect, name='dashboard'),
    path('accounts/', include('apps.accounts.urls', namespace='accounts')),
    path('admin-panel/', include('apps.accounts.admin_urls', namespace='admin_panel')),
    path('lecturer/', include('apps.results.lecturer_urls', namespace='lecturer')),
    path('student/', include('apps.results.student_urls', namespace='student')),
    path('parent/', include('apps.accounts.parent_urls', namespace='parent')),
    path('complaints/', include('apps.complaints.urls', namespace='complaints')),
    path('notifications/', include('apps.notifications.urls', namespace='notifications')),
    path('feedback/', include('apps.feedback.urls', namespace='feedback')),
    path('reports/', include('apps.reports.urls', namespace='reports')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

admin.site.site_header = 'ERMS — Adasu University Admin'
admin.site.site_title = 'ERMS Admin'
admin.site.index_title = 'Examination Results Management'
