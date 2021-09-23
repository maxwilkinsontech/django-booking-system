from django.test import TestCase

from model_bakery import baker

from ..utils import get_business_hours, get_resources


class GetBusinessHoursTest(TestCase):
    def setUp(self):
        self.site = baker.make('sites.Site')

    def test_get_business_hours(self):
        expected_business_hours = [
            {
                'startTime': self.site.mon_opening_hour.strftime("%H:%M"),
                'endTime': self.site.mon_closing_hour.strftime("%H:%M"),
                'daysOfWeek': [1],
            },
            {
                'startTime': self.site.tue_opening_hour.strftime("%H:%M"),
                'endTime': self.site.tue_closing_hour.strftime("%H:%M"),
                'daysOfWeek': [2],
            },
            {
                'startTime': self.site.wed_opening_hour.strftime("%H:%M"),
                'endTime': self.site.wed_closing_hour.strftime("%H:%M"),
                'daysOfWeek': [3],
            },
            {
                'startTime': self.site.thu_opening_hour.strftime("%H:%M"),
                'endTime': self.site.thu_closing_hour.strftime("%H:%M"),
                'daysOfWeek': [4],
            },
            {
                'startTime': self.site.fri_opening_hour.strftime("%H:%M"),
                'endTime': self.site.fri_closing_hour.strftime("%H:%M"),
                'daysOfWeek': [5],
            },
            {
                'startTime': self.site.sat_opening_hour.strftime("%H:%M"),
                'endTime': self.site.sat_closing_hour.strftime("%H:%M"),
                'daysOfWeek': [6],
            },
            {
                'startTime': self.site.sun_opening_hour.strftime("%H:%M"),
                'endTime': self.site.sun_closing_hour.strftime("%H:%M"),
                'daysOfWeek': [0],
            },
        ]

        business_hours = get_business_hours(self.site)

        self.assertEqual(expected_business_hours, business_hours)


class GetResourcesTest(TestCase):
    def setUp(self):
        self.site_1 = baker.make('sites.Site', site_name='a')
        self.site_2 = baker.make('sites.Site', site_name='b')
        self.site_1_table_1 = baker.make('sites.Table', site=self.site_1, table_name='a')
        self.site_1_table_2 = baker.make('sites.Table', site=self.site_1, table_name='b')
        self.site_2_table_1 = baker.make('sites.Table', site=self.site_2, table_name='a')
        self.site_2_table_2 = baker.make('sites.Table', site=self.site_2, table_name='b')

    def test_get_resources(self):
        resources = get_resources([self.site_1, self.site_2])

        expected_result = [
            {
                'id': self.site_1_table_1.id,
                'title': self.site_1_table_1.__str__(),
                'siteId': self.site_1.site_name,
                'businessHours': get_business_hours(self.site_1),
            },
            {
                'id': self.site_1_table_2.id,
                'title': self.site_1_table_2.__str__(),
                'siteId': self.site_1.site_name,
                'businessHours': get_business_hours(self.site_1),
            },
            {
                'id': self.site_2_table_1.id,
                'title': self.site_2_table_1.__str__(),
                'siteId': self.site_2.site_name,
                'businessHours': get_business_hours(self.site_2),
            },
            {
                'id': self.site_2_table_2.id,
                'title': self.site_2_table_2.__str__(),
                'siteId': self.site_2.site_name,
                'businessHours': get_business_hours(self.site_2),
            },
        ]

        self.assertJSONEqual(resources, expected_result)
