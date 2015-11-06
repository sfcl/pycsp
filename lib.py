#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import sys, os, re, shutil
import subprocess

import settings

class Installer(object):
    """Установщик ЭЦП в реестр КриптоПРО
    """
    def __init__(self):
        self.current_path = os.path.dirname(os.path.abspath(__file__))
        self.ver = ''
        self.select_number = 0
        self.dp = self.search_distrib()
        
        if not self.dp :
            self.send_error('Программа КриптоПРО не установлена!')
            sys.exit(1)
            return

        self.ver = self.get_version()
        self.ecps = self.get_list_ecp(search_path=settings.ECP_PATH)
        
        # получить список найденых закрытых контейнеров ЭП 
        self.print_list_ecp()

        # предложение пользователю ввести номер
        self.input_number()

        # подготивительные действия к установке ЭП
        self.clear_flash() # очищаем флешку от старых контейнеров
        self.copy_ecp()


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
            print('Каталог %s с ЭП пуст. Устанавливать нечего!' % (search_path, ))
            sys.exit(1)

        temp_dict = {}
        counter = 1
        for elem in ld:
            temp_dict[counter] = elem
            counter += 1
        temp_dict['len'] = counter - 1

        return temp_dict
        
    def print_list_ecp(self):
        """Распечатка списка закрытых контейнеров и сертификатов
        """    
        for inx in range(1, self.ecps['len'] + 1):
            print('%s : %s' % (inx, self.ecps[inx]))
        
    def send_error(self, message):
        """Сообщить о ошибке
        """
        print(message)
        return

    def input_number(self):
        """Примитивный диалог взаимодействия с пользователем
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

    def get_version(self):
        """Получить версию программы csptest
        """
        if self.path_exist(dir_path='./bin/sigcheck.exe'):
            pass
        else:
            self.send_error('Не найдена программа sigcheck. Дальнейшее продолжение невозможно.')
            sys.exit(1)
        
        pipe = subprocess.Popen([ self.current_path + '\\bin\\' + 'sigcheck.exe', '-q' , self.dp], shell=True, stdout=subprocess.PIPE)
        raw_string = pipe.stdout.read().decode('UTF-8')

        result = re.findall("Prod version:\s+(.*)\r\n", raw_string, re.MULTILINE)
        result = result[0]

        # выбираем первые две цифры в названии
        result = result.split('.')
        result = result[0:2]
        result = '.'.join(result)
        return result

    def clear_flash(self):
        """Очищаем флешку от старых ЭП
        """
        folder = settings.FLASH_PATH
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
        """Производим копирование закрытого контейнера на флеш
        """
        src_dir = settings.ECP_PATH + self.ecps[self.select_number] + '/'
        dst_dir = settings.FLASH_PATH
        for fs_item in os.listdir(src_dir):
            file_path = os.path.join(src_dir, fs_item)
            if os.path.isdir(file_path):
                # если элемент ФС является каталогом
                #pass
                shutil.copytree(file_path, dst_dir + fs_item, ignore=None)
            else:
                # если элемент ФС является файлом
                shutil.copy2(file_path, dst_dir)
            #print(file_path)

        
        
        #return


if __name__ == '__main__':
    ins = Installer()
    #print(ins.search_distrib())