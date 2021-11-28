from datetime import datetime

def str_to_datetime(date_string, format):
    if date_string:
        return datetime.strptime(date_string, format)
    return None

def datetime_output(date):
    if date:
        return datetime.strftime(date, '%H:%M  %d %b. %Y')
    return None