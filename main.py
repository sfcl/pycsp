#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from lib import Installer

# mode = ('cmd', 'gpp',)
ins = Installer(mode='cmd')
# утсанавливаем ЭП
ins.install_ep()
ins.install_crt()
