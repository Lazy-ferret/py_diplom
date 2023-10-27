from rest_framework import permissions


class IsShop(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.type == "shop"
