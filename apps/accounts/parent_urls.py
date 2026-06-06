from django.urls import path
from . import parent_views

app_name = 'parent'

urlpatterns = [
    path('dashboard/', parent_views.parent_dashboard, name='dashboard'),
    path('link-ward/', parent_views.link_ward, name='link_ward'),
    path('ward/<int:ward_id>/results/', parent_views.ward_results, name='ward_results'),
    path('ward/<int:ward_id>/history/', parent_views.ward_history, name='ward_history'),
]
