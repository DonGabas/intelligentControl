#!/usr/bin/env python3
# Version modificada de TCLab ==> Drogon. ( Arquitectura de calentador diferente )
# -*- coding: utf-8 -*-

from __future__ import print_function
import time
import os
import random
import serial
from serial.tools import list_ports
from .labtime import labtime
from .version import __version__


sep = ' '   # command/value separator in Drogon-sketch firmware

arduinos = [('USB VID:PID=16D0:0613', 'Arduino Uno'),
            ('USB VID:PID=1A86:7523', 'NHduino'),
            ('USB VID:PID=2341:8036', 'Arduino Leonardo'),
            ('USB VID:PID=2A03', 'Arduino.org device'),
            ('USB VID:PID', 'unknown device'),
            ]

_sketchurl = 'Buscar Drogon-sketch.ino'
_connected = False


def clip(val, lower=0, upper=100):
    """El valor límite debe estar entre los límites inferior y superior"""
    return max(lower, min(val, upper))


def command(name, argument, lower=0, upper=100):
    """Comando de construcción para Drogon-sketch."""
    return name + sep + str(clip(argument, lower, upper))


def find_arduino(port=''):
    """Localiza Arduino y devuelve el puerto y el dispositivo."""
    comports = [tuple for tuple in list_ports.comports() if port in tuple[0]]
    for port, desc, hwid in comports:
        for identifier, arduino in arduinos:
            if hwid.startswith(identifier):
                return port, arduino
    print('--- Serial Ports ---')
    for port, desc, hwid in list_ports.comports():
        print(port, desc, hwid)
    return None, None


class AlreadyConnectedError(Exception):
    pass


class TCLab(object):
    def __init__(self, port='', debug=False):
        global _connected
        self.debug = debug
        print("")
        print("Version", __version__)
        self.port, self.arduino = find_arduino(port)
        if self.port is None:
            raise RuntimeError('Dispositivo Arduino no encontrado.')

        try:
            self.connect(baud=38400)
        except AlreadyConnectedError:
            raise
        except:
            try:
                _connected = False
                self.sp.close()
                self.connect(baud=9600)
                print('No se pudo conectar a alta velocidad, pero se logró a baja velocidad.')
                print('Nuevo firmware Arduino disponible en:')
                print(_sketchurl)
            except:
                raise RuntimeError('No se pudo conectart.')

        self.sp.readline().decode('UTF-8')
        self.version = self.send_and_receive('VER')
        if self.sp.isOpen():
            print(self.arduino, 'conectado en el puerto', self.port,
                  'en', self.baud, 'baud.')
            print(self.version + '.')
        labtime.set_rate(1)
        labtime.start()
        self._P = 204.0
        self.sources = [('T', self.scan),
                        ('Q', None),
                        ]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return

    def connect(self, baud):
        """Establecer conexión con arduino

        baud: baud rate"""
        global _connected

        if _connected:
            raise AlreadyConnectedError('Ya tienes una conexión abierta')

        _connected = True

        self.sp = serial.Serial(port=self.port, baudrate=baud, timeout=2)
        time.sleep(2)
        self.Q(0)  # falla si no está conectado
        self.baud = baud

    def close(self):
        """Apaga el dispositivo y cierra la conexión en serie."""
        global _connected

        self.Q(0)
        self.send_and_receive('X')
        self.sp.close()
        _connected = False
        print('Se desconectó con éxito.')
        return

    def send(self, msg):
        """Enviar un mensaje de cadena al firmware."""
        self.sp.write((msg + '\r\n').encode())
        if self.debug:
            print('Sent: "' + msg + '"')
        self.sp.flush()

    def receive(self):
        """Devolver un mensaje de cadena recibido del firmware."""
        msg = self.sp.readline().decode('UTF-8').replace('\r\n', '')
        if self.debug:
            print('Return: "' + msg + '"')
        return msg

    def send_and_receive(self, msg, convert=str):
        """Envia un mensaje de cadena y devuelve la respuesta"""
        self.send(msg)
        return convert(self.receive())

    def LED(self, val=100):
        """Configura LED a un brillo especificado durante 10 segundos."""
        return self.send_and_receive(command('LED', val), float)

    @property
    def T(self):
        """Devuelve un float que indica la temperatura T en Celsius."""
        return self.send_and_receive('T', float)

    @property
    def P(self):
        """Devuelve un float que indica la potencia del calentador en pwm."""
        return self._P

    @P.setter
    def P(self, val):
        """Establece la maxima potencia del calentador en pwm, rango 0 a 255."""
        self._P = self.send_and_receive(command('P', val, 0, 255), float)

    def Q(self, val=None):
        """Obtener o configura la potencia del calentador

        val:Valor de potencia del calentador, el rango está limitado a 0-100

        devolver valor recortado."""
        if val is None:
            msg = 'R'      # lectura de potencia
        else:
            msg = 'Q' + sep + str(clip(val))
        return self.send_and_receive(msg, float)

 
    def scan(self):
        #self.send('SCAN')
        T = self.T  # float(self.receive())
        Q = self.Q()  # float(self.receive())
        return T, Q

    # Define propiedades para Q
    U1 = property(fget=Q, fset=Q, doc="Heater value")


class TCLabModel(object):
    def __init__(self, port='', debug=False, synced=True):
        self.debug = debug
        self.synced = synced
        print("Version", __version__)
        labtime.start()
        print('Simulated Calefactor')
        self.Ta = 23                  # temperatura ambiente
        self.tstart = labtime.time()  # start time
        self.tlast = self.tstart      # last update time
        self._P = 204.0              # maxima potencia del calentador 80% (limitada. max es 255)
        self._Q = 0                  # valor inicial del calentador
        self._T = self.Ta            # temperatura del termistor
        self._H = self.Ta            # temperatura del calentador
        self.maxstep = 0.2            # paso de tiempo máximo para la integración
        self.sources = [('T', self.scan),
                        ('Q', None),
                        ]

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return

    def close(self):
        """Simular el apagado del dispositivo calefactor."""
        self.Q(0)
        print('Modelo del calefactor desconectado con éxito.')
        return

    def LED(self, val=100):
        """Simula encendido LED

           val : especifica brillo (default 100). """
        self.update()
        return clip(val)

    @property
    def T(self):
        """Devuelve un float que indica la temperatura del calentador en Celsius."""
        self.update()
        return self.measurement(self._T)

    @property
    def P(self):
        """Devuelve un float que indica la potencia del calentador en pwm."""
        self.update()
        return self._P

    @P.setter
    def P(self, val):
        """Establece la maxima potencia del calentador en pwm, rango 0 a 255."""
        self.update()
        self._P = clip(val, 0, 255)

    def Q(self, val=None):
        """Obtener o configura la potencia del calentador

        val:Valor de potencia del calentador, el rango está limitado a 0-100

        devolver valor recortado."""
        self.update()
        if val is not None:
            self._Q = clip(val)
        return self._Q

    def scan(self):
        self.update()
        return (self.measurement(self._T),
                self._Q)

    # Define propiedades para Q
    U1 = property(fget=Q, fset=Q, doc="Heater 1 value")

    def quantize(self, T):
        """cuantifica las temperaturas del modelo para imitar la conversión A/D de Arduino."""
        return max(-50, min(132.2, T - T % 0.3223))

    def measurement(self, T):
        return self.quantize(T + random.normalvariate(0, 0.043))

    def update(self, t=None):
        if t is None:
            if self.synced:
                self.tnow = labtime.time() - self.tstart
            else:
                return
        else:
            self.tnow = t

        teuler = self.tlast

        while teuler < self.tnow:
            dt = min(self.maxstep, self.tnow - teuler)
            DeltaTaH = self.Ta - self._H
            DeltaT = self._H
            dH = self._P * self._Q / 5720 + DeltaTaH / 20 - DeltaT / 100
            dT = (self._H - self._T)/140

            self._H += dt * dH
            self._T += dt * dT
            teuler += dt

        self.tlast = self.tnow


def diagnose(port=''):
    def countdown(t=10):
        for i in reversed(range(t)):
            print('\r' + "Countdown: {0:d}  ".format(i), end='', flush=True)
            time.sleep(1)
        print()

    def heading(string):
        print()
        print(string)
        print('-'*len(string))

    heading('Comprobando la conexión')

    if port:
        print('Buscando Arduino en {} ...'.format(port))
    else:
        print('Buscando Arduino en algun puerto...')
    comport, name = find_arduino(port=port)

    if comport is None:
        print('No se encontró ningún Arduino conocido en los puertos enumerados anteriormente.')
        return

    print(name, 'encontrado en puerto', comport)

    heading('Probando el objeto en modo de depuración')

    with TCLab(port=port, debug=True) as lab:
        print('Leyendo temperatura')
        print(lab.T)

    heading('Probando las funciones')

    with TCLab(port=port) as lab:
        print('Probando el LED. Debería encenderse por 10 seg.')
        lab.LED(100)
        countdown()

        print()
        print('Leyendo temperatura')
        T = lab.T
        print('T = {} °C'.format(T))

        print()
        print('Escribir valor fraccionario al calentador...')
        try:
            Q = lab.Q(0.5)
        except:
            Q = -1.0
        print("Escribimos Q = 0.5 y leemos Q =", Q)

        if Q != 0.5:
            print("El firmware ({}) no soporta"
                  "valores fraccionados.".format(lab.version))
            print("You need to upgrade to at least version 1.4.0 for this:")
            print(_sketchurl)

        print()
        print('Ahora se encenderá el calefactor al 100%, espera 30 segundos '
              'y observe si la temperatura ha subido. ')
        lab.Q(100)
        countdown(30)

        print()
        def tempcheck(name, T_initial, T_final):
            print('{} comenzó en {} °C y finalizaó en {} °C'
                  .format(name, T_initial, T_final))
            if T_final - T_initial < 0.8:
                print('La temperatura subió menos de lo esperado.')
                print('Revise el suministro de energ;ia del calefactor.')

        T_final = lab.T

        tempcheck('T', T, T_final)

        print()
        heading("Comprobación de rendimiento")
        print("Esta parte comprueba qué tan rápido es su unidad")
        print("Se leerá T lo más rápido posible")

        start = time.time()
        n = 0
        while time.time() - start < 10:
            elapsed = time.time() - start + 0.0001  # avoid divide by zero
            T = lab.T
            n += 1
            print('\rTiempo transcurrido: {:3.2f} s.'
                  ' Número de lecturas: {}.'
                  ' Tasa de muestreo: {:2.2f} Hz'.format(elapsed, n, n/elapsed),
                  end='')

        print()

    print()
    print('Diagnóstico completado')
