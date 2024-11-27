import pytz
import os
tz = os.environ.get('TIME_ZONE')
if not tz:
    raise RuntimeError('set TIME_ZONE environ')
tz = pytz.timezone(tz)