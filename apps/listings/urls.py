from django.urls import path

from . import views

app_name = "listings"

urlpatterns = [
    path("", views.search, name="search"),
    path("saved/", views.saved, name="saved"),
    path("new/", views.create, name="create"),
    path("<slug:slug>/", views.detail, name="detail"),
    path("<slug:slug>/edit/", views.edit, name="edit"),
    path("<slug:slug>/manage/", views.manage, name="manage"),
    path("<slug:slug>/publish/", views.publish, name="publish"),
    path("<slug:slug>/unpublish/", views.unpublish, name="unpublish"),
    path("<slug:slug>/mark-rented/", views.mark_rented, name="mark_rented"),
    path("<slug:slug>/save/", views.toggle_save, name="toggle_save"),
]
