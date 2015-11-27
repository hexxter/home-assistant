"""
homeassistant.components.notify.xmpp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Jabber (XMPP) notification service.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/notify.xmpp/
"""
import logging

_LOGGER = logging.getLogger(__name__)

from homeassistant.helpers import validate_config
from homeassistant.components.notify import (
    DOMAIN, ATTR_TITLE, BaseNotificationService)

REQUIREMENTS = ['sleekxmpp==1.3.1', 'dnspython3==1.12.0']


def get_service(hass, config):
    """ Get the Jabber (XMPP) notification service. """

    if not validate_config({DOMAIN: config},
                           {DOMAIN: ['sender', 'password', 'recipient']},
                           _LOGGER):
        return None

    return XmppNotificationService(config['sender'],
                                   config['password'],
                                   config['recipient'])


# pylint: disable=too-few-public-methods
class XmppNotificationService(BaseNotificationService):
    """ Implements notification service for Jabber (XMPP). """

    def __init__(self, sender, password, recipient):
        self._sender = sender
        self._password = password
        self._recipient = recipient

    def send_message(self, message="", **kwargs):
        """ Send a message to a user. """

        title = kwargs.get(ATTR_TITLE)
        data = "{}: {}".format(title, message) if title else message

        send_message(self._sender + '/home-assistant', self._password,
                     self._recipient, data)


def send_message(sender, password, recipient, message):
    """ Send a message over XMPP. """
    import sleekxmpp

    class SendNotificationBot(sleekxmpp.ClientXMPP):
        """ Service for sending Jabber (XMPP) messages. """

        def __init__(self):
            super(SendNotificationBot, self).__init__(sender, password)

            logging.basicConfig(level=logging.ERROR)

            self.use_tls = True
            self.use_ipv6 = False
            self.add_event_handler('failed_auth', self.check_credentials)
            self.add_event_handler('session_start', self.start)
            self.connect()
            self.process()

        def start(self, event):
            """ Starts the communication and sends the message. """
            self.send_presence()
            self.get_roster()
            self.send_message(mto=recipient, mbody=message, mtype='chat')
            self.disconnect(wait=True)

        def check_credentials(self, event):
            """" Disconnect from the server if credentials are invalid. """
            self.disconnect()

    SendNotificationBot()
