from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from ..models import PharmacyProfile, Antibiotic, User

@login_required
def pharmacy_list(request):
    if request.user.role != 'GOVERNMENT': return redirect('dashboard_redirect')
    if request.method == 'POST' and request.POST.get('action') == 'add':
        user = User.objects.create_user(
            username=request.POST.get('username'), password=request.POST.get('password'), role='PHARMACY'
        )
        PharmacyProfile.objects.create(
            user=user, name=request.POST.get('name'), address=request.POST.get('address'),
            latitude=float(request.POST.get('latitude')), longitude=float(request.POST.get('longitude'))
        )
        return redirect('pharmacy_list')
    return render(request, 'core/management/pharmacy_list.html', {'pharmacies': PharmacyProfile.objects.all()})

@login_required
def pharmacy_edit(request, pk):
    if request.user.role != 'GOVERNMENT': return redirect('dashboard_redirect')
    profile = get_object_or_404(PharmacyProfile, pk=pk)
    if request.method == 'POST':
        profile.name, profile.address = request.POST.get('name'), request.POST.get('address')
        profile.latitude, profile.longitude = float(request.POST.get('latitude')), float(request.POST.get('longitude'))
        profile.save()
        return redirect('pharmacy_list')
    return render(request, 'core/management/pharmacy_edit.html', {'profile': profile})

@login_required
def pharmacy_delete(request, pk):
    if request.user.role != 'GOVERNMENT': return redirect('dashboard_redirect')
    profile = get_object_or_404(PharmacyProfile, pk=pk)
    user = profile.user
    profile.delete()
    user.delete()
    return redirect('pharmacy_list')

@login_required
def antibiotic_list(request):
    if request.user.role != 'GOVERNMENT': return redirect('dashboard_redirect')
    query = request.GET.get('q', '')
    antibiotics = Antibiotic.objects.filter(Q(name__icontains=query) | Q(group__icontains=query)) if query else Antibiotic.objects.all()
    if request.method == 'POST':
        Antibiotic.objects.create(name=request.POST.get('name'), group=request.POST.get('group'), category=request.POST.get('category'))
        return redirect('antibiotic_list')
    return render(request, 'core/management/antibiotic_list.html', {'antibiotics': antibiotics, 'query': query})

@login_required
def antibiotic_edit(request, pk):
    if request.user.role != 'GOVERNMENT': return redirect('dashboard_redirect')
    antibiotic = get_object_or_404(Antibiotic, pk=pk)
    if request.method == 'POST':
        antibiotic.name, antibiotic.group, antibiotic.category = request.POST.get('name'), request.POST.get('group'), request.POST.get('category')
        antibiotic.save()
        return redirect('antibiotic_list')
    return render(request, 'core/management/antibiotic_edit.html', {'antibiotic': antibiotic})

@login_required
def antibiotic_delete(request, pk):
    if request.user.role != 'GOVERNMENT': return redirect('dashboard_redirect')
    get_object_or_404(Antibiotic, pk=pk).delete()
    return redirect('antibiotic_list')
