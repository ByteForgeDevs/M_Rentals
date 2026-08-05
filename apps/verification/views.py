from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import LandlordVerificationForm, TenantVerificationForm
from .models import LandlordVerification, TenantVerification, VerificationStatus


@login_required
def status(request):
    return render(
        request,
        "verification/status.html",
        {
            "landlord_verification": getattr(request.user, "landlord_verification", None),
            "tenant_verification": getattr(request.user, "tenant_verification", None),
        },
    )


@login_required
def landlord_verification(request):
    return _handle_submission(
        request,
        model=LandlordVerification,
        form_class=LandlordVerificationForm,
        relation="landlord_verification",
        template="verification/landlord_form.html",
    )


@login_required
def tenant_verification(request):
    return _handle_submission(
        request,
        model=TenantVerification,
        form_class=TenantVerificationForm,
        relation="tenant_verification",
        template="verification/tenant_form.html",
    )


def _handle_submission(request, *, model, form_class, relation, template):
    """Create or resubmit a verification request for review."""
    instance = getattr(request.user, relation, None)

    if instance and instance.is_approved:
        messages.info(request, "You are already verified.")
        return redirect("verification:status")

    form = form_class(request.POST or None, request.FILES or None, instance=instance)
    if request.method == "POST" and form.is_valid():
        verification = form.save(commit=False)
        verification.user = request.user
        # A resubmission after rejection goes back into the queue.
        verification.status = VerificationStatus.PENDING
        verification.reviewed_by = None
        verification.reviewed_at = None
        verification.save()
        messages.success(
            request,
            "Documents submitted. Our team reviews verifications within 48 hours.",
        )
        return redirect("verification:status")

    return render(request, template, {"form": form, "verification": instance})
