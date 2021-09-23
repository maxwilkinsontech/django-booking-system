from django.template import Context, Template
from django.utils.html import strip_tags

from post_office import mail


def get_email_message(booking, message_template, html=True):
    """
    Return a dictionary of variables available in the email templates.
    """
    context = {
        'client_name': booking.client.client_name,
        'client_email': booking.client.client_email,
        'party': booking.party,
        'date': booking.booking_date,
        'duration': f'{booking.duration} mins',
        'site_name': booking.site.site_name,
        'reference': booking.reference,
    }

    # Remove html tags for plain text email.
    if not html:
        message_template = strip_tags(message_template)
    else:
        message_template = message_template.replace('\n', '<br>')

    t = Template(message_template)
    c = Context(context)
    return t.render(c)


def send_booking_created_email(booking):
    """
    Send an email to the Client of the given Booking when it is created.
    """
    client = booking.client
    site = booking.site

    subject = site.client_email_booking_created_subject
    message = get_email_message(booking, site.client_email_booking_created_content, html=False)
    html_message = get_email_message(booking, site.client_email_booking_created_content)

    mail.send(
        client.client_email,
        subject=subject,
        message=message,
        html_message=html_message,
    )


def send_booking_updated_email(booking):
    """
    Send an email to the Client of the given Booking when it is updated.
    """
    client = booking.client
    site = booking.site

    subject = site.client_email_booking_updated_subject
    message = get_email_message(booking, site.client_email_booking_updated_content, html=False)
    html_message = get_email_message(booking, site.client_email_booking_updated_content)

    mail.send(
        client.client_email,
        subject=subject,
        message=message,
        html_message=html_message,
    )


def send_booking_cancelled_email(booking):
    """
    Send an email to the Client of the given Booking when it is cancelled.
    """
    client = booking.client
    site = booking.site

    subject = site.client_email_booking_cancelled_subject
    message = get_email_message(booking, site.client_email_booking_cancelled_content, html=False)
    html_message = get_email_message(booking, site.client_email_booking_cancelled_content)

    mail.send(
        client.client_email,
        subject=subject,
        message=message,
        html_message=html_message,
    )


def send_booking_notification_email(booking):
    """
    Send an email to the Client of the given Booking to notify them.
    """
    client = booking.client
    site = booking.site

    subject = site.client_email_booking_reminder_subject
    message = get_email_message(booking, site.client_email_booking_reminder_content, html=False)
    html_message = get_email_message(booking, site.client_email_booking_reminder_content)

    mail.send(
        client.client_email,
        subject=subject,
        message=message,
        html_message=html_message,
    )


def send_client_email(booking, subject, content):
    """
    Send an email to the Client of a Booking.
    """
    client = booking.client
    site = booking.site

    message = get_email_message(booking, content, html=False)
    html_message = get_email_message(booking, content)

    mail.send(
        client.client_email,
        subject=subject,
        message=message,
        html_message=html_message,
    )


def send_admin_booking_created_email(booking):
    """
    Send an email to an admin notifying of a Booking.
    """
    site = booking.site

    if site.send_admin_notification_email:
        subject = site.admin_email_booking_created_subject
        message = get_email_message(booking, site.admin_email_booking_created_content, html=False)
        html_message = get_email_message(booking, site.admin_email_booking_created_content)

        mail.send(
            site.admin_notification_email,
            subject=subject,
            message=message,
            html_message=html_message,
        )
