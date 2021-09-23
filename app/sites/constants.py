import datetime

default_opening_time = datetime.time(12, 0)
default_closing_time = datetime.time(23, 0)

default_booking_created_subject = 'Your booking has been confirmed'
default_booking_updated_subject = 'Your booking has been updated'
default_booking_cancelled_subject = 'Your booking has been cancelled'
default_booking_reminder_subject = 'Your upcoming booking'
default_booking_admin_created_subject = 'New booking'

default_booking_created_content = '''
Hi {{ client_name }},

Your booking request has been <strong>confirmed</strong>. We look forward to seeing you soon.

<strong>Your booking:</strong>
Name: {{ client_name }}
Email: {{ client_email }}
Party: {{ party }}
Date: {{ date }} [{{ duration }}]
Location: {{ site_name }}
Reference: {{ reference }}
'''
default_booking_updated_content = '''
Hi {{ client_name }},

Your booking has been <strong>updated</strong>. We look forward to seeing you soon.

<strong>Your updated booking:</strong>
Name: {{ client_name }}
Email: {{ client_email }}
Party: {{ party }}
Date: {{ date }} [{{ duration }}]
Location: {{ site_name }}
Reference: {{ reference }}
'''
default_booking_cancelled_content = '''
Hi {{ client_name }},

Sorry, we could not accommodate your booking request.

<strong>Your cancelled booking:</strong>
Name: {{ client_name }}
Email: {{ client_email }}
Party: {{ party }}
Date: {{ date }} [{{ duration }}]
Location: {{ site_name }}
Reference: {{ reference }}
'''
default_booking_reminder_content = '''
Hi {{ client_name }},

We look forward to seeing you soon.

<strong>Your booking:</strong>
Name: {{ client_name }}
Email: {{ client_email }}
Party: {{ party }}
Date: {{ date }} [{{ duration }}]
Location: {{ site_name }}
Reference: {{ reference }}
'''
default_booking_admin_created_content = '''
<strong>A new booking has been created:</strong>
Name: {{ client_name }}
Email: {{ client_email }}
Party: {{ party }}
Date: {{ date }} [{{ duration }}]
Location: {{ site_name }}
Reference: {{ reference }}
'''
