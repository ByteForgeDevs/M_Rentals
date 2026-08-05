from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.listings.models import Listing

from .forms import LandlordReviewForm, RecordTenancyForm, TenantReviewForm
from .models import Tenancy


@login_required
def tenancy_list(request):
    """Every tenancy the user is part of, on either side, with review prompts."""
    as_tenant = (
        Tenancy.objects.filter(tenant=request.user)
        .select_related("listing", "landlord")
        .prefetch_related("landlord_review", "tenant_review")
    )
    as_landlord = (
        Tenancy.objects.filter(landlord=request.user)
        .select_related("listing", "tenant")
        .prefetch_related("landlord_review", "tenant_review")
    )
    return render(
        request,
        "reviews/tenancies.html",
        {"as_tenant": as_tenant, "as_landlord": as_landlord},
    )


@login_required
def record_tenancy(request, slug: str):
    """Landlord confirms a tenancy, which is what unlocks two-way reviews."""
    listing = get_object_or_404(Listing, slug=slug)
    if listing.landlord_id != request.user.pk:
        raise PermissionDenied("Only the landlord of this listing can record a tenancy.")

    form = RecordTenancyForm(
        request.POST or None, listing=listing, landlord=request.user
    )
    if request.method == "POST" and form.is_valid():
        tenancy = form.save()
        messages.success(
            request,
            f"Tenancy recorded. {tenancy.tenant.full_name} can now review you, and you can "
            "review them.",
        )
        return redirect("reviews:tenancies")

    return render(
        request, "reviews/record_tenancy.html", {"form": form, "listing": listing}
    )


@login_required
@require_POST
def end_tenancy(request, pk: int):
    tenancy = get_object_or_404(Tenancy, pk=pk)
    if tenancy.landlord_id != request.user.pk:
        raise PermissionDenied("Only the landlord can close this tenancy.")

    tenancy.ended_on = timezone.localdate()
    tenancy.status = Tenancy.Status.ENDED
    tenancy.save(update_fields=["ended_on", "status"])
    messages.success(request, "Tenancy closed.")
    return redirect("reviews:tenancies")


@login_required
def review_landlord(request, pk: int):
    tenancy = get_object_or_404(
        Tenancy.objects.select_related("landlord", "listing"), pk=pk
    )
    if tenancy.tenant_id != request.user.pk:
        raise PermissionDenied("Only the tenant on this tenancy can review the landlord.")
    if tenancy.has_landlord_review:
        messages.info(request, "You already reviewed this landlord.")
        return redirect("reviews:tenancies")

    form = LandlordReviewForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        review = form.save(commit=False)
        review.tenancy = tenancy
        review.author = request.user
        review.landlord = tenancy.landlord
        review.save()
        messages.success(request, "Thanks — your review is now on their profile.")
        return redirect("accounts:public_profile", pk=tenancy.landlord_id)

    return render(
        request,
        "reviews/review_form.html",
        {
            "form": form,
            "tenancy": tenancy,
            "subject": tenancy.landlord,
            "heading": f"Review {tenancy.landlord.full_name}",
            "subtitle": "Your honest experience helps the next tenant avoid a bad house.",
        },
    )


@login_required
def review_tenant(request, pk: int):
    tenancy = get_object_or_404(
        Tenancy.objects.select_related("tenant", "listing"), pk=pk
    )
    if tenancy.landlord_id != request.user.pk:
        raise PermissionDenied("Only the landlord on this tenancy can review the tenant.")
    if tenancy.has_tenant_review:
        messages.info(request, "You already reviewed this tenant.")
        return redirect("reviews:tenancies")

    form = TenantReviewForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        review = form.save(commit=False)
        review.tenancy = tenancy
        review.author = request.user
        review.tenant = tenancy.tenant
        review.save()
        messages.success(request, "Review saved. Future landlords will see it.")
        return redirect("accounts:public_profile", pk=tenancy.tenant_id)

    return render(
        request,
        "reviews/review_form.html",
        {
            "form": form,
            "tenancy": tenancy,
            "subject": tenancy.tenant,
            "heading": f"Review {tenancy.tenant.full_name}",
            "subtitle": "Payment reliability and care of the property.",
        },
    )
