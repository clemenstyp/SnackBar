import hashlib
import math
import os
from datetime import datetime
from hashlib import md5
from math import sqrt

import requests
from flask import current_app, send_from_directory, Response
from werkzeug.security import safe_join

from Snackbar import app

# image cache for gravatar images
imageCache = {}


def button_background(user):
    """
        returns the background color based on the username md5
    """
    hash_string = md5(user.encode('utf-8')).hexdigest()
    hash_values = (hash_string[:8], hash_string[8:16], hash_string[16:24])
    background = tuple(int(value, 16) % 256 for value in hash_values)
    return '#%02x%02x%02x' % background


def button_font_color(user):
    """
        returns black or white according to the brightness
    """
    r_coef = 0.241
    g_coef = 0.691
    b_coef = 0.068
    hash_string = md5(user.encode('utf-8')).hexdigest()
    hash_values = (hash_string[:8], hash_string[8:16], hash_string[16:24])
    bg = tuple(int(value, 16) % 256 for value in hash_values)
    b = sqrt(r_coef * bg[0] ** 2 + g_coef * bg[1] ** 2 + b_coef * bg[2] ** 2)
    if b > 130:
        return '#%02x%02x%02x' % (0, 0, 0)
    else:
        return '#%02x%02x%02x' % (255, 255, 255)


def allowed_file(filename):
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions


def monster_image(filename, userID):
    if filename is None:
        return monster_image_for_id(userID)

    fullpath = os.path.join(current_app.root_path, app.config['IMAGE_FOLDER'])

    full_file_path = safe_join(fullpath, filename)
    if not os.path.isabs(full_file_path):
        full_file_path = os.path.join(current_app.root_path, full_file_path)
    try:
        if not os.path.isfile(full_file_path):
            return monster_image_for_id(userID)
        if os.stat(full_file_path).st_size < 1:
            return monster_image_for_id(userID)
    except (TypeError, ValueError):
        pass

    return send_from_directory(directory=fullpath, path=filename, as_attachment=False)


def monster_image_for_id(userID):
    if userID is None:
        userID = "example@example.org"

    use_gravatar = True
    returnValue = send_from_directory(directory=current_app.root_path, path="static/unknown_image.png",
                                      as_attachment=False)

    # mail_parts = userID.split("@")
    # if len(mail_parts) == 2:
    #     prefix = mail_parts[0]
    #     domain = mail_parts[1]
    #     if domain == "fit.fraunhofer.de":
    #         use_gravatar = False
    #         requestURL = "https://chat.fit.fraunhofer.de/avatar/" + prefix
    #         try:
    #             proxyResponse = requests.get(requestURL, timeout=5)
    #
    #             returnValue = Response(proxyResponse)
    #         except:
    #             pass

    if use_gravatar:
        userHash = hashlib.md5(str(userID).encode('utf-8').lower()).hexdigest()
        if userHash in imageCache:
            return imageCache[userHash]

        image = get_monster_id_from_gravatar(userHash)
        if image is False:
            image = get_wavatar_from_gravatar(userHash)

        if image is not False:
            returnValue = image
            imageCache[userHash] = returnValue
    return returnValue


def get_wavatar_from_gravatar(userHash):
    returnValue = False

    requestURL = "https://www.gravatar.com/avatar/" + userHash + "?s=100" + "&d=wavatar"
    try:
        proxyResponse = requests.get(requestURL, timeout=5)
        # imageCache[userHash] = returnValue
        statusCode = proxyResponse.status_code
        if statusCode == 200:
            returnValue = Response(proxyResponse)
    except:
        pass

    return returnValue


def get_monster_id_from_gravatar(userHash):
    returnValue = False

    requestURL = "https://www.gravatar.com/avatar/" + userHash + "?s=100" + "&d=monsterid"
    try:
        proxyResponse = requests.get(requestURL, timeout=5)
        # imageCache[userHash] = returnValue
        statusCode = proxyResponse.status_code
        if statusCode == 200:
            returnValue = Response(proxyResponse)
    except:
        pass

    return returnValue


def image_from_folder(filename, image_folder, the_default_image):
    if filename is None:
        return send_from_directory(directory=current_app.root_path, path=the_default_image, as_attachment=False)

    fullpath = os.path.join(current_app.root_path, image_folder)

    full_file_path = safe_join(fullpath, filename)
    if not os.path.isabs(full_file_path):
        full_file_path = os.path.join(current_app.root_path, full_file_path)
    try:
        if not os.path.isfile(full_file_path):
            return send_from_directory(directory=current_app.root_path, path=the_default_image, as_attachment=False)
    except (TypeError, ValueError):
        pass

    return send_from_directory(directory=fullpath, path=filename, as_attachment=False)
    # return redirect(url)


def reltime(date, compare_to=None, at='@'):
    """Takes a datetime and returns a relative representation of the
    time.
    :param date: The date to render relatively
    :param compare_to: what to compare the date to. Defaults to datetime.now()
    :param at: date/time separator. defaults to "@". "at" is also reasonable.
    """

    def ordinal(n):
        r"""Returns a string ordinal representation of a number
        Taken from: http://stackoverflow.com/a/739301/180718
        """
        if 10 <= n % 100 < 20:
            return str(n) + 'th'
        else:
            return str(n) + {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, "th")

    compare_to = compare_to or datetime.now()
    if date > compare_to:
        return NotImplementedError(f"reltime only handles dates in the past: {date} > {compare_to}")
    # get timediff values
    diff = compare_to - date
    if diff.seconds < 60 * 60 * 8:  # less than a business day?
        days_ago = diff.days
    else:
        days_ago = diff.days + 1
    months_ago = compare_to.month - date.month
    years_ago = compare_to.year - date.year
    weeks_ago = int(math.ceil(days_ago / 7.0))
    # get a non-zero padded 24-hour hour
    hr = date.strftime('%H')
    if hr.startswith('0'):
        hr = hr[1:]
    wd = compare_to.weekday()
    # calculate the time string
    _time = '{0}:{1}'.format(hr, date.strftime('%M').lower())

    # calculate the date string
    if days_ago == 0:
        datestr = 'today {at} {time}'
    elif days_ago == 1:
        datestr = 'yesterday {at} {time}'
    elif (wd in (5, 6) and days_ago in (wd + 1, wd + 2)) or \
            wd + 3 <= days_ago <= wd + 8:
        # this was determined by making a table of wd versus days_ago and
        # divining a relationship based on everyday speech. This is somewhat
        # subjective I guess!
        datestr = 'last {weekday} {at} {time} ({days_ago} days ago)'
    elif days_ago <= wd + 2:
        datestr = '{weekday} {at} {time} ({days_ago} days ago)'
    elif years_ago == 1:
        datestr = '{month} {day}, {year} {at} {time} (last year)'
    elif years_ago > 1:
        datestr = '{month} {day}, {year} {at} {time} ({years_ago} years ago)'
    elif months_ago == 1:
        datestr = '{month} {day} {at} {time} (last month)'
    elif months_ago > 1:
        datestr = '{month} {day} {at} {time} ({months_ago} months ago)'
    else:
        # not last week, but not last month either
        datestr = '{month} {day} {at} {time} ({days_ago} days ago)'
    return datestr.format(time=_time,
                          weekday=date.strftime('%A'),
                          day=ordinal(date.day),
                          days=diff.days,
                          days_ago=days_ago,
                          month=date.strftime('%B'),
                          years_ago=years_ago,
                          months_ago=months_ago,
                          weeks_ago=weeks_ago,
                          year=date.year,
                          at=at)
