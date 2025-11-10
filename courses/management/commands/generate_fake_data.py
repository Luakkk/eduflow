from django.core.management.base import BaseCommand
from faker import Faker
import random
from users.models import User
from courses.models import Course, Lesson, Enrollment

class Command(BaseCommand):
    help = "Generate fake users, courses, lessons, and enrollments"

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=50, help='Number of fake users')
        parser.add_argument('--courses', type=int, default=20, help='Number of fake courses')
        parser.add_argument('--lessons', type=int, default=5, help='Average number of lessons per course')

    def handle(self, *args, **options):
        fake = Faker()
        num_users = options['users']
        num_courses = options['courses']
        num_lessons = options['lessons']

        self.stdout.write(self.style.WARNING("🚀 Starting fake data generation..."))

        # --- USERS ---
        users = []
        for _ in range(num_users):
            role = random.choice([User.Roles.INSTRUCTOR, User.Roles.STUDENT])
            user = User.objects.create_user(
                username=fake.user_name(),
                email=fake.email(),
                password="12345678",
                role=role,
            )
            users.append(user)
        instructors = [u for u in users if u.role == User.Roles.INSTRUCTOR]
        students = [u for u in users if u.role == User.Roles.STUDENT]
        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(users)} users ({len(instructors)} instructors, {len(students)} students)"))

        # --- COURSES ---
        courses = []
        for _ in range(num_courses):
            instructor = random.choice(instructors)
            course = Course.objects.create(
                title=fake.sentence(nb_words=4),
                description=fake.paragraph(nb_sentences=3),
                owner=instructor,
                price=round(random.uniform(10, 100), 2),
                is_published=random.choice([True, False]),
            )
            courses.append(course)
        self.stdout.write(self.style.SUCCESS(f"✅ Created {len(courses)} courses"))

        # --- LESSONS ---
        lessons_created = 0
        for course in courses:
            num_course_lessons = random.randint(max(1, num_lessons - 2), num_lessons + 2)
            for i in range(num_course_lessons):
                Lesson.objects.create(
                    course=course,
                    title=fake.sentence(nb_words=3),
                    content=fake.text(max_nb_chars=400),
                    duration_min=random.randint(5, 30),
                    order_index=i + 1,
                )
                lessons_created += 1
        self.stdout.write(self.style.SUCCESS(f"✅ Created {lessons_created} lessons"))

        # --- ENROLLMENTS ---
        enrollments_created = 0
        for student in students:
            enrolled_courses = random.sample(courses, k=random.randint(1, min(5, len(courses))))
            for course in enrolled_courses:
                Enrollment.objects.get_or_create(student=student, course=course)
                enrollments_created += 1
        self.stdout.write(self.style.SUCCESS(f"✅ Created {enrollments_created} enrollments"))

        self.stdout.write(self.style.SUCCESS("🎉 Fake data generation completed successfully!"))
