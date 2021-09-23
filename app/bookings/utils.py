import itertools
from datetime import date, datetime, timedelta

from django.utils import timezone

from bookings.models import Booking, BookingTableRelationship
from frontend.utils import get_last_booking_date
from sites.models import Site


def round_time(date):
    """
    Round the given date's time to the nearest 15 mins.
    """
    hour = date.hour
    minute = date.minute

    if minute == 0:
        return date
    elif minute <= 15:
        return date.replace(minute=15)
    elif 15 < minute <= 30:
        return date.replace(minute=30)
    elif 30 < minute <= 45:
        return date.replace(minute=45)
    else:
        if hour == 23:
            hour = 0
        else:
            hour += 1
        return date.replace(hour=hour, minute=0)


class BookingSystem:
    """
    This class contains the methods for the complete booking system.
    """

    DAY_MAPPINGS = {
        0: 'mon',
        1: 'tue',
        2: 'wed',
        3: 'thu',
        4: 'fri',
        5: 'sat',
        6: 'sun',
    }

    def __init__(
        self,
        site,
        date,
        party_size,
        frontend=False,
        duration=None,
        exclude_booking_id=None,
    ):
        self.frontend = frontend
        self.site = site

        self.booking_date = date
        self.booking_day = date.weekday()

        self.party_size = party_size
        self.normalised_party_size = self.get_potential_party_sizes()
        self.flat_party_size = set(itertools.chain.from_iterable(self.normalised_party_size))

        self.duration = duration if duration is not None else self.site.booking_duration

        self.exclude_booking_id = exclude_booking_id

        # Fields populated by class.
        self.opening_hour = None
        self.closing_hour = None
        self.min_booking_hour = None
        self.max_booking_hour = None
        self.all_time_slots = []
        self.timetable = {}
        self.available_time_slots = []
        self.already_booked_tables = []

    # ----------------------------------------------------------------------------------
    # PUBLIC METHODS
    # ----------------------------------------------------------------------------------

    def get_available_time_slots(self):
        """
        Generate all timeslots that are available given the parameters the class is
        initialised with.
        """
        self.generate_booking_times()
        self.create_timetable()
        self.populate_timetable()
        self.generate_available_time_slots()

        return self.available_time_slots

    def check_time_slot_available(self, time_slot):
        """
        Return True if the given time_slot is available for booking, False otherwise.
        """
        # Generate the available time slots if it does not exists already.
        if not self.timetable:
            self.get_available_time_slots()

        table_allocation = self.get_tables(time_slot)
        return table_allocation != []

    def get_tables(self, time_slot):
        """
        Return a list of Table ids that are going to be assigned to this booking. It is
        assumed that the given time slot has been validated as being available before
        this method is called.
        """
        # Generate the timetable if it does not exists already.
        if not self.timetable:
            self.get_available_time_slots()

        for potential_table in self.normalised_party_size:
            tables = []
            valid_time_slot = [False for _ in range(len(potential_table))]

            # For each party, find an available Table of the appropriate size.
            for index, party_size in enumerate(potential_table):
                for table, info in self.timetable.items():
                    # Table appropriate size and not already selected.
                    if info['number_of_seats'] == party_size and table not in tables:
                        # If all day duration, needs to be no other Bookings for that day.
                        # Otherwise, the time slot must be present in the Table's timetable.
                        if (
                            self.duration == Site.BookingDurationChoices.ALL
                            and info['booking_count'] == 0
                        ) or (
                            self.duration != Site.BookingDurationChoices.ALL
                            and time_slot in info['timetable']
                        ):
                            valid_time_slot[index] = True
                            tables.append(table)
                            break

            # If Tables found for all parties, return them.
            if all(valid_time_slot):
                return tables
        return []

    # ----------------------------------------------------------------------------------
    # PRIVATE METHODS
    # ----------------------------------------------------------------------------------

    def get_potential_party_sizes(self):
        """
        This method generates all of the potential party sizes the party_size could fall
        into. E.g. if the party_size=2 and the upward_scaling_policy=2 then a Table of
        3 and 4 should also be explorer for availabilities (if they exists). If the
        party_size is greater than the largest Table, the remainder after division only
        has this process applied for it.
        """
        seat_choices = list(
            self.site.tables.all()
            .values_list('number_of_seats', flat=True)
            .order_by('number_of_seats')
        )

        # Ensure there are Tables for the Site.
        if not seat_choices:
            return []

        largest_table = max(seat_choices)

        party_size = self.party_size
        large_party_size = []
        normalised_party_size = []

        if party_size > largest_table:
            # Split the party size into smaller groups when it is greater than the
            # largest table. Splitting rule: split by the largest table size as many
            # times as possible and then find a suitable table for the rest.
            largest_table_count = party_size // largest_table

            for _ in range(largest_table_count):
                if largest_table in seat_choices:
                    # Remove the largest_table_count from the seat_choices to prevent
                    # the same table being used multiple times.
                    seat_choices.remove(largest_table)
                    party_size -= largest_table
                    large_party_size.append(largest_table)

        if party_size != 0:
            scaling_policy = self.site.upward_scaling_policy
            scaled_seats = [
                x for x in set(seat_choices) if party_size <= x <= party_size + scaling_policy
            ]

            # Include large seats (if they exists).
            if scaled_seats:
                normalised_party_size = [[x, *large_party_size] for x in scaled_seats]
        else:
            normalised_party_size = [large_party_size]

        return normalised_party_size

    def generate_booking_times(self):
        """Generate all of the theoretical time slots that could be booked."""
        # Calculate the minimum and maximum range a booking can be made for.
        opening_hour = getattr(self.site, self.DAY_MAPPINGS[self.booking_day] + '_opening_hour')
        closing_hour = getattr(self.site, self.DAY_MAPPINGS[self.booking_day] + '_closing_hour')
        first_booking_time = opening_hour
        last_booking_time = (
            datetime.combine(date.today(), closing_hour)
            - timedelta(minutes=self.site.booking_time_before_closing)
        ).time()

        # If the booking date is today, only show time slots in the future.
        now = timezone.localtime(timezone.now())
        last_booking_date = timezone.localtime(get_last_booking_date(self.site))
        if self.booking_date == last_booking_date.date() == now.date():
            if self.frontend:
                first_booking_time = (
                    round_time(last_booking_date).time().replace(second=0, microsecond=0)
                )
            else:
                first_booking_time = round_time(now).time().replace(second=0, microsecond=0)

        self.opening_hour = opening_hour
        self.closing_hour = closing_hour
        self.min_booking_hour = first_booking_time
        self.max_booking_hour = last_booking_time

        # Create a list of all the possible time slots.
        all_time_slots = []
        temp_date = datetime.combine(date.today(), self.opening_hour)
        while temp_date.time() <= self.closing_hour:
            all_time_slots.append(temp_date.time())
            temp_date += timedelta(minutes=15)

        self.all_time_slots = all_time_slots

    def create_timetable(self):
        """Create a timetable containing the time slots for each "table"."""
        tables = self.site.tables.filter(number_of_seats__in=self.flat_party_size)

        timetable = {
            x.id: {
                'number_of_seats': x.number_of_seats,
                'timetable': self.all_time_slots.copy(),
                'booking_count': 0,
            }
            for x in tables
        }

        self.timetable = timetable

    def populate_timetable(self):
        """
        `Populating` in this context works by removing the current confirmed Bookings
        from the timeable of it's corresponding Table/s.
        """
        # Remove the time slots that have already been booked.
        tables = self.already_booked_tables = (  # For testing purposes
            BookingTableRelationship.objects.filter(
                booking_id__in=Booking.objects.filter(
                    site=self.site,
                    booking_date__date=self.booking_date,
                    status=Booking.StatusChoices.CONFIRMED,
                ).values_list('id', flat=True),
                table__number_of_seats__in=self.flat_party_size,
            )
            .exclude(booking_id=self.exclude_booking_id)
            .select_related('booking', 'table')
            .order_by('created_at')
        )

        for table in tables:
            # Remove this tables time slot from the timetable.
            start_time = timezone.localtime(table.booking.booking_date).time()
            duration = table.booking.duration

            if duration == Site.BookingDurationChoices.ALL:
                time_slots = self.all_time_slots.copy()
            else:
                time_slots = []
                for x in range(duration // 15):
                    time_slot = (
                        datetime.combine(date.today(), start_time) + timedelta(minutes=x * 15)
                    ).time()

                    if time_slot in self.all_time_slots:
                        time_slots.append(time_slot)

            time_table = self.timetable[table.table_id]

            # Increase the booking count for the Table.
            time_table['booking_count'] += 1

            # Remove the already existing Booking's time slots from the timetable for
            # the Table.
            table_time_slots = time_table['timetable']

            for time_slot in time_slots:
                if time_slot in table_time_slots:
                    table_time_slots.remove(time_slot)

    def generate_available_time_slots(self):
        """
        Combine the timetables into a list of available times. It is important to note a
        time slot is only valid if it has enough time slots following it to cover the
        whole duration of the Booking. This method also reduces the time slots in the
        Table's timetable to be all valid time slots to be booked.
        """
        booking_duration_intervals = self.duration // 15

        # For each tables timetable, remove the time slots which cannot be booked.
        for table_time_slots in self.timetable.values():
            table_time_slots = table_time_slots['timetable']
            time_slots = list(table_time_slots)

            # Make sure the time slot is valid and is allowed to be booked for.
            # For each time slot remaining in the tables time slot (indicating no
            # booking for that time), generate the range of time slots a booking
            # would occupy if it was booked for the given duration. If any of these
            # time slots are not in the timetable, the start time slot is not valid.
            for time_slot in time_slots:
                # No need to check a time slot if it has already been removed.
                if time_slot not in table_time_slots:
                    continue

                # Check time slot is in bookable time range.
                if not (self.min_booking_hour <= time_slot <= self.max_booking_hour):
                    if time_slot in table_time_slots:
                        table_time_slots.remove(time_slot)
                    continue

                # Generate all time slots for given start time slot and check if there
                # are all in the timetable.
                valid_time_slots = []

                for x in range(booking_duration_intervals):
                    potential_time_slot = (
                        datetime.combine(date.today(), time_slot) + timedelta(minutes=x * 15)
                    ).time()

                    if potential_time_slot in self.all_time_slots:
                        valid_time_slots.append(potential_time_slot)

                # If any of the time slots are not in the table's timetable, the start
                # time slot is not available for booking.
                for valid_time_slot in valid_time_slots:
                    if valid_time_slot not in table_time_slots:
                        if time_slot in table_time_slots:
                            table_time_slots.remove(time_slot)

        # Now we have the available time slots for all the tables that are valid for the
        # bookings party size. Need to find a combination of table/s that can be booked.
        available_time_slots = []

        for time_slot in self.all_time_slots:
            # Add time slot if any of the potential party sizes can be booked for.
            for potential_party in self.normalised_party_size:
                # Need all values to be True to indicate the time slot is valid.
                valid_time_slot = [False for _ in range(len(potential_party))]
                taken_tables = []

                # For each party, find a Table and set it `unavailable` for other parties.
                for index, party_size in enumerate(potential_party):
                    for table, info in self.timetable.items():
                        if info['number_of_seats'] == party_size:
                            if time_slot in info['timetable'] and table not in taken_tables:
                                valid_time_slot[index] = True
                                taken_tables.append(table)
                                break

                # If all parties have been found a unique Table, the time slot is valid.
                if all(valid_time_slot):
                    available_time_slots.append(time_slot)
                    break

        self.available_time_slots = sorted(available_time_slots)
