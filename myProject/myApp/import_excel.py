import pandas as pd
from myApp.models import Mark, Student, Subject, Exam, StudentPersonal, Classroom, Attendance, Teacher
from django.db import IntegrityError
from datetime import datetime

# Load Excel file once
excel_file = pd.ExcelFile('DATA-FYP-DB.xlsx')

# ==============================
# ✅ Sheet1: Import Mark Records
# ==============================

# df_marks = excel_file.parse('Sheet1')
# print("📄 Importing marks from Sheet1...")

# for _, row in df_marks.iterrows():
#     try:
#         student = Student.objects.get(id=row['student_id'])
#         subject = Subject.objects.get(id=row['subject_id'])
#         exam = Exam.objects.get(id=row['exam_id'])

#         Mark.objects.update_or_create(
#             student=student,
#             subject=subject,
#             exam=exam,
#             defaults={'marks': row['marks']}
#         )
#     except Exception as e:
#         print(f"❌ Error in Mark row {_ + 2}: {e}")

# print("✅ Mark data import complete.\n")

# # ========================================
# # ✅ Sheet2: Import Student Personal Info
# # ========================================

# df_personal = excel_file.parse('Sheet2')
# print("📄 Importing personal info from Sheet2...")

# for _, row in df_personal.iterrows():
#     try:
#         student = Student.objects.get(id=row['student_id'])
#         exam = Exam.objects.get(id=row['exam_id'])

#         StudentPersonal.objects.update_or_create(
#             student=student,
#             exam=exam,
#             defaults={
#                 'address': row['address'],
#                 'famsize': row['famsize'],
#                 'pstatus': row['pstatus'],
#                 'medu': row['medu'],
#                 'fedu': row['fedu'],
#                 'mjob': row['mjob'],
#                 'fjob': row['fjob'],
#                 'guardian': row['guardian'],
#                 'traveltime': row['traveltime'],
#                 'studytime': row['studytime'],
#                 'merit': row['merit'],
#                 'famsup': row['famsup'],
#                 'activities': row['activities'],
#                 'internet': row['internet'],
#                 'famrel': row['famrel'],
#                 'freetime': row['freetime'],
#                 'goout': row['goout'],
#                 'health': row['health'],
#             }
#         )
#     except Exception as e:
#         print(f"❌ Error in Personal row {_ + 2}: {e}")

# print("✅ StudentPersonal data import complete.")

# df = pd.read_excel("DATA-FYP-DB.xlsx", sheet_name="Sheet4")

# print("📥 Importing student data...")

# for index, row in df.iterrows():
#     try:
#         intake = str(row["intake"]).strip()

#         # Auto-generate number_matric_std
#         existing = Student.objects.filter(intake=intake).values_list("number_matric_std", flat=True)
#         suffixes = [int(s[-2:]) for s in existing if s.startswith(f"{intake}02") and s[-2:].isdigit()]
#         next_suffix = max(suffixes, default=0) + 1
#         number_matric_std = f"{intake}02{next_suffix:02d}"

#         # Get related classroom and teacher
#         classroom = Classroom.objects.filter(id=row.get("student_class_id")).first()
#         teacher = Teacher.objects.filter(id=row.get("registered_by_id")).first()

#         student = Student.objects.create(
#             full_name=row["full_name"],
#             nickname=row["nickname"],
#             ic_number=str(row["ic_number"]),
#             age=int(row["age"]),
#             gender=row["gender"],
#             race=row["race"],
#             address=row["address"],
#             intake=intake,
#             number_matric_std=number_matric_std,
#             student_class=classroom,
#             guardian_name=row["guardian_name"],
#             guardian_contact=str(row["guardian_contact"]),
#             guardian_email=row["guardian_email"],
#             registered_by=teacher
#         )

#         print(f"✅ Created: {student.full_name} ({student.number_matric_std})")

#     except IntegrityError as ie:
#         print(f"⚠️ Duplicate entry at row {index + 2}: {ie}")
#     except Exception as e:
#         print(f"❌ Error at row {index + 2}: {e}")

# print("✅ Student import complete.")


# excel_file = pd.ExcelFile('DATA-FYP-DB.xlsx')

# ================================
# ✅ Sheet5: Assign Subjects to Students
# ================================

# df_subjects = excel_file.parse('Sheet5')
# print("📚 Assigning subjects from Sheet5...")

# for _, row in df_subjects.iterrows():
#     try:
#         student = Student.objects.get(id=row['student_id'])
#         subject = Subject.objects.get(id=row['subject_id'])

#         student.subjects.add(subject)
#         print(f"✅ Linked Subject {subject.id} to Student {student.id}")

#     except Exception as e:
#         print(f"❌ Error on row {_ + 2}: {e}")

# print("✅ Subject assignments complete.")

# excel_file = pd.ExcelFile('DATA-FYP-DB.xlsx')
df_attendance = excel_file.parse('Sheet7')

print("📄 Importing attendance from Sheet7...")

rows_inserted = 0
rows_skipped = 0

for idx, row in df_attendance.iterrows():
    try:
        student = Student.objects.get(id=row['student_id'])
        date = pd.to_datetime(row['date']).date()
        status = row['status'].strip().upper()

        # Optionally: assign any teacher (or set null)
        teacher = Teacher.objects.get(id=row['recorded_by_id'])

        # Avoid duplicates
        exists = Attendance.objects.filter(student=student, date=date).exists()
        if exists:
            rows_skipped += 1
            continue

        # Validate status
        if status not in ['P', 'A', 'R']:
            print(f"⚠️ Skipping invalid status in row {idx + 2}: {status}")
            rows_skipped += 1
            continue

        Attendance.objects.create(
            student=student,
            date=date,
            status=status,
            recorded_by=teacher
        )
        rows_inserted += 1

    except Exception as e:
        print(f"❌ Error in row {idx + 2}: {e}")
        rows_skipped += 1

print(f"✅ Done. Inserted: {rows_inserted}, Skipped: {rows_skipped}")
# exec(open('myApp/import_excel.py').read())
# exec(open('myApp/import_excel.py', encoding='utf-8').read())