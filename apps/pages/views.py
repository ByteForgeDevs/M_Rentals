from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count
from django.shortcuts import render

from apps.listings.models import KENYAN_COUNTIES, Listing, SavedListing
from apps.reviews.models import LandlordReview, Tenancy


def home(request):
    listings = Listing.objects.published().with_cover()
    featured = listings.from_verified_landlords()[:6]
    if not featured:
        featured = listings[:6]

    areas = (
        Listing.objects.published()
        .values("area", "county")
        .annotate(count=Count("id"))
        .order_by("-count")[:8]
    )

    return render(
        request,
        "pages/home.html",
        {
            "featured": featured,
            "areas": areas,
            "counties": KENYAN_COUNTIES[:8],
            "stats": {
                "listings": listings.count(),
                "verified_landlords": listings.from_verified_landlords()
                .values("landlord")
                .distinct()
                .count(),
                "reviews": LandlordReview.objects.count(),
            },
        },
    )


def how_it_works(request):
    return render(request, "pages/how_it_works.html")


@login_required
def dashboard(request):
    user = request.user
    context = {
        "pending_reviews_as_tenant": (
            Tenancy.objects.filter(tenant=user, landlord_review__isnull=True)
            .select_related("listing", "landlord")
        ),
        "pending_reviews_as_landlord": (
            Tenancy.objects.filter(landlord=user, tenant_review__isnull=True)
            .select_related("listing", "tenant")
        ),
    }

    if user.is_landlord:
        listings = (
            Listing.objects.filter(landlord=user).with_cover().order_by("-updated_at")
        )
        context |= {
            "listings": listings,
            "listing_counts": {
                "total": listings.count(),
                "published": listings.filter(status=Listing.Status.PUBLISHED).count(),
                "draft": listings.filter(status=Listing.Status.DRAFT).count(),
                "rented": listings.filter(status=Listing.Status.RENTED).count(),
            },
            "total_views": sum(listing.view_count for listing in listings),
            "rating": LandlordReview.objects.filter(landlord=user).aggregate(
                avg=Avg("overall_rating"), count=Count("id")
            ),
            "verification": getattr(user, "landlord_verification", None),
        }
    else:
        context |= {
            "saved": (
                SavedListing.objects.filter(user=user)
                .select_related("listing__landlord")
                .prefetch_related("listing__photos")[:6]
            ),
            "recommended": (
                Listing.objects.published()
                .from_verified_landlords()
                .with_cover()
                .filter(area__icontains=user.preferred_area)[:4]
                if user.preferred_area
                else Listing.objects.published().from_verified_landlords().with_cover()[:4]
            ),
            "tenancies": Tenancy.objects.filter(tenant=user).select_related("listing"),
            "verification": getattr(user, "tenant_verification", None),
        }

    return render(request, "pages/dashboard.html", context)
