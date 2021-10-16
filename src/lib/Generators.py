STUDENT_DOMAIN = '@student.gssb.org'
TEACHER_DOMAIN = '@gssb.org'

def __formatFirstName(name):
    return (
        name
            .strip()
            .replace(' ', '')
            .replace('\'', '')
            )

def __formatLastName(name):
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

def __createEmailAddress(first_name, last_name, domain):
    return (__formatFirstName(first_name) + '.'
            + __formatLastName(last_name)
            + domain)

def createStudentEmailAddress(first_name, last_name):
    return __createEmailAddress(first_name, last_name, STUDENT_DOMAIN)

def createTeacherEmailAddress(first_name, last_name, email):
    if email.strip().endswith('@gssb.org'):
        return email.strip()

    return __createEmailAddress(first_name, last_name, TEACHER_DOMAIN)
