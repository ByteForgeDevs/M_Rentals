from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.db.models import Avg, Count
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST

from apps.listings.models import Listing
from apps.reviews.models import LandlordReview, TenantReview

from .forms import LoginForm, ProfileForm, SignUpForm
from .models import User


class MrentalsLoginView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = LoginForm
    redirect_authenticated_user = True

    def form_valid(self, form):
        messages.success(self.request, f"Welcome back, {form.get_user().full_name}.")
        return super().form_valid(form)


def signup(request):
    if request.user.is_authenticated:
        return redirect("pages:dashboard")

    form = SignUpForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user, backend="apps.accounts.backends.EmailOrPhoneBackend")
        if user.is_landlord:
            messages.success(
                request,
                "Account created. Verify your identity next so your listings can go live.",
            )
            return redirect("verification:landlord")
        messages.success(request, "Account created. Start searching for a place.")
        return redirect("listings:search")

    return render(request, "accounts/signup.html", {"form": form})


@require_POST
def logout_view(request):
    logout(request)
    messages.info(request, "You have been signed out.")
    return redirect("pages:home")


@login_required
def profile(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated.")
        return redirect("accounts:profile")
    return render(request, "accounts/profile.html", {"form": form})


@login_required
@require_POST
def switch_role(request):
    user = request.user
    user.role = User.Role.LANDLORD if user.is_tenant else User.Role.TENANT
    user.save(update_fields=["role"])
    messages.success(request, f"You are now using Mrentals as a {user.get_role_display()}.")
    return redirect(request.POST.get("next") or reverse("pages:dashboard"))


def public_profile(request, pk: int):
    """Public trust page: who this person is and what the other side says."""
    person = get_object_or_404(User, pk=pk, is_active=True)

    landlord_reviews = (
        LandlordReview.objects.filter(landlord=person)
        .select_related("author", "tenancy__listing")
        .order_by("-created_at")
    )
    tenant_reviews = (
        TenantReview.objects.filter(tenant=person)
        .select_related("author", "tenancy__listing")
        .order_by("-created_at")
    )
    stats = landlord_reviews.aggregate(avg=Avg("overall_rating"), count=Count("id"))
    tenant_stats = tenant_reviews.aggregate(avg=Avg("overall_rating"), count=Count("id"))

    context = {
        "person": person,
        "landlord_reviews": landlord_reviews[:20],
        "tenant_reviews": tenant_reviews[:20],
        "landlord_rating": stats["avg"],
        "landlord_review_count": stats["count"],
        "tenant_rating": tenant_stats["avg"],
        "tenant_review_count": tenant_stats["count"],
        "active_listings": (
            Listing.objects.published()
            .filter(landlord=person)
            .with_cover()
            .order_by("-published_at")[:6]
        ),
    }
    return render(request, "accounts/public_profile.html", context)
