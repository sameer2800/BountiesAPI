from datetime import datetime
from functools import reduce

import arrow
from django.core.management import BaseCommand
from analytics.models import BountiesTimeline
from std_bounties.constants import EXPIRED_STAGE, DEAD_STAGE, COMPLETED_STAGE, ACTIVE_STAGE, DRAFT_STAGE
from std_bounties.models import BountyState, Fulfillment, Bounty


def diff_time(since, until):
    return until - since


def diff_days(last_update, now=datetime.utcnow()):
    return (diff_time(now, last_update)).days


def day_bounds(day):
    utc_day = arrow.get(day).to('utc')
    floor = utc_day.floor('day')
    ceil = utc_day.ceil('day')

    return floor.datetime, ceil.datetime


def range_days(since, until):
    return arrow.Arrow.range('day', since, until)


def get_date(time_frame):
    return time_frame.last().change_date


def add_on(stage):
    return lambda current, next_value: current + 1 if next_value.bountyStage == stage else current


def get_bounties_issued(time_frame):
    return time_frame.count()


def get_fulfillments_submitted(time_frame):
    return time_frame.count()


def get_fulfillments_accepted(time_frame):
    return time_frame.count()


def get_fulfillments_pending_acceptance(time_frame):
    return 0


def get_fulfillment_acceptance_rate(time_frame):
    return 0


def get_bounty_fulfilled_rate(time_frame):
    return 0


def get_avg_fulfiller_acceptance_rate(time_frame):
    return 0


def get_avg_fulfillment_amount(time_frame):
    return 0


def get_total_fulfillment_amount(time_frame):
    return 0

def get_bounty_draft(time_frame):
    return reduce(add_on(DRAFT_STAGE), time_frame, 0)


def get_bounty_active(time_frame):
    return reduce(add_on(ACTIVE_STAGE), time_frame, 0)


def get_bounty_completed(time_frame):
    return reduce(add_on(COMPLETED_STAGE), time_frame, 0)


def get_bounty_expired(time_frame):
    return reduce(add_on(EXPIRED_STAGE), time_frame, 0)


def get_bounty_dead(time_frame):
    return reduce(add_on(DEAD_STAGE), time_frame, 0)


def generate_timeline(time_frame):
    bounties_state_frame = BountyState.objects.filter(change_date__range=time_frame)
    bounty_created_frame = Bounty.objects.filter(bounty_created__range=time_frame)
    fulfillment_accepted_frame = Fulfillment.objects.filter(accepted_date__range=time_frame)
    fulfillment_submitted_frame = Fulfillment.objects.filter(fulfillment_created__range=time_frame)

    date = time_frame[1]
    bounties_issued = get_bounties_issued(bounty_created_frame)

    fulfillments_submitted = get_fulfillments_submitted(fulfillment_submitted_frame)
    fulfillments_accepted = get_fulfillments_accepted(fulfillment_accepted_frame)

    fulfillments_pending_acceptance = get_fulfillments_pending_acceptance(time_frame)
    fulfillment_acceptance_rate = get_fulfillment_acceptance_rate(time_frame)

    bounty_fulfilled_rate = get_bounty_fulfilled_rate(time_frame)
    avg_fulfiller_acceptance_rate = get_avg_fulfiller_acceptance_rate(time_frame)
    avg_fulfillment_amount = get_avg_fulfillment_amount(time_frame)
    total_fulfillment_amount = get_total_fulfillment_amount(time_frame)

    bounty_draft = get_bounty_draft(bounties_state_frame)
    bounty_active = get_bounty_active(bounties_state_frame)
    bounty_completed = get_bounty_completed(bounties_state_frame)
    bounty_expired = get_bounty_expired(bounties_state_frame)
    bounty_dead = get_bounty_dead(bounties_state_frame)

    bounty_frame = BountiesTimeline(date=date,
                                    bounties_issued=bounties_issued,
                                    fulfillments_submitted=fulfillments_submitted,
                                    fulfillments_accepted=fulfillments_accepted,
                                    fulfillments_pending_acceptance=fulfillments_pending_acceptance,
                                    fulfillment_acceptance_rate=fulfillment_acceptance_rate,
                                    bounty_fulfilled_rate=bounty_fulfilled_rate,
                                    avg_fulfiller_acceptance_rate=avg_fulfiller_acceptance_rate,
                                    avg_fulfillment_amount=avg_fulfillment_amount,
                                    total_fulfillment_amount=total_fulfillment_amount,
                                    bounty_draft=bounty_draft,
                                    bounty_active=bounty_active,
                                    bounty_completed=bounty_completed,
                                    bounty_expired=bounty_expired,
                                    bounty_dead=bounty_dead)

    return bounty_frame


class Command(BaseCommand):
    def handle(self, *args, **options):
        needs_genesis = not BountiesTimeline.objects.all().count()

        if needs_genesis:
            first_date = BountyState.objects.first()
            last_date = BountyState.objects.last()

            bounties_by_day = range_days(first_date.change_date, last_date.change_date)

            for day in bounties_by_day:
                bounty_day = generate_timeline(day_bounds(day))

                bounty_day.save()
        else:
            last_update = BountiesTimeline.objects.order_by('date').last()
            since = arrow.get(last_update.date).to('utc')
            days = range_days(since, datetime.utcnow())

            # Instead of calculate the last 5 min, we update all day until now
            # this approach provides more flexibility and simplicity in calculating more stats in the future
            # and provides a better way to expose by day or by hour in case of been needed
            for day in days:
                bounty_day = generate_timeline(day_bounds(day))
                bounty_points = BountiesTimeline.objects.filter(date=day.date())

                if bounty_points.exists():
                    bounty_point = bounty_points.first()
                    bounty_day.id = bounty_point.id

                bounty_day.save()