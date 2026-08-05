from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Avg, Count, F
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.reviews.models import LandlordReview

from .forms import ListingForm, ListingPhotoFormSet, ListingSearchForm
from .models import Listing, SavedListing
from .selectors import active_filter_summary, search_listings

PAGE_SIZE = 12


def search(request):
    """Browse and filter published listings. HTMX swaps just the results grid."""
    form = ListingSearchForm(request.GET or None)
    filters = form.cleaned_data if form.is_valid() else {}

    queryset = Listing.objects.published().with_cover().with_landlord_rating()
    results = search_listings(queryset, filters)

    paginator = Paginator(results, PAGE_SIZE)
    page = paginator.get_page(request.GET.get("page"))

    querystring = request.GET.copy()
    querystring.pop("page", None)

    context = {
        "form": form,
        "page_obj": page,
        "paginator": paginator,
        "total_count": paginator.count,
        "filter_chips": active_filter_summary(filters),
        "querystring": querystring.urlencode(),
    }
    if request.htmx:
        return render(request, "listings/partials/results.html", context)
    return render(request, "listings/search.html", context)


def detail(request, slug: str):
    listing = get_object_or_404(
        Listing.objects.visible_to(request.user).select_related("landlord").prefetch_related("photos"),
        slug=slug,
    )

    if listing.landlord_id != request.user.pk:
        Listing.objects.filter(pk=listing.pk).update(view_count=F("view_count") + 1)

    landlord_stats = LandlordReview.objects.filter(landlord=listing.landlord).aggregate(
        avg=Avg("overall_rating"), count=Count("id")
    )
    is_saved = (
        request.user.is_authenticated
        and SavedListing.objects.filter(user=request.user, listing=listing).exists()
    )

    context = {
        "listing": listing,
        "photos_by_category": _group_photos(listing),
        "landlord_rating": landlord_stats["avg"],
        "landlord_review_count": landlord_stats["count"],
        "recent_reviews": (
            LandlordReview.objects.filter(landlord=listing.landlord)
            .select_related("author")
            .order_by("-created_at")[:3]
        ),
        "is_saved": is_saved,
        "is_owner": listing.landlord_id == request.user.pk,
        "similar": (
            Listing.objects.published()
            .filter(area__iexact=listing.area)
            .exclude(pk=listing.pk)
            .with_cover()[:3]
        ),
    }
    return render(request, "listings/detail.html", context)


def _group_photos(listing: Listing) -> list[tuple[str, list]]:
    grouped: dict[str, list] = {}
    for photo in listing.photos.all():
        grouped.setdefault(photo.get_category_display(), []).append(photo)
    return list(grouped.items())


@login_required
def create(request):
    if not request.user.is_landlord:
        messages.warning(
            request, "Switch to a landlord account to post a house."
        )
        return redirect("accounts:profile")

    listing = Listing(landlord=request.user)
    form = ListingForm(request.POST or None, instance=listing)
    formset = ListingPhotoFormSet(
        request.POST or None, request.FILES or None, instance=listing
    )

    if request.method == "POST" and form.is_valid() and formset.is_valid():
        with transaction.atomic():
            listing = form.save(commit=False)
            listing.landlord = request.user
            listing.status = Listing.Status.DRAFT
            listing.save()
            formset.instance = listing
            formset.save()
        messages.success(request, "Listing saved. Review it and publish when ready.")
        return redirect("listings:manage", slug=listing.slug)

    return render(
        request,
        "listings/form.html",
        {"form": form, "formset": formset, "is_create": True},
    )


@login_required
def edit(request, slug: str):
    listing = _get_own_listing(request, slug)
    form = ListingForm(request.POST or None, instance=listing)
    formset = ListingPhotoFormSet(
        request.POST or None, request.FILES or None, instance=listing
    )

    if request.method == "POST" and form.is_valid() and formset.is_valid():
        with transaction.atomic():
            form.save()
            formset.save()
        messages.success(request, "Listing updated.")
        return redirect("listings:manage", slug=listing.slug)

    return render(
        request,
        "listings/form.html",
        {"form": form, "formset": formset, "listing": listing, "is_create": False},
    )


@login_required
def manage(request, slug: str):
    """Landlord-side view of one listing: readiness, stats, tenancy actions."""
    listing = _get_own_listing(request, slug)
    return render(
        request,
        "listings/manage.html",
        {
            "listing": listing,
            "blockers": listing.publication_blockers(),
            "tenancies": listing.tenancies.select_related("tenant").order_by("-started_on"),
        },
    )


@login_required
@require_POST
def publish(request, slug: str):
    listing = _get_own_listing(request, slug)
    blockers = listing.publication_blockers()
    if blockers:
        for blocker in blockers:
            messages.error(request, blocker)
        return redirect("listings:manage", slug=listing.slug)

    listing.status = Listing.Status.PUBLISHED
    listing.save(update_fields=["status", "published_at", "updated_at"])
    messages.success(request, "Listing is live. Tenants can now find it.")
    return redirect(listing.get_absolute_url())


@login_required
@require_POST
def unpublish(request, slug: str):
    listing = _get_own_listing(request, slug)
    listing.status = Listing.Status.ARCHIVED
    listing.save(update_fields=["status", "updated_at"])
    messages.info(request, "Listing removed from search results.")
    return redirect("listings:manage", slug=listing.slug)


@login_required
@require_POST
def mark_rented(request, slug: str):
    listing = _get_own_listing(request, slug)
    listing.status = Listing.Status.RENTED
    listing.save(update_fields=["status", "updated_at"])
    messages.success(request, "Marked as rented. Record the tenancy to unlock reviews.")
    return redirect("reviews:record_tenancy", slug=listing.slug)


@login_required
@require_POST
def toggle_save(request, slug: str):
    listing = get_object_or_404(Listing.objects.published(), slug=slug)
    saved = SavedListing.objects.filter(user=request.user, listing=listing)
    if saved.exists():
        saved.delete()
        is_saved = False
    else:
        SavedListing.objects.create(user=request.user, listing=listing)
        is_saved = True

    if request.htmx:
        return render(
            request,
            "listings/partials/save_button.html",
            {"listing": listing, "is_saved": is_saved},
        )
    return redirect(listing.get_absolute_url())


@login_required
def saved(request):
    entries = (
        SavedListing.objects.filter(user=request.user)
        .select_related("listing__landlord")
        .prefetch_related("listing__photos")
    )
    return render(request, "listings/saved.html", {"entries": entries})


def _get_own_listing(request, slug: str) -> Listing:
    listing = get_object_or_404(Listing, slug=slug)
    if listing.landlord_id != request.user.pk and not request.user.is_staff:
        raise PermissionDenied("You can only manage your own listings.")
    return listing
