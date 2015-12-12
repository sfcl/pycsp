#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from getpass import getpass
import sys
from lib import Installer


pswd = getpass('Input password: ')
if pswd != 'qwerty123':
    input('Password not correct!')
    sys.exit(1)
 
# mode = ('cmd', 'gpp',)
ins = Installer(mode='cmd')

# утсанавливаем ЭП
ins.install_ep()
ins.install_crt()
input('Pause...')
