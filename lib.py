#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys, os, re, shutil, glob
import getpass
import subprocess
import logging
import settings
from hash_table import hash_table
from cert_info import cert_info

class Installer(object):
    """Установщик ЭЦП в реестр КриптоПРО.
    """
    def __init__(self, mode='cmd'):
        # mode=('cmd', 'gpp', 'ui')
        # пока поддерживается 2 режима работы cmd и gpp. В cmd пользователь вводит
        # номаер ЭП исходя из списка предложеннных вариантов. 
        # gpp - скрипт самостоятельно определяет какую ЭП необходимо установить на основе
        # имени пользователя windows. 
        self.mode = mode
        self.current_path = os.path.dirname(os.path.abspath(__file__))
        self.ecp_structure = {} 
        # { 'nlastname': {'secure_cont': 'TExpressEx_2014_12_10_15_06_2', 'fio' : 'Иванов Иван Иванович', 'inx': 5} }
        self.ver = ''
        self.key_conteyner = ''
        self.user_name = ''
        self.select_number = 0
        self.distr_path = self.search_distrib()
        
        # Настраиваем логирование
        if not os.path.exists(self.current_path + '/logs'):
            os.makedirs(self.current_path + '/logs')
        
        # Проверяем наличие ключевых файловых путей 
        if not os.path.exists(settings.ECP_PATH):
            self.send_error('Не определён путь к закрытым контейнерам. Настройте файл settings.py')
            sys.exit(1)

        logging.basicConfig(filename=self.current_path + '/logs/debug.log',
                            format='%(asctime)s %(levelname)s:%(message)s',
                            level = logging.DEBUG )
        
        # завершаем настройку
        if not self.distr_path :
            self.send_error('Программа КриптоПРО не установлена!')
            sys.exit(1)

        self.ver = self.get_version()
        self.ecps = self.get_list_ecp()
        
        if mode == 'cmd':
            # получить список найденых закрытых контейнеров ЭП 
            self.print_list_ecp()
            # предложение пользователю ввести номер
            self.input_number()
            self.key_conteyner = self.choose_conteyner()

        elif mode == 'gpp':
            # установка ЭП в молчаливом режиме
            self.key_conteyner = self.choose_conteyner()

    def send_error(self, message):
        """Сообщить о ошибке.
        """
        if self.mode == 'cmd':
            print(message)
        elif self.mode == 'gpp':
            logging.error(message)
        else:
            pass
        return
    
    def search_distrib(self):
        """Поиск каталога установки КриптоПРО
        """
        search_paths = ['C:/Program Files (x86)/Crypto Pro/CSP',
                        'C:/Program Files/Crypto Pro/CSP',]
        for path_str in search_paths:
            if self.path_exist(path_str):
                path_str = path_str + '/csptest.exe'
                return path_str
        # если программа не установленна, то дальнейшее продолжение невозможно
        self.send_error('Программа csptest не установлена.')
        sys.exit(1)


    def choose_conteyner(self):
        """Выбор ключевого контейнера. На основании введенного пользователем номера.
        """
        if self.mode == 'cmd':
            # { 'nlastname': {'secure_cont': 'TExpressEx_2014_12_10_15_06_2', 'fio' : 'Иванов Иван Иванович', 'inx': 5} }
            for elem in self.ecp_structure.keys():
                data = self.ecp_structure.get(elem, '')
                if data['inx'] == self.select_number:
                    return data['secure_cont']

            self.send_error('Имя закрытого контейнера не найдено (method: selt.choose_conteyner)')
            
        elif self.mode == 'gpp':
            windows_user_name = getpass.getuser()
            windows_user_name = windows_user_name.lower()
            data = self.ecp_structure.get(windows_user_name, '')
            if data:
                return data['secure_cont']
            else:
                self.send_error('Для пользователя %s не найдено закрытого контейнера' % (windows_user_name,))
                
        sys.exit(1)
        return None

    def path_exist(self, dir_path=''):
        """Проверяет, есть ли каталог с данным именем
        """
        try:
            os.stat(dir_path)
        except FileNotFoundError:
            return False
        return True

    def get_list_ecp(self):
        """Заполняем структуру self.ecp_structure нужными данными
        """
        #заполняем структуру данных
        # { 'nlastname': {'secure_cont': 'TExpressEx_2014_12_10_15_06_2', 'fio' : 'Иванов Иван Иванович', 'inx': 5} }

        # 
        # {'nlastname': 'key_name_folder'}
        # просматриваем все каталоги settings.ECP_PATH
        # http://stackoverflow.com/questions/141291/how-to-list-only-top-level-directories-in-python
        ld = [ name for name in os.listdir(settings.ECP_PATH) if os.path.isdir(os.path.join(settings.ECP_PATH, name)) ]

        if len(ld) == 0:
            self.send_error('Каталог %s с закрытыми контейнерами ЭП пуст. Устанавливать нечего!' % (settings.ECP_PATH, ))
            sys.exit(1)

        temp_dict = {}
        counter = 1

        for id_uname in hash_table.keys():
            with open(settings.ECP_PATH + hash_table.get(id_uname) + '/name.key', 'r', encoding="latin1") as fd:
                key_name = fd.read()
                key_name = key_name[4:]
            
            cert_file = settings.ECP_PATH + id_uname + '.cer'
            fio = cert_info(cert_file)
            self.ecp_structure[id_uname] = {'secure_cont':  key_name, 'fio': fio, 'inx': counter}
            counter += 1
        temp_dict['len'] = counter - 1
        return temp_dict
        
    def print_list_ecp(self):
        """Распечатка списка имеющихся закрытых контейнеров упорядоченных по возрастанию.
        """
        #{ 'nlastname': {'secure_cont': 'TExpressEx_2014_12_10_15_06_5', 'fio' : 'Иванов Иван Иванович', 'inx': 5} }
        tmpl = [self.ecp_structure.get(ky).get('inx') for ky in self.ecp_structure.keys() ]
        tmpl.sort()
        for inx in tmpl:
            for k in self.ecp_structure.keys():
                if self.ecp_structure.get(k).get('inx') == inx:
                    print('%2s  :  %2s' % (self.ecp_structure[k]['inx'], self.ecp_structure[k]['fio'],))
                    

    def input_number(self):
        """Примитивный диалог взаимодействия с пользователем. Определяет атрибут self.user_name.
        """
        num = input('Введите номер устанавливаемого ЭЦП = ')
        try:
            num = int(num)
        except ValueError:
            self.send_error('Допустим ввод только чисел!')
            sys.exit(1)

        try:
            ep_count = self.ecps['len'] + 1
            ep_list = range(1, ep_count)
            if num in ep_list:
                self.select_number = num
            else:
                raise(KeyError)
        except KeyError:
            self.send_error('Веденое число не принадлежит доступному диапазону.')
            sys.exit(1)

        for k in self.ecp_structure.keys():
            if self.ecp_structure.get(k, '').get('inx') == self.select_number:
                fio = self.ecp_structure.get(k, '').get('fio')
                break

        fio = fio.split(' ')
        fio = fio[0] + '_' + fio[1][0] + fio[2][0]
        self.user_name = fio
        return None
            

    def get_version(self):
        """Получить версию программы csptest
        """
        if self.path_exist(dir_path='./bin/filever.exe'):
            pass
        else:
            self.send_error('Не найдена программа filever.exe. Дальнейшее продолжение невозможно.')
            sys.exit(1)
        
        pipe = subprocess.Popen([ self.current_path + '\\bin\\' + 'filever.exe', '-v' , self.distr_path], shell=True, stdout=subprocess.PIPE)
        raw_string = pipe.stdout.read().decode('UTF-8', 'ignore')

        result = re.findall("FileVersion\s+(.*)\r\n", raw_string, re.MULTILINE)
        result = result[0]

        # выбираем первые две цифры в названии
        result = result.split('.')
        result = result[0:2]
        result = '.'.join(result)
        return result

    def install_ep(self):
        """Установка ЭП
        """
        dst_cont = '\\\\.\\REGISTRY\\' + self.user_name
        if self.ver == '3.9':
            big_array_list = [
                            self.distr_path, '-keycopy', 
                            '-src', self.key_conteyner,
                            '-pinsrc', '',
                            '-dest', dst_cont,
                            '-pindest', ''
                            ]
            pipe = subprocess.Popen(big_array_list, shell=True, stdout=subprocess.PIPE)
            raw_string = pipe.stdout.read().decode('UTF-8', 'ignore')
            print('raw_string', raw_string)
        
        elif self.ver == '4.0':
            big_array_list = [
                            self.distr_path, '-keycopy', 
                            '-contsrc', self.key_conteyner,
                            '-pinsrc','',
                            '-contdest', dst_cont,
                            '-pindest','',
                            ]
            pipe = subprocess.Popen(big_array_list, shell=True, stdout=subprocess.PIPE)
            raw_string = pipe.stdout.read().decode('UTF-8', 'ignore')

        else:
            self.send_error('Поддержка программы csptest версии %s не реализована' % (self.ver, ))
            sys.exit(1)
        
        
    def install_crt(self):
        """Установка сертификата в закрытый контейнер
        """
        # "C:\Program Files (x86)\Crypto Pro\CSP\csptest" -property -cinstall  -container "Иванов_ИИ"
        if self.ver == '3.9':
            big_array_list = [
                            self.distr_path, 
                            '-property',
                            '-cinstall',
                            '-container',
                            self.user_name
                            ]
            pipe = subprocess.Popen(big_array_list, shell=True, stdout=subprocess.PIPE)
            raw_string = pipe.stdout.read().decode('UTF-8', 'ignore')
            #print('raw_string', raw_string)

        elif self.ver == '4.0':
            big_array_list = [
                            self.distr_path, 
                            '-property',
                            '-cinstall',
                            '-container',
                            self.user_name
                            ]
            pipe = subprocess.Popen(big_array_list, shell=True, stdout=subprocess.PIPE)
            raw_string = pipe.stdout.read().decode('UTF-8', 'ignore')
            #print('raw_string', raw_string)


        else:
            self.send_error('Поддержка программы csptest версии %s не реализована' % (self.ver, ))
            sys.exit(1)
