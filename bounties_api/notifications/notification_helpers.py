from django.template.loader import render_to_string
from notifications.models import Notification, DashboardNotification
from bounties.ses_client import send_email
from bounties.utils import bounty_url_for, profile_url_for
from django.db import transaction


@transaction.atomic
def create_notification(
        bounty,
        uid,
        notification_name,
        user,
        notification_created,
        string_data,
        subject,
        is_activity=True,
        string_data_email=None,
        email_button_string='View in App',
        url_query=''):
    bounty_url = bounty_url_for(bounty.bounty_id, bounty.platform) + url_query
    notification, created = Notification.objects.get_or_create(
        uid=str(uid),
        defaults={
            'notification_name': notification_name,
            'user': user,
            'notification_created': notification_created,
            'dashboard': True,
        },
    )
    # this is atomic, so this is a good indicator
    if not created:
        return
    DashboardNotification.objects.create(
        notification=notification,
        string_data=string_data,
        is_activity=is_activity,
        data={'link': bounty_url},
    )
    bounty_user = bounty.user
    username = 'bounty hunter'
    if bounty_user and bounty_user.name:
        username = bounty_user.name
    email_html = render_to_string(
        'base_notification.html',
        context={
            'link': bounty_url,
            'username': username,
            'message_string': string_data_email or string_data,
            'button_text': email_button_string})
    email_txt = 'Hello {}! \n {}'.format(
        username, string_data_email or string_data, )
    email_settings = user.settings.emails
    activity_emails = email_settings['activity']
    if is_activity and not activity_emails:
        return

    if not is_activity and notification_name not in user.settings.accepted_email_settings():
        return

    if not notification.email_sent:
        send_email(user.email, subject, email_txt, email_html)
        notification.email_sent = True
        notification.save()


@transaction.atomic
def create_other_notification(uid, notification_name, user, notification_created, string_data, subject, is_activity=True, string_data_email=None, email_button_string='View in App', url=''):
    notification, created = Notification.objects.get_or_create(
        uid=str(uid),
        defaults = {
            'notification_name': notification_name,
            'user': user,
            'notification_created': notification_created,
            'dashboard': True,
        },
    )
    # this is atomic, so this is a good indicator
    if not created:
        return
    DashboardNotification.objects.create(
        notification=notification,
        string_data=string_data,
        is_activity=is_activity,
        data={'link': profile_url_for(user.public_address)},
    )

    username = 'bounty hunter'
    if user and user.name:
        username = user.name
    email_html = render_to_string('base_notification.html', context={'link': profile_url_for(user.public_address), 'username': username, 'message_string': string_data_email or string_data, 'button_text': email_button_string})
    email_txt = 'Hello {}! \n {}'.format(username, string_data_email or string_data, )
    email_settings = user.settings.emails
    activity_emails = email_settings['activity']
    if is_activity and not activity_emails:
        return

    if not is_activity and notification_name not in user.settings.accepted_email_settings():
        return

    if not notification.email_sent:
        send_email(user.email, subject, email_txt, email_html)
        notification.email_sent = True
        notification.save()
