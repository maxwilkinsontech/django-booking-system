import json

from sites.models import Site


def get_business_hours(site):
    business_hours = [
        {
            'startTime': getattr(site, f'{day}_opening_hour').strftime("%H:%M"),
            'endTime': getattr(site, f'{day}_closing_hour').strftime("%H:%M"),
            'daysOfWeek': [(index + 1) % 7],  # Sunday=0
        }
        for index, day in enumerate(Site.DAY_PREFIXES)
    ]
    return business_hours


def get_resources(sites):
    """Create dict containing table info for calendar resources."""
    resources = []

    for site in sites:
        # Create site business hours.
        business_hours = get_business_hours(site)

        tables = site.tables.order_by('table_name')
        for table in tables:
            resources.append(
                {
                    'id': table.id,
                    'title': table.__str__(),
                    'siteId': site.site_name,
                    'businessHours': business_hours,
                }
            )

    return json.dumps(resources)
