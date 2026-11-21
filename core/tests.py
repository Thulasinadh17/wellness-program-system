from datetime import timedelta
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from django.core.exceptions import ValidationError
from core.models import User, Category, Program, Session, Enrollment, Attendance


class WellnessSystemTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.password = "TestPass@123"

        # Create Category
        self.category = Category.objects.create(
            name="Fitness",
            description="Fitness programs",
            icon="bi-activity"
        )

        # Create Users
        self.admin = User.objects.create_user(
            username="admin_user",
            password=self.password,
            role=User.Role.ADMIN
        )
        self.coordinator = User.objects.create_user(
            username="coord_user",
            password=self.password,
            role=User.Role.COORDINATOR
        )
        self.participant = User.objects.create_user(
            username="part_user",
            password=self.password,
            role=User.Role.PARTICIPANT
        )
        self.participant2 = User.objects.create_user(
            username="part_user2",
            password=self.password,
            role=User.Role.PARTICIPANT
        )
        self.hr = User.objects.create_user(
            username="hr_user",
            password=self.password,
            role=User.Role.HR
        )

        # Create Program
        today = timezone.now().date()
        self.program = Program.objects.create(
            title="Cardio Blast",
            description="High intensity cardio",
            category=self.category,
            coordinator=self.coordinator,
            start_date=today,
            end_date=today + timedelta(days=30),
            capacity=2,
            status=Program.Status.ACTIVE
        )

    # 1. Authentication & Role Redirect Tests
    def test_login_success_and_redirect(self):
        login_success = self.client.login(username="part_user", password=self.password)
        self.assertTrue(login_success)
        response = self.client.get(reverse('dashboard_redirect'))
        self.assertRedirects(response, reverse('participant_dashboard'))

    def test_login_invalid_credentials(self):
        login_success = self.client.login(username="part_user", password="wrongpassword")
        self.assertFalse(login_success)

    # 2. Role-Based Access Control (RBAC) & 403 Tests
    def test_participant_blocked_from_coordinator_dashboard(self):
        self.client.login(username="part_user", password=self.password)
        response = self.client.get(reverse('coordinator_dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_coordinator_blocked_from_hr_dashboard(self):
        self.client.login(username="coord_user", password=self.password)
        response = self.client.get(reverse('hr_dashboard'))
        self.assertEqual(response.status_code, 403)

    def test_hr_can_access_hr_dashboard(self):
        self.client.login(username="hr_user", password=self.password)
        response = self.client.get(reverse('hr_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_admin_can_access_admin_dashboard(self):
        self.client.login(username="admin_user", password=self.password)
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)

    # 3. Enrollment Rules Tests
    def test_successful_enrollment(self):
        self.client.login(username="part_user", password=self.password)
        response = self.client.post(reverse('program_enroll', args=[self.program.id]))
        self.assertRedirects(response, reverse('program_detail', args=[self.program.id]))
        self.assertTrue(Enrollment.objects.filter(user=self.participant, program=self.program, status='ENROLLED').exists())

    def test_cannot_enroll_twice(self):
        # First enrollment
        Enrollment.objects.create(user=self.participant, program=self.program, status='ENROLLED')
        self.client.login(username="part_user", password=self.password)
        # Attempt second enrollment
        response = self.client.post(reverse('program_enroll', args=[self.program.id]))
        self.assertEqual(Enrollment.objects.filter(user=self.participant, program=self.program, status='ENROLLED').count(), 1)

    def test_capacity_limit_rejection(self):
        # Fill capacity (capacity = 2)
        Enrollment.objects.create(user=self.participant, program=self.program, status='ENROLLED')
        Enrollment.objects.create(user=self.participant2, program=self.program, status='ENROLLED')

        third_user = User.objects.create_user(username="part_user3", password=self.password, role=User.Role.PARTICIPANT)
        self.client.login(username="part_user3", password=self.password)

        # Attempt to enroll when full
        response = self.client.post(reverse('program_enroll', args=[self.program.id]))
        self.assertFalse(Enrollment.objects.filter(user=third_user, program=self.program, status='ENROLLED').exists())

    def test_program_date_validation(self):
        today = timezone.now().date()
        invalid_program = Program(
            title="Invalid Dates",
            description="Test",
            category=self.category,
            coordinator=self.coordinator,
            start_date=today,
            end_date=today - timedelta(days=5),
            capacity=10
        )
        with self.assertRaises(ValidationError):
            invalid_program.clean()

    # 4. Participation % and Reward Eligibility Tests
    def test_participation_rate_and_reward_eligibility(self):
        enrollment = Enrollment.objects.create(user=self.participant, program=self.program, status='ENROLLED')

        # Create 4 sessions
        today = timezone.now().date()
        sessions = []
        for i in range(4):
            s = Session.objects.create(
                program=self.program,
                title=f"Session {i+1}",
                session_date=today + timedelta(days=i),
                start_time="10:00:00",
                end_time="11:00:00",
                is_completed=True
            )
            sessions.append(s)

        # Case 1: Attended 2 of 4 (50%) -> Not eligible
        Attendance.objects.create(session=sessions[0], enrollment=enrollment, attended=True)
        Attendance.objects.create(session=sessions[1], enrollment=enrollment, attended=True)
        Attendance.objects.create(session=sessions[2], enrollment=enrollment, attended=False)
        Attendance.objects.create(session=sessions[3], enrollment=enrollment, attended=False)

        self.assertEqual(enrollment.participation_rate, 50.0)
        self.assertFalse(enrollment.is_eligible_for_reward)

        # Case 2: Attend third session -> 3 of 4 (75%) -> Eligible for reward!
        att3 = Attendance.objects.get(session=sessions[2], enrollment=enrollment)
        att3.attended = True
        att3.save()

        self.assertEqual(enrollment.participation_rate, 75.0)
        self.assertTrue(enrollment.is_eligible_for_reward)
