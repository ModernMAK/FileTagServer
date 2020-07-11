import mimetypes
import re
from email.message import EmailMessage
from email.utils import make_msgid
from os.path import exists
from smtplib import SMTP, SMTP_SSL
from threading import Thread
from typing import Iterable, List, Optional, Union
from urllib.request import urlopen


class Mail:
    """Wrapper around EmailMessage. Handles attachments, embeds, send later in another thread, tls, ssl."""
    default_email = {
        'from': '',
        'username': '',
        'password': '',
        'host': '',
        'port': 25,
        'ssl': False,
        'tls': True,
        'timeout': 0
    }

    def __init__(self, subject: str, body: str, to: Optional[Union[str, Iterable[str]]] = None, _from: Optional[str] = None, reply_to: Optional[str] = None, cc: Optional[Union[str, Iterable[str]]] = None, bcc: Optional[Union[str, Iterable[str]]] = None, html: Optional[str] = None):
        m = self.message = EmailMessage()
        m['Subject'] = subject
        m['From'] = _from or self.default_email['from'] or self.default_email['username']
        if to:
            m['To'] = ','.join(to) if not isinstance(to, str) else to
        if cc:
            m['CC'] = ','.join(cc) if not isinstance(cc, str) else cc
        if bcc:
            m['BCC'] = ','.join(bcc) if not isinstance(bcc, str) else bcc
        if reply_to:
            m['Reply-To'] = ','.join(reply_to) if not isinstance(reply_to, str) else reply_to
        m.set_content(body)
        self.html = html
        if html:
            m.add_alternative(html, subtype='html')

    def embed(self, extra_embed: Optional[List[str]] = None, embed_files: bool = True):
        cids = []
        if embed_files and self.html:
            for file in (extra_embed or []) + re.findall(r'<(?:link|script|img)[\w\"\s=]*(?:href|src)=\"([\w/._:-]+)\"', self.html):
                type = 'local'
                if file.startswith('http') or file.startswith('//'):
                    type = 'remote'
                cid = make_msgid()
                self.html = self.html.replace(file, f'cid:{cid[1:-1]}')
                ctype, encoding = mimetypes.guess_type(file)
                if ctype is None or encoding is not None:
                    ctype = 'application/octet-stream'
                maintype, subtype = ctype.split('/', 1)
                if type == 'local':
                    with open(file, 'rb') as fp:
                        cids.append((fp.read(), maintype, subtype, cid))
                else:
                    with urlopen(file) as fp:
                        cids.append((fp.read(), maintype, subtype, cid))
        if self.html:
            self.message.get_payload()[1].set_payload(self.html)
            for cid in cids:
                self.message.get_payload()[1].add_related(cid[0], cid[1], cid[2], cid=cid[3])
        return self

    def attach(self, *attachments: str):
        for f in attachments:
            if exists(f):
                ctype, encoding = mimetypes.guess_type(f)
                if ctype is None or encoding is not None:
                    ctype = 'application/octet-stream'
                maintype, subtype = ctype.split('/', 1)
                with open(f, 'rb') as fp:
                    self.message.add_attachment(fp.read(), maintype=maintype, subtype=subtype, filename=f)
        return Mail

    def send(self, host: Optional[str] = None, port: Optional[int] = None, username: Optional[str] = None, password: Optional[str] = None, tls: bool = True, ssl: bool = False, timeout: Optional[int] = None, wait: bool = False):
        """actually send the email. uses values from defualt_email if none specified"""
        if not host:
            host = self.default_email['host']
            port = self.default_email['port']
            username = self.default_email['username']
            password = self.default_email['password']
            tls = self.default_email['tls']
            ssl = self.default_email['ssl']
            timeout = self.default_email['timeout']

        def _send():
            with (SMTP_SSL if ssl else SMTP)(host, port, **({'timeout': timeout} if timeout else {})) as s:
                if tls and not ssl:
                    s.starttls()
                s.login(username, password)
                s.send_message(self.message)

        if not self.message['From']:
            del self.message['From']
            self.message['From'] = username
        if not wait:
            Thread(target=_send).start()
        else:
            _send()
