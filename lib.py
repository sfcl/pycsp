#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys, os, re, shutil, glob
import getpass
import subprocess
import logging
import settings
from cert_info import cert_info

class Installer(object):
    """Установщик ЭЦП в реестр КриптоПРО
    """
    def __init__(self, mode='cmd'):
        # mode=('cmd', 'gpp',)
        # пока поддерживается 2 режима работы cmd и gpp. В cmd пользователь сам вводит
        # номаер ЭП исходя из списка предложеннных вариантов. 
        # gpp - скрипт самостоятельно определяет какую ЭП необходимо установить на основе
        # анализа имени пользователя. 
        self.mode = mode
        self.current_path = os.path.dirname(os.path.abspath(__file__))
        self.ecp_structure = {} 
        # { 'nlastname': {'ep_path': 'C:/ECP/nlasnmame', 'fio' : 'Иванов Иван Иванович', 'inx': 5} }
        self.ver = ''
        self.key_conteyner = ''
        self.user_name = ''
        self.select_number = 0
        self.distr_path = self.search_distrib()
        
        # Настраиваем логирование
        if not os.path.exists(self.current_path + '/logs'):
            os.makedirs(self.current_path + '/logs')
        
        logging.basicConfig(filename=self.current_path + '/logs/debug.log',
                            format='%(asctime)s %(levelname)s:%(message)s',
                            level = logging.DEBUG )
        
        # завершаем настройку
        if not self.distr_path :
            self.send_error('Программа КриптоПРО не установлена!')
            sys.exit(1)
            return

        self.ver = self.get_version()
        self.ecps = self.get_list_ecp(search_path=settings.ECP_PATH)
        
        if mode == 'cmd':
            # получить список найденых закрытых контейнеров ЭП 
            self.print_list_ecp()

            # предложение пользователю ввести номер
            self.input_number()

            # подготивительные действия к установке ЭП
            self.clear_flash() # очищаем флешку от старых контейнеров
            self.copy_ecp()    # копируем файлы и каталог с контейнером на флешку

            self.key_conteyner = self.choose_conteyner()
            #logging.debug('Ключевой контейнер %s' % (self.key_conteyner,))
        elif mode == 'gpp':
            # получаем имя пользователя
            pass
            # из структуры self.ecp_structure по имени пользователя определяем номер ЭП
            # которую нужно установить.

    def search_distrib(self):
        """Поиск каталога установки КриптоПРО
        """
        search_paths = ['C:/Program Files (x86)/Crypto Pro/CSP',
                        'C:/Program Files/Crypto Pro/CSP',]
        for path_str in search_paths:
            if self.path_exist(path_str):
                path_str = path_str + '/csptest.exe'
                return path_str
                
        return None

    
    def path_exist(self, dir_path=''):
        """Проверяет, есть ли каталог с данным именем
        """
        try:
            os.stat(dir_path)
        except FileNotFoundError:
            return False
        
        return True

    def get_list_ecp(self, search_path=''):
        """Составляет список каталогов закрытх контейнеров
        """
        # http://stackoverflow.com/questions/141291/how-to-list-only-top-level-directories-in-python
        ld = [ name for name in os.listdir(search_path) if os.path.isdir(os.path.join(search_path, name)) ]
        
        if len(ld) == 0:
            send_error('Каталог %s с ЭП пуст. Устанавливать нечего!' % (search_path, ))
            sys.exit(1)

        temp_dict = {}
        counter = 1
        for elem in ld:
            temp_dict[counter] = elem
            cert_pattern = settings.ECP_PATH + '/' + elem + '/*.cer'
            cert_file = glob.glob(cert_pattern)
            cert_file = cert_file[0]
            fio = cert_info(cert_file)
            self.ecp_structure[elem] = {'ep_path':  settings.ECP_PATH + '/' + elem,
                                        'fio': fio, 'inx': counter,
                                        }
            counter += 1
        temp_dict['len'] = counter - 1

        return temp_dict
        
    def print_list_ecp(self):
        """Распечатка списка закрытых контейнеров и сертификатов.
            Упорядоченных по возрастанию.
        """    
        # { 'nlastname': {'ep_path': 'C:/ECP/nlasnmame', 'fio' : 'Иванов Иван Иванович', 'inx': 5} }
        
        tmpl = [self.ecp_structure.get(ky).get('inx') for ky in self.ecp_structure.keys() ]
        tmpl.sort()
        for inx in tmpl:
            for k in self.ecp_structure.keys():
                if self.ecp_structure.get(k).get('inx') == inx:
                    print('%2s  :  %2s' % (self.ecp_structure[k]['inx'], self.ecp_structure[k]['fio'],))        
        
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

    def input_number(self):
        """Примитивный диалог взаимодействия с пользователем. Определяет атрибут self.user_name.
        """
        num = input('Введите номер устанавливаемого ЭЦП = ')
        try:
            num = int(num)
        except ValueError:
            print('Допустим ввод только чисел!')
            sys.exit(1)

        try:
            self.select_number = num
        except KeyError:
            print('Веденое число не принадлежит доступному диапазону.')
            sys.exit(1)

        # определяем имя закрытого контейнера
        tmp = self.ecps.get(self.select_number)
        #tmp = tmp.split(' ')
        tmp = re.split('\s+', tmp)
        tmp = tmp[0] + '_' +tmp[1][0] + tmp[2][0]
        self.user_name = tmp

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

    def clear_flash(self):
        """Очищаем флешку от старых ЭП
        """
        folder = settings.FLASH_PATH + ':'
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path): 
                    shutil.rmtree(file_path)
            except Exception as e:
                print(e)
                sys.exit(1)
        return None

    def copy_ecp(self):
        """Производим копирование закрытого контейнера на флеш.
        """
        if self.mode == 'cmd':
            src_dir = settings.ECP_PATH + self.ecps[self.select_number] + '/'
        elif self.mode == 'gpp':
            u_name = getpass.getuser()
            if self.ecp_structure.get(u_name, ''):
                src_dir = settings.ECP_PATH + \
                          self.ecp_structure.get(u_name).get('ep_path') + '/'
            else:
                logging.error('ЭП с имененем ключевого контейнера %s не найдено' % (u_name,))
                sys.exit(1)
        else:
            logging.error('Режим работы программы %s не поддерживается' % (self.mode,))
            sys.exit(1)
        dst_dir = settings.FLASH_PATH + ':'
        for fs_item in os.listdir(src_dir):
            file_path = os.path.join(src_dir, fs_item)
            if os.path.isdir(file_path):
                # если элемент ФС является каталогом
                shutil.copytree(file_path, dst_dir + fs_item, ignore=None)
            else:
                # если элемент ФС является файлом
                shutil.copy2(file_path, dst_dir)

        return None

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
                            '-pinsrc', '',
                            '-contdest', dst_cont,
                            '-pindest', ''
                            ]
            pipe = subprocess.Popen(big_array_list, shell=True, stdout=subprocess.PIPE)
            raw_string = pipe.stdout.read().decode('UTF-8', 'ignore')
            print('raw_string', raw_string)

        else:
            print('Поддержка программы csptest версии %s не реализована' % (self.ver, ))
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
            print('Поддержка программы csptest версии %s не реализована' % (self.ver, ))
            sys.exit(1)


    def list_key_conteyners(self):
        """Перечисляет список установленных физических контейнеров (флешки, дискеты, етокены)
            Возвращает значение в виде \\.\FAT12_F\TExpressEx_2015_05_21_16_09_01
        """        
        # "C:\Program Files (x86)\Crypto Pro\CSP\csptest" -keyset -enum_containers -verifycontext -fqcn  -machinekeys
        
        if self.ver == '3.9':
            key_list = [    self.distr_path, 
                            '-keyset',
                            '-enum_containers', 
                            '-verifycontext', 
                            '-fqcn',
                            '-machinekeys',
                            ]
            pipe = subprocess.Popen(key_list, shell=True, stdout=subprocess.PIPE)
            raw_string = pipe.stdout.read().decode('UTF-8', 'ignore')
            result = re.findall(r'(\\.*)\r\n', raw_string, re.MULTILINE)
            return result
        elif self.ver == '4.0':
            #  csptest.exe -keyset -enum_containers -verifycontext  -fqcn
            key_list = [    self.distr_path, 
                            '-keyset',
                            '-enum_containers', 
                            '-verifycontext', 
                            '-fqcn',
                            ]
            pipe = subprocess.Popen(key_list, shell=True, stdout=subprocess.PIPE)
            raw_string = pipe.stdout.read().decode('UTF-8', 'ignore')
            result = re.findall(r'(\\.*)\r\n', raw_string, re.MULTILINE)
            return result
        else:
            print('Поддержка программы csptest версии %s не реализована' % (self.ver, ))
            sys.exit(1)
        
    def choose_conteyner(self):
        """Выбор нужного ключевого контейнера
        """
        res = self.list_key_conteyners()
        search_pat = 'FAT12_' + settings.FLASH_PATH.upper()
        for elem in res:
            if re.search(search_pat , elem):
                return elem
        return None
    
    def __del__(self):
        """Очищаем за собой флешку от ненужных файлов.
        """
        self.clear_flash()
