from django.db import IntegrityError, connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from .models import Antibiotic, PharmacyProfile, SaleRecord, SystemSettings, User
from .utils.risk import classify, load_area_sales, score_area


def make_pharmacy(username='pharm', latitude=23.8, longitude=90.4):
    user = User.objects.create_user(username=username, password='pw12345678', role='PHARMACY')
    profile = PharmacyProfile.objects.create(
        user=user, name=f'{username} store', address='12 Road, Dhaka',
        latitude=latitude, longitude=longitude,
    )
    return user, profile


class DeleteRequiresPostTests(TestCase):
    """Deletes used to be GET links, so a prefetch or forged <img> could destroy data."""

    def setUp(self):
        self.gov = User.objects.create_user(username='gov', password='pw12345678', role='GOVERNMENT')
        self.client.force_login(self.gov)
        _, self.pharmacy = make_pharmacy()
        self.antibiotic = Antibiotic.objects.create(name='Amoxicillin', group='Penicillin', category='A')

    def test_get_does_not_delete_pharmacy(self):
        response = self.client.get(reverse('pharmacy_delete', args=[self.pharmacy.pk]))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(PharmacyProfile.objects.filter(pk=self.pharmacy.pk).exists())

    def test_get_does_not_delete_antibiotic(self):
        response = self.client.get(reverse('antibiotic_delete', args=[self.antibiotic.pk]))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Antibiotic.objects.filter(pk=self.antibiotic.pk).exists())

    def test_post_deletes_pharmacy_and_its_user(self):
        user_id = self.pharmacy.user_id
        self.client.post(reverse('pharmacy_delete', args=[self.pharmacy.pk]))
        self.assertFalse(PharmacyProfile.objects.filter(pk=self.pharmacy.pk).exists())
        self.assertFalse(User.objects.filter(pk=user_id).exists())


class AntibioticUniquenessTests(TestCase):
    def setUp(self):
        self.gov = User.objects.create_user(username='gov', password='pw12345678', role='GOVERNMENT')
        self.client.force_login(self.gov)
        Antibiotic.objects.create(name='Amoxicillin', group='Penicillin', category='A')

    def test_database_rejects_duplicate_name(self):
        with self.assertRaises(IntegrityError):
            Antibiotic.objects.create(name='Amoxicillin', group='Other', category='B')

    def test_form_rejects_duplicate_ignoring_case(self):
        response = self.client.post(reverse('antibiotic_list'), {
            'name': 'amoxicillin', 'group': 'Penicillin', 'category': 'A',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Antibiotic.objects.filter(name__iexact='amoxicillin').count(), 1)

    def test_recording_a_sale_reuses_existing_name_in_any_case(self):
        _, pharmacy = make_pharmacy()
        self.client.force_login(pharmacy.user)
        self.client.post(reverse('pharmacy_dashboard'), {
            'antibiotic_name': 'AMOXICILLIN', 'quantity': '3',
        })
        self.assertEqual(Antibiotic.objects.count(), 1)
        self.assertEqual(SaleRecord.objects.get().antibiotic.name, 'Amoxicillin')

    def test_government_dashboard_survives_the_full_catalogue(self):
        _, pharmacy = make_pharmacy()
        SaleRecord.objects.create(pharmacy=pharmacy, antibiotic=Antibiotic.objects.first(), quantity=5)
        response = self.client.get(reverse('government_dashboard'))
        self.assertEqual(response.status_code, 200)


class SalesApiTests(TestCase):
    def setUp(self):
        Antibiotic.objects.create(name='Cefixime', group='Cephalosporin', category='B')

    def test_non_pharmacy_gets_403_not_500(self):
        user = User.objects.create_user(username='someone', password='pw12345678', role='INDIVIDUAL')
        self.client.force_login(user)
        response = self.client.post(reverse('api_sales_create'), {'antibiotic_name': 'Cefixime', 'quantity': 2})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(SaleRecord.objects.count(), 0)

    def test_pharmacy_can_record_a_sale(self):
        user, profile = make_pharmacy()
        self.client.force_login(user)
        response = self.client.post(reverse('api_sales_create'), {'antibiotic_name': 'Cefixime', 'quantity': 2})
        self.assertEqual(response.status_code, 201)
        self.assertEqual(SaleRecord.objects.get().pharmacy, profile)

    def test_sale_is_attributed_to_the_caller_not_the_payload(self):
        _, victim = make_pharmacy(username='victim')
        attacker_user, attacker = make_pharmacy(username='attacker')
        self.client.force_login(attacker_user)
        self.client.post(reverse('api_sales_create'), {
            'antibiotic_name': 'Cefixime', 'quantity': 2, 'pharmacy': victim.pk,
        })
        self.assertEqual(SaleRecord.objects.get().pharmacy, attacker)

    def test_zero_quantity_is_rejected(self):
        user, _ = make_pharmacy()
        self.client.force_login(user)
        response = self.client.post(reverse('api_sales_create'), {'antibiotic_name': 'Cefixime', 'quantity': 0})
        self.assertEqual(response.status_code, 400)


class InputValidationTests(TestCase):
    def setUp(self):
        self.gov = User.objects.create_user(username='gov', password='pw12345678', role='GOVERNMENT')
        self.client.force_login(self.gov)

    def test_non_numeric_coordinates_do_not_crash(self):
        response = self.client.post(reverse('pharmacy_list'), {
            'action': 'add', 'username': 'newpharm', 'password': 'pw12345678',
            'name': 'Corner Chemist', 'address': '9 Lane, Dhaka',
            'latitude': 'not-a-number', 'longitude': '',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='newpharm').exists())

    def test_duplicate_username_is_reported_not_raised(self):
        User.objects.create_user(username='taken', password='pw12345678', role='PHARMACY')
        response = self.client.post(reverse('pharmacy_list'), {
            'action': 'add', 'username': 'taken', 'password': 'pw12345678',
            'name': 'Corner Chemist', 'address': '9 Lane, Dhaka',
            'latitude': '23.8', 'longitude': '90.4',
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(User.objects.filter(username='taken').count(), 1)

    def test_valid_pharmacy_is_created(self):
        response = self.client.post(reverse('pharmacy_list'), {
            'action': 'add', 'username': 'newpharm', 'password': 'pw12345678',
            'name': 'Corner Chemist', 'address': '9 Lane, Dhaka',
            'latitude': '23.8', 'longitude': '90.4',
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(PharmacyProfile.objects.filter(name='Corner Chemist').exists())

    def test_garbage_risk_limits_leave_settings_untouched(self):
        self.client.post(reverse('update_risk_limits'), {
            'low_risk_limit': 'abc', 'moderate_risk_limit': '30', 'high_risk_limit': '100',
        })
        self.assertEqual(SystemSettings.load().low_risk_limit, 15)

    def test_risk_limits_must_increase(self):
        self.client.post(reverse('update_risk_limits'), {
            'low_risk_limit': '90', 'moderate_risk_limit': '30', 'high_risk_limit': '100',
        })
        self.assertEqual(SystemSettings.load().low_risk_limit, 15)

    def test_valid_risk_limits_are_saved(self):
        self.client.post(reverse('update_risk_limits'), {
            'low_risk_limit': '5', 'moderate_risk_limit': '20', 'high_risk_limit': '50',
        })
        self.assertEqual(SystemSettings.load().low_risk_limit, 5)

    def test_negative_quantity_is_rejected(self):
        user, _ = make_pharmacy()
        self.client.force_login(user)
        self.client.post(reverse('pharmacy_dashboard'), {'antibiotic_name': 'Cefixime', 'quantity': '-5'})
        self.assertEqual(SaleRecord.objects.count(), 0)


class RoleAccessTests(TestCase):
    def test_individual_cannot_reach_government_pages(self):
        user = User.objects.create_user(username='ind', password='pw12345678', role='INDIVIDUAL')
        self.client.force_login(user)
        for name in ['government_dashboard', 'pharmacy_list', 'antibiotic_list', 'export_sales_csv']:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 302, name)
            self.assertEqual(response.url, reverse('dashboard_redirect'), name)

    def test_pharmacy_without_profile_is_redirected_not_crashed(self):
        user = User.objects.create_user(username='ghost', password='pw12345678', role='PHARMACY')
        self.client.force_login(user)
        response = self.client.get(reverse('pharmacy_dashboard'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('profile_settings'))


class RiskScoringTests(TestCase):
    def setUp(self):
        self.antibiotic = Antibiotic.objects.create(name='Azithromycin', group='Macrolide', category='A')
        _, self.pharmacy = make_pharmacy(latitude=23.80, longitude=90.40)

    def test_thresholds_map_to_expected_bands(self):
        thresholds = SystemSettings.load()  # 15 / 30 / 100
        self.assertEqual(classify(0, thresholds)[1], 'green')
        self.assertEqual(classify(20, thresholds)[1], 'yellow')
        self.assertEqual(classify(50, thresholds)[1], 'orange')
        self.assertEqual(classify(150, thresholds)[1], 'red')

    def test_distant_sales_do_not_raise_local_risk(self):
        _, far = make_pharmacy(username='far', latitude=30.0, longitude=95.0)
        SaleRecord.objects.create(pharmacy=far, antibiotic=self.antibiotic, quantity=500)
        _, color = score_area(load_area_sales(), SystemSettings.load(), self.antibiotic.id, 23.80, 90.40)
        self.assertEqual(color, 'green')

    def test_nearby_sales_accumulate(self):
        SaleRecord.objects.create(pharmacy=self.pharmacy, antibiotic=self.antibiotic, quantity=200)
        _, color = score_area(load_area_sales(), SystemSettings.load(), self.antibiotic.id, 23.80, 90.40)
        self.assertEqual(color, 'red')

    def test_dashboard_queries_do_not_grow_with_catalogue_size(self):
        """The risk grid loads once, so extra antibiotics must not add queries."""
        user = User.objects.create_user(username='ind', password='pw12345678', role='INDIVIDUAL',
                                        latitude=23.80, longitude=90.40)
        self.client.force_login(user)

        # Warm up so one-time costs (creating the settings row) are not counted.
        self.client.get(reverse('user_dashboard'))

        with CaptureQueriesContext(connection) as first:
            self.client.get(reverse('user_dashboard'))
        baseline = len(first.captured_queries)

        for i in range(10):
            Antibiotic.objects.create(name=f'Drug {i}', group='G', category='C')

        with CaptureQueriesContext(connection) as second:
            self.client.get(reverse('user_dashboard'))
        self.assertEqual(len(second.captured_queries), baseline)


class SystemSettingsTests(TestCase):
    def test_load_always_returns_the_same_row(self):
        self.assertEqual(SystemSettings.load().pk, SystemSettings.load().pk)
        self.assertEqual(SystemSettings.objects.count(), 1)

    def test_saving_a_new_instance_overwrites_the_singleton(self):
        SystemSettings.load()
        SystemSettings(low_risk_limit=1, moderate_risk_limit=2, high_risk_limit=3).save()
        self.assertEqual(SystemSettings.objects.count(), 1)
        self.assertEqual(SystemSettings.load().low_risk_limit, 1)
