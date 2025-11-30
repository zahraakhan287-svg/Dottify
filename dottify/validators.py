from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta

def increments_validator(value):
    '''
    Makes sure values increment in 0.5's
    '''
    if value * 2 % 1 != 0 :
        raise ValidationError("Stars should increment in 0.5's")
    
def valid_release_date(value):
    '''
    This makes sure that the release date is not more than six months away.
    '''
    rn = timezone.now().date()
    add_six_month = rn + timedelta(days=180)
    if value > add_six_month:
        raise ValidationError("Release date must be under 6 months")
    