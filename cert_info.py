#!/usr/bin/env python3
# -*- coding:utf-8 -*-
import json
from asn1crypto import x509

def cert_info(cert_file=None):
    """Возвращаем ФИО извлеченную из сертификата.
    """
    with open(cert_file, 'rb') as der_file:
        cert = x509.Certificate.load(der_file.read())
        ret = json.dumps(cert.subject.native, indent=2, ensure_ascii=False)
        ret = json.loads(ret)
        ret = ret.get('surname', '') + ' ' + ret.get('given_name','')
        return ret
