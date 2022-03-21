from datetime import datetime
from datetime import timedelta
import logging

STUDENT_DOMAIN = '@student.gssb.org'
TEACHER_DOMAIN = '@gssb.org'

def __formatFirstName(name: str) -> str:
    return (
        name
            .strip()
            .replace(' ', '')
            .replace('\'', '')
            )

def __formatLastName(name: str) -> str:
    name = (
        name
            .strip()
            .replace('\'', '')
            )

    if name[:4] in ('van ', 'Van ', 'von ', 'Von '):
        return name.replace(' ', '')
    elif name.startswith('Freiin von '):
        return name.replace('Freiin von ', 'Von').replace(' ','-')
    elif ' zu ' in name:
        return name.replace(' ', '')
    elif ' Zu ' in name:
        return name.replace(' ', '')
    elif name.startswith('de '):
        return name.replace(' ', '')
    elif name.startswith('De '):
        return name.replace(' ', '')
    elif ' Nguyen' in name:
        return name.replace(' ', '')
    elif ' nguyen' in name:
        return name.replace(' ', '')
    else:
        return name.replace(' ', '-')

def __createEmailAddress(first_name: str, last_name: str, domain: str) -> str:
    return (__formatFirstName(first_name) + '.'
            + __formatLastName(last_name)
            + domain)

def createStudentEmailAddress(first_name: str, last_name: str) -> str:
    return __createEmailAddress(first_name, last_name, STUDENT_DOMAIN)

def createTeacherEmailAddress(first_name: str, last_name: str, email: str) -> str:
    if email.strip().endswith('@gssb.org'):
        return email.strip()

    return __createEmailAddress(first_name, last_name, TEACHER_DOMAIN)

GRADE_MAP = {
    'Preschool': 'Prekindergarten',
    'Kindergarten': 'Kindergarten',
    '1st': '1',
    '2nd': '2',
    '3rd': '3',
    '4th': '4',
    '5th': '5',
    '6th': '6',
    '7th': '7',
    '8th': '8',
    '9th - DSD 1': '9',
    '10th - DSD 2 y1': '10',
    '11th - DSD 2 y2': '11',
}

def createGrade(sycamore_grade: str) -> str:

    if sycamore_grade is None:
        logging.warn("Translating None grade to ''.")
        return ''

    if sycamore_grade in GRADE_MAP:
        return GRADE_MAP[sycamore_grade]

    logging.warn("Could not translate grade '" + sycamore_grade + "'.")
    return sycamore_grade

def createSectionName(sycamore_class_name: str, sycamore_section: str) -> str:
    return str(sycamore_class_name) + '-' + str(sycamore_section)

def createTermName(sycamore_term_name: str):
    if sycamore_term_name == 'First':
        return 'S1'
    if sycamore_term_name == 'Second':
        return 'S2'
    if sycamore_term_name == 'Full Year':
        return 'Year'

    logging.warn("Could not translate term '" + sycamore_term_name + "'.")
    return sycamore_term_name

def createTermStart(sycamore_term_name: str, s1_start: datetime.date, s2_start: datetime.date, _year_end: datetime.date):
    if sycamore_term_name == 'First':
        return s1_start
    if sycamore_term_name == 'Second':
        return s2_start
    if sycamore_term_name == 'Full Year':
        return s1_start

    logging.warn("Could not translate term '" + sycamore_term_name + "'.")
    return s1_start

def createTermEnd(sycamore_term_name: str, s1_start: datetime.date, s2_start: datetime.date, year_end: datetime.date):
    if sycamore_term_name == 'First':
        return s2_start - timedelta(days=7)
    if sycamore_term_name == 'Second':
        return year_end
    if sycamore_term_name == 'Full Year':
        return year_end

    logging.warn("Could not translate term '" + sycamore_term_name + "'.")
    return year_end
