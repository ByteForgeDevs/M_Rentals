"""Inline SVG icons.

Icons ship as inline SVG rather than a font or a sprite file: there is no extra
request to make, they inherit ``currentColor``, and they survive with the page
when the network is slow, which matters for the mobile connections this
audience actually uses.
"""

from django import template
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()

# Paths use a 24x24 viewBox and are stroked, not filled, so one set works at
# every size. Keep them geometric to match the mark.
ICONS = {
    "shield-check": '<path d="M12 3 4.5 6v5.4c0 4.3 3.1 8.3 7.5 9.6 4.4-1.3 7.5-5.3 7.5-9.6V6L12 3Z"/><path d="m9 12 2.2 2.2L15.5 10"/>',
    "map-pin": '<path d="M20 10.5c0 5.2-6.2 10.4-7.4 11.3a1 1 0 0 1-1.2 0C10.2 20.9 4 15.7 4 10.5a8 8 0 1 1 16 0Z"/><circle cx="12" cy="10.3" r="2.8"/>',
    "camera": '<path d="M3 8.5A2.5 2.5 0 0 1 5.5 6h1.7a1 1 0 0 0 .83-.44l.94-1.4A1 1 0 0 1 9.8 3.7h4.4a1 1 0 0 1 .83.45l.94 1.4a1 1 0 0 0 .83.45h1.7A2.5 2.5 0 0 1 21 8.5v8A2.5 2.5 0 0 1 18.5 19h-13A2.5 2.5 0 0 1 3 16.5Z"/><circle cx="12" cy="12.2" r="3.4"/>',
    "star": '<path d="m12 3.6 2.6 5.3 5.9.85-4.25 4.14 1 5.86L12 16.98l-5.25 2.77 1-5.86L3.5 9.75l5.9-.85L12 3.6Z"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="m16 16 4.5 4.5"/>',
    "arrow-right": '<path d="M4.5 12h15"/><path d="m13 5.5 6.5 6.5-6.5 6.5"/>',
    "arrow-left": '<path d="M19.5 12h-15"/><path d="M11 5.5 4.5 12 11 18.5"/>',
    "check": '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    "close": '<path d="M6 6l12 12M18 6 6 18"/>',
    "menu": '<path d="M4 7h16M4 12h16M4 17h16"/>',
    "phone": '<path d="M7.3 3.8h-2A1.8 1.8 0 0 0 3.5 5.7C3.5 13.6 10.4 20.5 18.3 20.5a1.8 1.8 0 0 0 1.9-1.8v-2a1 1 0 0 0-.78-.98l-3.4-.75a1 1 0 0 0-1.02.4l-1 1.4a12.6 12.6 0 0 1-5.3-5.3l1.4-1a1 1 0 0 0 .4-1.02l-.75-3.4a1 1 0 0 0-.98-.78Z"/>',
    "mail": '<rect x="3" y="5.5" width="18" height="13" rx="2.2"/><path d="m3.8 7 7.5 5.3a1.2 1.2 0 0 0 1.4 0L20.2 7"/>',
    "heart": '<path d="M12 20.2S3.8 15.4 3.8 9.8a4.3 4.3 0 0 1 8.2-1.8 4.3 4.3 0 0 1 8.2 1.8c0 5.6-8.2 10.4-8.2 10.4Z"/>',
    "bolt": '<path d="M13.2 3 5.5 13.4h5.4L10.2 21l7.7-10.4h-5.4L13.2 3Z"/>',
    "droplet": '<path d="M12 3.4s6 6 6 9.9a6 6 0 0 1-12 0c0-3.9 6-9.9 6-9.9Z"/>',
    "key": '<circle cx="8.5" cy="13.5" r="4"/><path d="m11.8 11 8-8"/><path d="m17 5.8 2 2"/><path d="m14.5 8.3 2 2"/>',
    "users": '<circle cx="9.5" cy="8.5" r="3.3"/><path d="M3.8 19.2a5.9 5.9 0 0 1 11.4 0"/><path d="M16 5.6a3.3 3.3 0 0 1 0 6.4"/><path d="M17.6 14.2a5.9 5.9 0 0 1 2.8 4.4"/>',
    "clock": '<circle cx="12" cy="12" r="8.4"/><path d="M12 7.4V12l3 1.8"/>',
    "home": '<path d="M4 10.6 12 4l8 6.6"/><path d="M6 9.7v9.4h12V9.7"/><path d="M10 19.1v-5h4v5"/>',
    "filter": '<path d="M4 6h16"/><path d="M7 12h10"/><path d="M10 18h4"/>',
    "expand": '<path d="M9 4H4v5"/><path d="M15 20h5v-5"/><path d="m4 4 6 6"/><path d="m20 20-6-6"/>',
    "info": '<circle cx="12" cy="12" r="8.4"/><path d="M12 11v5.2"/><path d="M12 7.9h.01"/>',
    "alert": '<path d="M12 4.2 2.9 19.4h18.2L12 4.2Z"/><path d="M12 10v4"/><path d="M12 17.2h.01"/>',
    "video": '<rect x="3" y="6" width="12.5" height="12" rx="2.2"/><path d="m15.5 10.8 5.5-3v8.4l-5.5-3Z"/>',
    "sparkle": '<path d="M12 3.5 13.7 9l5.5 1.7-5.5 1.7L12 18l-1.7-5.6L4.8 10.7 10.3 9 12 3.5Z"/>',
    "sun": '<circle cx="12" cy="12" r="4.2"/><path d="M12 2.8v2.1M12 19.1v2.1M4.4 4.4l1.5 1.5M18.1 18.1l1.5 1.5M2.8 12h2.1M19.1 12h2.1M4.4 19.6l1.5-1.5M18.1 5.9l1.5-1.5"/>',
    "moon": '<path d="M20.5 14.2A8.4 8.4 0 0 1 9.8 3.5a8.4 8.4 0 1 0 10.7 10.7Z"/>',
    "chevron-down": '<path d="m6 9.5 6 6 6-6"/>',
}


@register.simple_tag
def icon(name, css_class="h-5 w-5", stroke_width="1.7"):
    """Render an inline SVG icon.

    Icons are decorative by default. Where an icon carries the only meaning in
    its context, the surrounding element supplies the accessible name.
    """
    body = ICONS.get(name)
    if body is None:
        return ""
    return format_html(
        '<svg class="{}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="{}" stroke-linecap="round" stroke-linejoin="round" '
        'aria-hidden="true" focusable="false">{}</svg>',
        css_class,
        stroke_width,
        mark_safe(body),
    )


@register.simple_tag(takes_context=True)
def query_without(context, *params):
    """Return the current querystring with ``params`` removed.

    Used by the removable filter chips so each chip can link back to the same
    search minus the one filter it represents.
    """
    request = context.get("request")
    if request is None:
        return ""
    query = request.GET.copy()
    for param in params:
        query.pop(param, None)
    query.pop("page", None)
    encoded = query.urlencode()
    return f"?{encoded}" if encoded else "?"


# Photographic backdrops. Each entry names a file stem in
# ``static/img/backdrops`` and the focal point to hold on to when the band is
# cropped, so the subject survives on a narrow phone.
BACKDROPS = {
    "estate-day": "object-center",
    "estate-night": "object-bottom",
    "balconies-warm": "object-center",
    "keys-door": "object-center",
    "facade-grid": "object-center",
}


@register.simple_tag
def backdrop(name, css_class="", *, loading="lazy"):
    """Render a decorative photographic background for a section.

    The image is purely presentational, so it is hidden from assistive
    technology and carries an empty alt. WebP is served first with a JPEG
    fallback, because a slice of this audience browses through proxies that
    never learned WebP. The parent element must be positioned, and the caller
    is responsible for laying a scrim over the top so text keeps its contrast.
    """
    position = BACKDROPS.get(name)
    if position is None:
        return ""

    stem = f"img/backdrops/{name}"
    small_webp, large_webp = static(f"{stem}-sm.webp"), static(f"{stem}.webp")
    small_jpg, large_jpg = static(f"{stem}-sm.jpg"), static(f"{stem}.jpg")

    return format_html(
        '<picture aria-hidden="true">'
        '<source type="image/webp" srcset="{} 560w, {} 960w" sizes="100vw">'
        '<source type="image/jpeg" srcset="{} 560w, {} 960w" sizes="100vw">'
        '<img src="{}" alt="" loading="{}" decoding="async" fetchpriority="{}" '
        'class="pointer-events-none absolute inset-0 h-full w-full object-cover {} {}">'
        "</picture>",
        small_webp,
        large_webp,
        small_jpg,
        large_jpg,
        large_jpg,
        loading,
        "high" if loading == "eager" else "auto",
        position,
        css_class,
    )
