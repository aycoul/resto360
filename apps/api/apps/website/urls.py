"""
Website Generator URL Configuration
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

router = DefaultRouter()
router.register(r"gallery", views.WebsiteGalleryViewSet, basename="gallery")
router.register(r"hours", views.WebsiteBusinessHoursViewSet, basename="hours")
router.register(r"contacts", views.WebsiteContactFormViewSet, basename="contacts")

urlpatterns = [
    path("", include(router.urls)),
    path("config/", views.WebsiteView.as_view(), name="website-config"),
    path("publish/", views.WebsitePublishView.as_view(), name="website-publish"),
    path("templates/", views.TemplateChoicesView.as_view(), name="website-templates"),
    path("check-subdomain/", views.CheckSubdomainView.as_view(), name="check-subdomain"),
    path("update-subdomain/", views.UpdateSubdomainView.as_view(), name="update-subdomain"),
    # Public endpoints
    path("public/<str:subdomain>/", views.PublicWebsiteView.as_view(), name="public-website"),
    path("public/<str:subdomain>/contact/", views.PublicContactFormView.as_view(), name="public-contact"),
]
