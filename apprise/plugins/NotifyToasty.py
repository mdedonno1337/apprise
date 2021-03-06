# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 Chris Caron <lead2gold@gmail.com>
# All rights reserved.
#
# This code is licensed under the MIT License.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files(the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and / or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions :
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import re
import requests

from .NotifyBase import NotifyBase
from .NotifyBase import HTTP_ERROR_MAP
from ..common import NotifyImageSize
from ..utils import compat_is_basestring

# Used to break apart list of potential devices by their delimiter
# into a usable list.
DEVICES_LIST_DELIM = re.compile(r'[ \t\r\n,\\/]+')


class NotifyToasty(NotifyBase):
    """
    A wrapper for Toasty Notifications
    """

    # The default descriptive name associated with the Notification
    service_name = 'Toasty'

    # The services URL
    service_url = 'http://supertoasty.com/'

    # The default protocol
    protocol = 'toasty'

    # A URL that takes you to the setup/help of the specific protocol
    setup_url = 'https://github.com/caronc/apprise/wiki/Notify_toasty'

    # Toasty uses the http protocol with JSON requests
    notify_url = 'http://api.supertoasty.com/notify/'

    # Allows the user to specify the NotifyImageSize object
    image_size = NotifyImageSize.XY_128

    def __init__(self, devices, **kwargs):
        """
        Initialize Toasty Object
        """
        super(NotifyToasty, self).__init__(**kwargs)

        if compat_is_basestring(devices):
            self.devices = [x for x in filter(bool, DEVICES_LIST_DELIM.split(
                devices,
            ))]

        elif isinstance(devices, (set, tuple, list)):
            self.devices = devices

        else:
            self.devices = list()

        if len(devices) == 0:
            raise TypeError('You must specify at least 1 device.')

        if not self.user:
            raise TypeError('You must specify a username.')

    def notify(self, title, body, notify_type, **kwargs):
        """
        Perform Toasty Notification
        """

        headers = {
            'User-Agent': self.app_id,
            'Content-Type': 'multipart/form-data',
        }

        # error tracking (used for function return)
        has_error = False

        # Create a copy of the devices list
        devices = list(self.devices)
        while len(devices):
            device = devices.pop(0)

            # prepare JSON Object
            payload = {
                'sender': NotifyBase.quote(self.user),
                'title': NotifyBase.quote(title),
                'text': NotifyBase.quote(body),
            }

            image_url = self.image_url(notify_type)
            if image_url:
                payload['image'] = image_url

            # URL to transmit content via
            url = '%s%s' % (self.notify_url, device)

            self.logger.debug('Toasty POST URL: %s (cert_verify=%r)' % (
                url, self.verify_certificate,
            ))
            self.logger.debug('Toasty Payload: %s' % str(payload))
            try:
                r = requests.get(
                    url,
                    data=payload,
                    headers=headers,
                    verify=self.verify_certificate,
                )
                if r.status_code != requests.codes.ok:
                    # We had a problem
                    try:
                        self.logger.warning(
                            'Failed to send Toasty:%s '
                            'notification: %s (error=%s).' % (
                                device,
                                HTTP_ERROR_MAP[r.status_code],
                                r.status_code))

                    except KeyError:
                        self.logger.warning(
                            'Failed to send Toasty:%s '
                            'notification (error=%s).' % (
                                device,
                                r.status_code))

                    # self.logger.debug('Response Details: %s' % r.raw.read())

                    # Return; we're done
                    has_error = True

                else:
                    self.logger.info(
                        'Sent Toasty notification to %s.' % device)

            except requests.RequestException as e:
                self.logger.warning(
                    'A Connection error occured sending Toasty:%s ' % (
                        device) + 'notification.'
                )
                self.logger.debug('Socket Exception: %s' % str(e))
                has_error = True

            if len(devices):
                # Prevent thrashing requests
                self.throttle()

        return not has_error

    @staticmethod
    def parse_url(url):
        """
        Parses the URL and returns enough arguments that can allow
        us to substantiate this object.

        """
        results = NotifyBase.parse_url(url)

        if not results:
            # We're done early as we couldn't load the results
            return results

        # Apply our settings now
        devices = NotifyBase.unquote(results['fullpath'])

        # Store our devices
        results['devices'] = '%s/%s' % (results['host'], devices)

        return results
