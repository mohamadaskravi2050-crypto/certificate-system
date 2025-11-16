from django.urls import path
from . import views

urlpatterns = [
    # HTML Pages
    path('', views.HomeView.as_view(), name='home'),
    path('upload/', views.UploadView.as_view(), name='upload'),
    path('edit/<int:pdf_id>/', views.EditView.as_view(), name='edit'),
    path('fill/<int:pdf_id>/', views.FillView.as_view(), name='fill'),
    path('batch/<int:pdf_id>/', views.BatchFillView.as_view(), name='batch_fill'),
    
    # API Endpoints
    path('api/upload/', views.upload_pdf, name='api_upload'),
    path('api/list/', views.list_pdfs, name='api_list'),
    path('api/edit/<int:pdf_id>/', views.edit_pdf, name='api_edit'),
    path('api/fill/<int:pdf_id>/', views.fill_pdf, name='api_fill'),
    path('api/batch-fill/<int:pdf_id>/', views.batch_fill_pdf, name='api_batch_fill'),
    path('api/textbox/<int:textbox_id>/', views.delete_textbox, name='api_delete_textbox'),
]