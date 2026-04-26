from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from rest_framework import generics, permissions
from ..serializers import SaleRecordSerializer

@login_required
def api_docs(request):
    if request.user.role != 'PHARMACY': return redirect('dashboard_redirect')
    return render(request, 'core/dashboards/api_docs.html')

class SaleRecordCreateAPIView(generics.CreateAPIView):
    serializer_class = SaleRecordSerializer
    permission_classes = [permissions.IsAuthenticated]
    def perform_create(self, serializer):
        if self.request.user.role != 'PHARMACY': raise PermissionError("Unauthorized.")
        serializer.save()
