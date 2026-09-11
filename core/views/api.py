from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from rest_framework import generics, permissions

from ..decorators import role_required
from ..serializers import SaleRecordSerializer


@login_required
@role_required('PHARMACY')
def api_docs(request):
    return render(request, 'core/dashboards/api_docs.html')


class IsPharmacyWithProfile(permissions.BasePermission):
    message = 'Only pharmacy accounts with a registered profile can record sales.'

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user.is_authenticated
            and user.role == 'PHARMACY'
            and hasattr(user, 'pharmacy_profile')
        )


class SaleRecordCreateAPIView(generics.CreateAPIView):
    serializer_class = SaleRecordSerializer
    permission_classes = [permissions.IsAuthenticated, IsPharmacyWithProfile]
