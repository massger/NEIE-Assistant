#!/usr/bin/python
# coding=utf-8
import xml.etree.ElementTree as ET

from library import library
from library import requests


class learn_rwt:
    def __init__(self, path, username, password, level):
        self.path = path
        self.username = username
        self.password = password
        self.level = level
        self.available = 0

    def __encode_object(self, obj):
        for name in obj:
            obj[name] = library.encode(obj[name])
        return obj

    def __decode_object(self, obj):
        for name in obj:
            obj[name] = library.decode(obj[name])
        return obj

    def __xml(self, method, head, data):
        xml = '''<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
  <soap:Header>
    <CredentialSoapHeader xmlns="http://www.open.com.cn">
'''
        xml += '      <Username>' + head['Username'] + '</Username>\n'
        xml += '      <Password>' + head['Password'] + '</Password>\n'
        xml += '''      <ClientCredential>83BCC79913F2331685F4851C4ED2DA72  E37438347941F22F6A873D18CE562AC9</ClientCredential>
    </CredentialSoapHeader>
  </soap:Header>
  <soap:Body>
'''
        xml += '    <' + method + ' xmlns="http://www.open.com.cn">\n'
        for name in data:
            xml += '      <' + name + '>' + data[name] + '</' + name + '>\n'
        xml += '    </' + method + '>\n'
        xml += '''  </soap:Body>
</soap:Envelope>
'''
        return xml

    def __check_connect(self):
        if self.available == 0:
            try:
                r = requests.get('http://' + self.path + '/WebService/ServiceV3.asmx?WSDL',
                                 headers={'Content-Type': 'application/x-www-form-urlencoded'})
                text = r.text
                if text.find('LoginReadingResponse') != -1:
                    self.available = 1
            except:
                library.fail('fail to connect server: ' + self.path)
                exit()
        return

    def __sopa_post(self, method, body):
        head = {'Username': self.username, 'Password': self.password}
        self.__encode_object(head)

        headers = {'Content-Type': 'text/xml; charset=utf-8', 'SOAPAction': 'http://www.open.com.cn/' + method}
        payload = self.__xml(method, head, body)

        r = requests.post('http://' + self.path + '/WebService/ServiceV3.asmx', headers=headers, data=payload)
        root = ET.fromstring(r.text)
        result = {}
        body = root[0][0]
        for child in body:
            if child.text != None:
                result[child.tag[24:]] = child.text
        return result

    def LoginReading(self):
        self.__check_connect()
        data = {'UserName': self.username, 'Password': self.password, 'Version': '5.0', 'LevelID': self.level}
        self.__encode_object(data)

        result = self.__sopa_post('LoginReading', data)

        self.__decode_object(result)
        # result['ReturnMessage'] = result['ReturnMessage'].decode('gbk')
        # result['ReturnMessage'] = result['ReturnMessage']

        try:
            self.UserID = result['UserID']
            self.UserNumber = result['UserNumber']
        except:
            pass
        return result

    def GetReadingProgress(self):
        self.__check_connect()
        data = {}
        data['UserID'] = self.UserID
        data['LevelID'] = self.level

        result = self.__sopa_post('GetReadingProgress', data)

        try:
            self.UnitID = result['UnitID']
        except:
            self.UnitID = '1'

        try:
            self.SectionID = result['SectionID']
        except:
            self.SectionID = self.level + self.UnitID + '21'
        return result

    def SetReadingUnitLearnStaus(self, status):
        self.__check_connect()
        data = {}
        data['UserID'] = self.UserID
        data['LevelID'] = self.level
        data['UnitID'] = self.UnitID
        data['Status'] = status
        self.__encode_object(data)

        result = self.__sopa_post('SetReadingUnitLearnStaus', data)

        self.__decode_object(result)
        return result

    def GetServerTime(self):
        self.__check_connect()
        data = {}

        result = self.__sopa_post('GetServerTime', data)

        self.BeginTime = result['GetServerTimeResult']
        return result

    def SetReadingResponseInformation(self, Score, IsCompleted):
        self.__check_connect()
        data = {}
        data['UserID'] = self.UserID
        data['UserNumber'] = self.UserNumber
        data['SectionID'] = self.SectionID
        data['Response'] = ''
        data['Score'] = Score
        data['IsSaveResponse'] = '1'
        data['IsCompleted'] = IsCompleted
        data['BeginTime'] = self.BeginTime
        self.__encode_object(data)

        result = self.__sopa_post('SetReadingResponseInformation', data)

        self.__decode_object(result)
        return result

    def SetReadingUserActiveInfo(self, SerialNumber, LicenseNumber, ActivationCode):
        self.__check_connect()
        data = {}
        data['UserID'] = self.UserID
        data['LevelID'] = self.level
        data['SerialNumber'] = SerialNumber
        data['LicenseNumber'] = LicenseNumber
        data['ActivationCode'] = ActivationCode
        data['IsActive'] = '2'
        self.__encode_object(data)

        result = self.__sopa_post('SetReadingUserActiveInfo', data)

        self.__decode_object(result)
        result['ReturnMessage'] = result['ReturnMessage'].decode('gbk')
        return result


def active(learn, SerialNumber, LicenseNumber, ActivationCode):
    result = learn.LoginReading()
    status = result['LoginReadingResult']
    if status == '2':
        library.warning('user ' + learn.username + ' have been actived')
        return '1'
    elif status != '1':
        if result['ReturnMessage'].find('Activation') == -1:
            library.fail('user ' + learn.username + ' login failed: ' + result['ReturnMessage'])
            exit()

    result = learn.SetReadingUserActiveInfo(SerialNumber, LicenseNumber, ActivationCode)
    status = result['SetReadingUserActiveInfoResult']
    if status == '1':
        library.success('user ' + learn.username + ' active successfully')
    else:
        library.fail('user ' + learn.username + ' active failed: ' + result['ReturnMessage'])
        exit()
    return status


def login(learn):
    result = learn.LoginReading()
    status = result['LoginReadingResult']
    if status == '1':
        library.warning('user ' + learn.username + ' need activation')
        exit()
    elif status != '2':
        library.fail('user ' + learn.username + ' login failed: ' + result['ReturnMessage'])
        exit()
    else:
        library.success('user ' + learn.username + ' login successfully')
    return status


def get_progress(learn):
    result = learn.GetReadingProgress()
    status = result['GetReadingProgressResult']
    return status


def update_unit(learn):
    result = learn.SetReadingUnitLearnStaus('1')
    status = result['SetReadingUnitLearnStausResult']
    if status == '1':
        library.success('update unit learn status success: unit ' + learn.UnitID)
    else:
        library.fail('update unit learn status fail: unit ' + learn.UnitID)
        exit()
    return status


def end_section(learn, score):
    if int(score) == score:
        score_str = "%d" % int(score)
    else:
        score_str = "%.1f" % score
    result = learn.SetReadingResponseInformation(score_str, '1')
    status = result['SetReadingResponseInformationResult']
    if status == '1':
        library.success('ended section ' + learn.SectionID + ' successfully: score ' + score_str)
    else:
        library.fail('ended section ' + learn.SectionID + ' failed')
        # Retry login
        status = login(learn)
        # Retry set response
        result = learn.SetReadingResponseInformation(score_str, '1')
        status = result['SetReadingResponseInformationResult']
        if status == '1':
            library.success('ended section ' + learn.SectionID + ' successfully: score ' + score_str)
        else:
            library.fail('ended section ' + learn.SectionID + ' failed twice')
            exit()
    return status


def start_section(learn):
    result = learn.SetReadingResponseInformation('0', '0')
    status = result['SetReadingResponseInformationResult']
    if status == '1':
        library.success('started section ' + learn.SectionID + ' successfully')
    else:
        library.fail('started section ' + learn.SectionID + ' failed')
        exit()
    return status
