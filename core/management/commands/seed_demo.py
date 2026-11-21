import random
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import (
    User, Category, Program, Session, Enrollment, Attendance,
    ActivityLog, Goal, Notification, Feedback, ProgressNote
)


class Command(BaseCommand):
    help = "Seeds demo accounts and realistic sample wellness data (idempotent)."

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("🌱 Starting database demo seed..."))

        demo_password = "Demo@1234"

        # 1. Create Core Demo Accounts
        admin_user, _ = User.objects.get_or_create(
            username='admin_demo',
            defaults={
                'email': 'admin@wellness.local',
                'first_name': 'Alexandra',
                'last_name': 'Vance',
                'role': User.Role.ADMIN,
                'is_staff': True,
                'is_superuser': True,
                'department': 'Operations',
            }
        )
        admin_user.set_password(demo_password)
        admin_user.role = User.Role.ADMIN
        admin_user.is_staff = True
        admin_user.is_superuser = True
        admin_user.save()

        coord_user, _ = User.objects.get_or_create(
            username='coord_demo',
            defaults={
                'email': 'coordinator@wellness.local',
                'first_name': 'Marcus',
                'last_name': 'Chen',
                'role': User.Role.COORDINATOR,
                'department': 'Human Resources & Wellness',
                'bio': 'Certified Wellness Program Coordinator with 7 years managing workplace fitness and lifestyle workshops.'
            }
        )
        coord_user.set_password(demo_password)
        coord_user.role = User.Role.COORDINATOR
        coord_user.save()

        pro_user, _ = User.objects.get_or_create(
            username='pro_demo',
            defaults={
                'email': 'professional@wellness.local',
                'first_name': 'Dr. Elena',
                'last_name': 'Rostova',
                'role': User.Role.PROFESSIONAL,
                'professional_title': 'Lead Exercise Physiologist & Clinical Nutritionist',
                'department': 'Health Sciences',
                'bio': 'Specializing in metabolic conditioning, mindfulness, and functional longevity.'
            }
        )
        pro_user.set_password(demo_password)
        pro_user.role = User.Role.PROFESSIONAL
        pro_user.save()

        hr_user, _ = User.objects.get_or_create(
            username='hr_demo',
            defaults={
                'email': 'hr@wellness.local',
                'first_name': 'Sarah',
                'last_name': 'Jenkins',
                'role': User.Role.HR,
                'department': 'People & Culture Leadership',
            }
        )
        hr_user.set_password(demo_password)
        hr_user.role = User.Role.HR
        hr_user.save()

        primary_participant, _ = User.objects.get_or_create(
            username='user_demo',
            defaults={
                'email': 'participant@wellness.local',
                'first_name': 'Jordan',
                'last_name': 'Taylor',
                'role': User.Role.PARTICIPANT,
                'department': 'Software Engineering',
                'points': 240,
            }
        )
        primary_participant.set_password(demo_password)
        primary_participant.role = User.Role.PARTICIPANT
        primary_participant.save()

        self.stdout.write(self.style.SUCCESS("✓ Demo accounts ensured with password Demo@1234"))

        # 2. Create 20 Participants
        first_names = ['Liam', 'Olivia', 'Noah', 'Emma', 'Oliver', 'Charlotte', 'Elijah', 'Amelia',
                       'James', 'Ava', 'William', 'Sophia', 'Benjamin', 'Isabella', 'Lucas', 'Mia',
                       'Henry', 'Evelyn', 'Alexander', 'Harper']
        last_names = ['Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
                      'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez', 'Wilson', 'Anderson',
                      'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin']
        departments = ['Engineering', 'Marketing', 'Product', 'Finance', 'Customer Support', 'Design', 'Data Science', 'Operations']

        participants = [primary_participant]
        for i in range(19):
            uname = f"participant_{i+1:02d}"
            fname = first_names[i]
            lname = last_names[i]
            dept = departments[i % len(departments)]
            u, created = User.objects.get_or_create(
                username=uname,
                defaults={
                    'email': f"{uname}@wellness.local",
                    'first_name': fname,
                    'last_name': lname,
                    'role': User.Role.PARTICIPANT,
                    'department': dept,
                    'points': random.randint(50, 350),
                }
            )
            u.set_password(demo_password)
            u.role = User.Role.PARTICIPANT
            u.department = dept
            u.save()
            participants.append(u)

        self.stdout.write(self.style.SUCCESS(f"✓ 20 Participants ready"))

        # 3. Create Categories
        categories_data = [
            {
                'name': 'Fitness & Exercise',
                'description': 'High-energy movement, cardio conditioning, strength training, and functional mobility.',
                'icon': 'bi-activity',
                'color': '#059669',
            },
            {
                'name': 'Nutrition & Diet',
                'description': 'Balanced eating habits, metabolic health, meal planning, and wholesome culinary science.',
                'icon': 'bi-apple',
                'color': '#0d9488',
            },
            {
                'name': 'Mental Health & Mindfulness',
                'description': 'Stress resilience, guided meditation, emotional wellness, and cognitive renewal.',
                'icon': 'bi-flower1',
                'color': '#0284c7',
            },
            {
                'name': 'Health Screening & Prevention',
                'description': 'Biometric screenings, cardiovascular health checks, preventive longevity assessments.',
                'icon': 'bi-heart-pulse-fill',
                'color': '#e11d48',
            },
            {
                'name': 'Ergonomics & Desk Mobility',
                'description': 'Postural correction, workplace physical therapy, cervical spine and lumbar decompression.',
                'icon': 'bi-person-arms-up',
                'color': '#d97706',
            },
            {
                'name': 'Sleep Optimization & Recovery',
                'description': 'Circadian rhythm calibration, deep sleep architecture, and restorative nervous system recovery.',
                'icon': 'bi-moon-stars-fill',
                'color': '#7c3aed',
            },
        ]

        cats = {}
        for cdata in categories_data:
            cat, _ = Category.objects.update_or_create(
                name=cdata['name'],
                defaults=cdata
            )
            cats[cat.name] = cat

        self.stdout.write(self.style.SUCCESS("✓ 6 Wellness categories configured"))

        # 4. Create 6 Rich Programs
        today = timezone.now().date()
        programs_data = [
            {
                'title': '10-Week Workplace Endurance & 5K Challenge',
                'description': 'Transform your cardiovascular fitness with progressive interval training, running mechanics, and stamina coaching. Perfect for beginners to intermediate joggers.',
                'category': cats['Fitness & Exercise'],
                'start_date': today - timedelta(days=28),
                'end_date': today + timedelta(days=42),
                'capacity': 25,
                'status': Program.Status.ACTIVE,
            },
            {
                'title': 'Mindful Resilience: Stress Reduction & Meditation',
                'description': 'Scientifically backed mindfulness practices, breathwork (box breathing, 4-7-8), and cognitive stress-coping strategies to reduce burnout and enhance focus.',
                'category': cats['Mental Health & Mindfulness'],
                'start_date': today - timedelta(days=21),
                'end_date': today + timedelta(days=21),
                'capacity': 30,
                'status': Program.Status.ACTIVE,
            },
            {
                'title': 'Mediterranean Fuel: Nutrition & Gut Longevity Workshop',
                'description': 'Explore plant-rich, whole-food dietary patterns that nourish your microbiome, stabilize energy levels, and curb afternoon fatigue. Includes meal prep masterclasses.',
                'category': cats['Nutrition & Diet'],
                'start_date': today - timedelta(days=14),
                'end_date': today + timedelta(days=35),
                'capacity': 20,
                'status': Program.Status.ACTIVE,
            },
            {
                'title': 'Comprehensive Biometrics & Preventive Health Screening',
                'description': 'Professional biometric screening including blood pressure, lipid panels, BMI, resting metabolic rates, and personalized consultations with healthcare providers.',
                'category': cats['Health Screening & Prevention'],
                'start_date': today - timedelta(days=45),
                'end_date': today - timedelta(days=5),
                'capacity': 40,
                'status': Program.Status.COMPLETED,
            },
            {
                'title': 'Postural Correction & Desk Ergonomics Workshop',
                'description': 'Combat prolonged sitting fatigue. Learn targeted thoracic spine mobility, hip flexor releases, and ergonomic workstation setups for pain-free productivity.',
                'category': cats['Ergonomics & Desk Mobility'],
                'start_date': today + timedelta(days=7),
                'end_date': today + timedelta(days=45),
                'capacity': 22,
                'status': Program.Status.UPCOMING,
            },
            {
                'title': 'Sleep Architecture & Circadian Reset Protocol',
                'description': 'Master the science of deep sleep, blue light mitigation, sleep hygiene, and evening unwind routines to boost cognitive vitality and athletic recovery.',
                'category': cats['Sleep Optimization & Recovery'],
                'start_date': today + timedelta(days=14),
                'end_date': today + timedelta(days=60),
                'capacity': 18,
                'status': Program.Status.UPCOMING,
            },
        ]

        created_programs = []
        for pdata in programs_data:
            prog, _ = Program.objects.update_or_create(
                title=pdata['title'],
                defaults={
                    **pdata,
                    'coordinator': coord_user,
                    'assigned_professional': pro_user,
                }
            )
            created_programs.append(prog)

        self.stdout.write(self.style.SUCCESS("✓ 6 Wellness programs created"))

        # 5. Create Sessions for each program
        session_templates = {
            '10-Week Workplace Endurance & 5K Challenge': [
                ("Session 1: Aerobic Base & Stride Form", -21, True, "Track & Field Grounds"),
                ("Session 2: Interval Training Fundamentals", -14, True, "Fitness Studio A"),
                ("Session 3: Tempo Runs & Breath Control", -7, True, "Campus Loop / Outdoor"),
                ("Session 4: Hill Repeats & Lower Body Power", 7, False, "West Hill Trail"),
                ("Session 5: 5K Race Simulation & Recovery", 21, False, "Main Athletic Field"),
            ],
            'Mindful Resilience: Stress Reduction & Meditation': [
                ("Session 1: Neurobiology of Stress & Somatic Awareness", -18, True, "Zen Room 301"),
                ("Session 2: Breathwork & Parasympathetic Activation", -11, True, "Zen Room 301 / Zoom"),
                ("Session 3: Cognitive Reframing & Focus Habits", -4, True, "Zen Room 301"),
                ("Session 4: Mindful Communication in Workplaces", 5, False, "Executive Boardroom"),
            ],
            'Mediterranean Fuel: Nutrition & Gut Longevity Workshop': [
                ("Session 1: Understanding Macronutrients & Glycemic Index", -10, True, "Culinary Lab / Zoom"),
                ("Session 2: Microbiome Diversity & Fermented Foods", -3, True, "Culinary Lab"),
                ("Session 3: Batch Cooking & Healthy Office Lunches", 11, False, "Culinary Lab"),
            ],
            'Comprehensive Biometrics & Preventive Health Screening': [
                ("Session 1: Morning Fasting Biometric Lab Draws", -40, True, "Wellness Center Clinic"),
                ("Session 2: Cardiovascular EKG & Vitals Assessment", -30, True, "Wellness Center Clinic"),
                ("Session 3: Individual Physician Results Consultations", -10, True, "Private Consult Suites"),
            ],
            'Postural Correction & Desk Ergonomics Workshop': [
                ("Session 1: Posture Assessment & Spine Alignment", 10, False, "Ergonomics Lab"),
                ("Session 2: Micro-stretching at the Desk", 24, False, "Ergonomics Lab / Zoom"),
            ],
            'Sleep Architecture & Circadian Reset Protocol': [
                ("Session 1: Melatonin, Light & Circadian Clocks", 16, False, "Lecture Hall C"),
                ("Session 2: Sleep Tracker Data & Temperature Control", 30, False, "Lecture Hall C"),
            ],
        }

        created_sessions = {}
        for prog in created_programs:
            created_sessions[prog.title] = []
            templates = session_templates.get(prog.title, [])
            for s_title, day_offset, completed, location in templates:
                s_date = today + timedelta(days=day_offset)
                sess, _ = Session.objects.update_or_create(
                    program=prog,
                    title=s_title,
                    defaults={
                        'description': f"Comprehensive interactive session covering {s_title}.",
                        'session_date': s_date,
                        'start_time': '10:00:00',
                        'end_time': '11:15:00',
                        'location': location,
                        'is_completed': completed,
                    }
                )
                created_sessions[prog.title].append(sess)

        self.stdout.write(self.style.SUCCESS("✓ Sessions scheduled and marked"))

        # 6. Enrollments and Attendance
        # Enroll user_demo in the first 3 active/completed programs
        target_programs = created_programs[:4]
        for prog in target_programs:
            Enrollment.objects.get_or_create(
                user=primary_participant,
                program=prog,
                defaults={'status': 'ENROLLED'}
            )

        # Distribute remaining participants across programs
        for i, participant in enumerate(participants[1:]):
            # Enroll in 2 to 3 programs
            chosen_progs = random.sample(created_programs, k=min(3, len(created_programs)))
            for prog in chosen_progs:
                if not prog.is_full:
                    Enrollment.objects.get_or_create(
                        user=participant,
                        program=prog,
                        defaults={'status': 'ENROLLED'}
                    )

        # Mark Attendance for completed sessions
        for prog in created_programs:
            completed_sessions = [s for s in created_sessions.get(prog.title, []) if s.is_completed]
            if not completed_sessions:
                continue

            enrolled_list = Enrollment.objects.filter(program=prog, status='ENROLLED')
            for enr in enrolled_list:
                # user_demo attends almost all sessions to guarantee >= 75% reward eligibility!
                is_demo = (enr.user == primary_participant)
                for sess in completed_sessions:
                    if is_demo:
                        attended = True
                    else:
                        # 80% attendance chance
                        attended = random.random() > 0.20

                    Attendance.objects.update_or_create(
                        session=sess,
                        enrollment=enr,
                        defaults={
                            'attended': attended,
                            'marked_by': coord_user,
                            'notes': 'On time and active' if attended else 'Excused absence',
                        }
                    )

        self.stdout.write(self.style.SUCCESS("✓ Enrollments and attendance records created"))

        # 7. Activity Logs for Participants (past 14 days)
        for participant in participants[:10]: # Top 10 participants have full 14-day logs
            for days_back in range(14):
                log_day = today - timedelta(days=days_back)
                # Realistic stats
                steps = random.randint(5500, 13500)
                workout = random.choice([25, 30, 45, 60, 0, 40, 50])
                water = random.randint(1800, 3500)
                sleep = round(random.uniform(6.0, 8.8), 1)
                meals = random.choice([
                    "Oatmeal with berries for breakfast, grilled salmon salad for lunch, green tea.",
                    "Greek yogurt with chia seeds, quinoa avocado bowl, plenty of hydration.",
                    "Scrambled eggs with spinach, chicken breast and steamed broccoli.",
                    "Smoothie with whey protein and bananas, roasted vegetables with tofu.",
                    "Healthy Mediterranean wrap, apple with almond butter, 2.5L water.",
                ])

                ActivityLog.objects.get_or_create(
                    user=participant,
                    log_date=log_day,
                    defaults={
                        'steps': steps,
                        'workout_minutes': workout,
                        'water_intake_ml': water,
                        'sleep_hours': sleep,
                        'meals_notes': meals,
                    }
                )

        self.stdout.write(self.style.SUCCESS("✓ Realistic 14-day activity logs generated"))

        # 8. Goals for Participants
        goals_data = [
            ("Walk 10,000 steps daily", Goal.GoalType.STEPS, 10000, "steps", False),
            ("Workout 45 minutes 4x a week", Goal.GoalType.WORKOUT, 45, "mins", True),
            ("Drink 2.5 Liters of water daily", Goal.GoalType.WATER, 2500, "ml", True),
            ("Achieve 8 hours of restorative sleep", Goal.GoalType.SLEEP, 8.0, "hours", False),
        ]
        for title, gtype, val, unit, achieved in goals_data:
            Goal.objects.get_or_create(
                user=primary_participant,
                title=title,
                defaults={
                    'goal_type': gtype,
                    'target_value': val,
                    'unit': unit,
                    'is_achieved': achieved,
                    'target_date': today + timedelta(days=14),
                }
            )

        # 9. Feedbacks for Completed / Active Programs
        feedback_samples = [
            (5, "Incredible experience! The coordinator and Dr. Elena provided exceptional guidance. My stamina has noticeably improved."),
            (5, "The mindfulness sessions completely shifted my workday focus and reduced my stress levels."),
            (4, "Very practical nutrition advice. The meal prep strategies were easy to integrate into a busy work schedule."),
            (5, "Screening was conducted smoothly and the personalized recommendations were eye-opening."),
        ]

        for i, prog in enumerate(created_programs[:4]):
            rating, text = feedback_samples[i % len(feedback_samples)]
            Feedback.objects.update_or_create(
                program=prog,
                participant=primary_participant,
                defaults={
                    'rating': rating,
                    'comments': text,
                }
            )
            # Add feedbacks from a few other participants
            for extra_user in participants[1:4]:
                Feedback.objects.get_or_create(
                    program=prog,
                    participant=extra_user,
                    defaults={
                        'rating': random.choice([4, 5]),
                        'comments': "Thoroughly enjoyed the program sessions and the community support!",
                    }
                )

        # 10. Progress Notes by Professional
        notes_data = [
            (created_programs[0], None, ProgressNote.NoteType.RECOMMENDATION, "Aerobic Base Building Guidelines",
             "All endurance runners should maintain Zone 2 heart rate (65-75% max HR) during easy runs. Prioritize dynamic stretching before runs and cold foam rolling post-run."),
            (created_programs[0], primary_participant, ProgressNote.NoteType.MILESTONE, "Remarkable Stride Efficiency",
             "Jordan demonstrated superb hip mobility and cadence pacing during Session 3. Ready to advance to interval tempo splits next week!"),
            (created_programs[1], None, ProgressNote.NoteType.RECOMMENDATION, "Midday Reset Protocol",
             "Incorporate 3 minutes of cyclic sighing (two quick inhales through nose, long audible exhale through mouth) whenever workday tension spikes."),
            (created_programs[2], None, ProgressNote.NoteType.OBSERVATION, "Dietary Fiber & Satiety Metrics",
             "Participants report steady afternoon energy levels after adopting the 30g daily fiber target. Excellent group engagement."),
        ]
        for prog, part, ntype, title, content in notes_data:
            ProgressNote.objects.get_or_create(
                program=prog,
                participant=part,
                title=title,
                defaults={
                    'professional': pro_user,
                    'note_type': ntype,
                    'content': content,
                }
            )

        # 11. Notifications
        notifications_data = [
            (primary_participant, "Eligible for Wellness Reward! 🎖️", "Great job! Your participation rate in '10-Week Workplace Endurance & 5K Challenge' is 100%, exceeding the 75% threshold! You have earned wellness milestone points.", Notification.NotificationType.REWARD),
            (primary_participant, "[10-Week Workplace Endurance] Upcoming Hill Repeats", "Reminder: Session 4 takes place next Tuesday at West Hill Trail. Bring water and running shoes!", Notification.NotificationType.ANNOUNCEMENT),
            (primary_participant, "Goal Milestone Reached! 🏆", "You achieved your target of 45 workout minutes! +50 wellness points added to your account.", Notification.NotificationType.GOAL_ACHIEVED),
        ]
        for u, title, msg, ntype in notifications_data:
            Notification.objects.get_or_create(
                user=u,
                title=title,
                defaults={
                    'message': msg,
                    'notification_type': ntype,
                    'is_read': False,
                }
            )

        self.stdout.write(self.style.SUCCESS("🎉 Demo data seed finished successfully!"))
