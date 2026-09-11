from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from ..decorators import role_required
from ..forms import AntibioticForm, PharmacyCreateForm, PharmacyProfileForm
from ..models import Antibiotic, PharmacyProfile


@login_required
@role_required('GOVERNMENT')
def pharmacy_list(request):
    form = PharmacyCreateForm()
    if request.method == 'POST' and request.POST.get('action') == 'add':
        form = PharmacyCreateForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('pharmacy_list')
    return render(request, 'core/management/pharmacy_list.html', {
        'pharmacies': PharmacyProfile.objects.select_related('user').annotate(sales_count=Count('sales')),
        'form': form
    })


@login_required
@role_required('GOVERNMENT')
def pharmacy_edit(request, pk):
    profile = get_object_or_404(PharmacyProfile, pk=pk)
    form = PharmacyProfileForm(instance=profile)
    if request.method == 'POST':
        form = PharmacyProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('pharmacy_list')
    return render(request, 'core/management/pharmacy_edit.html', {'profile': profile, 'form': form})


@login_required
@role_required('GOVERNMENT')
@require_POST
def pharmacy_delete(request, pk):
    profile = get_object_or_404(PharmacyProfile, pk=pk)
    user = profile.user
    profile.delete()
    user.delete()
    return redirect('pharmacy_list')


@login_required
@role_required('GOVERNMENT')
def antibiotic_list(request):
    query = request.GET.get('q', '')
    antibiotics = Antibiotic.objects.filter(Q(name__icontains=query) | Q(group__icontains=query)) if query else Antibiotic.objects.all()
    form = AntibioticForm()
    if request.method == 'POST':
        form = AntibioticForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('antibiotic_list')
    return render(request, 'core/management/antibiotic_list.html', {
        'antibiotics': antibiotics, 'query': query, 'form': form
    })


@login_required
@role_required('GOVERNMENT')
def antibiotic_edit(request, pk):
    antibiotic = get_object_or_404(Antibiotic, pk=pk)
    form = AntibioticForm(instance=antibiotic)
    if request.method == 'POST':
        form = AntibioticForm(request.POST, instance=antibiotic)
        if form.is_valid():
            form.save()
            return redirect('antibiotic_list')
    return render(request, 'core/management/antibiotic_edit.html', {'antibiotic': antibiotic, 'form': form})


@login_required
@role_required('GOVERNMENT')
@require_POST
def antibiotic_delete(request, pk):
    get_object_or_404(Antibiotic, pk=pk).delete()
    return redirect('antibiotic_list')
