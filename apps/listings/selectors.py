"""Query helpers for listing search and filtering."""

from django.db.models import Avg, Count, Q, QuerySet

from .models import Listing


def search_listings(queryset: QuerySet[Listing], filters: dict) -> QuerySet[Listing]:
    """Apply the search form's cleaned data to a listing queryset."""
    qs = queryset

    query = (filters.get("q") or "").strip()
    if query:
        qs = qs.filter(
            Q(title__icontains=query)
            | Q(area__icontains=query)
            | Q(county__icontains=query)
            | Q(nearest_landmark__icontains=query)
            | Q(landmark_description__icontains=query)
            | Q(description__icontains=query)
        )

    if county := filters.get("county"):
        qs = qs.filter(county=county)

    if (min_price := filters.get("min_price")) is not None:
        qs = qs.filter(rent_amount__gte=min_price)

    if (max_price := filters.get("max_price")) is not None:
        qs = qs.filter(rent_amount__lte=max_price)

    bedrooms = filters.get("bedrooms")
    if bedrooms not in (None, ""):
        bedrooms = int(bedrooms)
        # "3" in the filter means "3 or more".
        qs = qs.filter(bedrooms__gte=3) if bedrooms >= 3 else qs.filter(bedrooms=bedrooms)

    if property_type := filters.get("property_type"):
        qs = qs.filter(property_type=property_type)

    if filters.get("verified_only"):
        qs = qs.filter(landlord__landlord_verification__status="approved")

    if filters.get("has_video"):
        qs = qs.exclude(walkthrough_video_url="")

    return _apply_sort(qs, filters.get("sort") or "recent")


def _apply_sort(qs: QuerySet[Listing], sort: str) -> QuerySet[Listing]:
    if sort == "price_asc":
        return qs.order_by("rent_amount", "-published_at")
    if sort == "price_desc":
        return qs.order_by("-rent_amount", "-published_at")
    if sort == "rating":
        return qs.annotate(
            _rating=Avg("landlord__reviews_received__overall_rating"),
            _review_count=Count("landlord__reviews_received", distinct=True),
        ).order_by("-_rating", "-_review_count", "-published_at")
    return qs.order_by("-published_at", "-created_at")


def active_filter_summary(filters: dict) -> list[dict]:
    """Chips describing the filters currently applied.

    Each chip carries the query parameter it came from so the template can
    render it as a one tap "remove this filter" control.
    """
    chips: list[dict] = []

    def add(param: str, label: str) -> None:
        chips.append({"param": param, "label": label})

    if q := (filters.get("q") or "").strip():
        add("q", f'"{q}"')
    if county := filters.get("county"):
        add("county", county)
    if (mn := filters.get("min_price")) is not None:
        add("min_price", f"from KES {mn:,}")
    if (mx := filters.get("max_price")) is not None:
        add("max_price", f"up to KES {mx:,}")
    bedrooms = filters.get("bedrooms")
    if bedrooms not in (None, ""):
        bedrooms = int(bedrooms)
        add(
            "bedrooms",
            "Bedsitter"
            if bedrooms == 0
            else f"{bedrooms}+ bedrooms"
            if bedrooms >= 3
            else f"{bedrooms} bedroom",
        )
    if property_type := filters.get("property_type"):
        add("property_type", dict(Listing.PropertyType.choices).get(property_type, property_type))
    if filters.get("verified_only"):
        add("verified_only", "Verified landlords")
    if filters.get("has_video"):
        add("has_video", "With video")
    return chips
