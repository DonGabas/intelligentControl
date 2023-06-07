###############################################################
###
###       Control neuronal por modelo interno
###
###############################################################
import planta
import tclab
import numpy as np
import time
import matplotlib.pyplot as plt
import pandas as pd # manipulación y análisis de datos
import statistics
import tensorflow as tf
from tensorflow import keras
from scipy.signal import savgol_filter
import random

###############

OFF = 0

###############
##########################################

run_time = 40.0                            # Tiempo de ejecución en minutos
sp1 = 40.1                                  # Setpoint temp
sp2 = 34.0 
sp3 = 30.8

t_min = 21.0                                # temperaturas de escalado
t_max = 55.0


ruta = '/home/arwen/Documentos/PG/Python/Vs/DisipadoraI/'
nombre = "control_RNA_IMC_vs_3spI.csv"
model_I_cargar = 'RN_entrenadas/ident_arx_mlp_8-4-2-1_LR-R_sc_v1.h5'
model_C_cargar = 'RN_entrenadas/ModInvPlus_mlp_9-4-2-1_L-L_sc_v2.h5'
##########################################
# Conecta con Arduino
a = tclab.TCLab()
# Simulacion de planta arduino
#a = planta.Planta()

ta = a.T                                   # temperatura ambiente
ta_sc = (ta-t_min)/(t_max-t_min)            # temperatura ambiente escalada

print()
print("Calefactor bajo control IMC ")
print('-'*35)

loops = int(60.0*run_time)                      # número de ciclos
tm = np.zeros(loops)                            # vector de tiempo
dtV = np.zeros(loops)

T = np.ones(loops) * ta_sc                        # Temperatura esclada (Celsius)
T_RN = np.ones(loops) * T[0]                      # Temperatura de la RN 
retraso = np.ones(16) * T[0]

escalonRef = np.ones(loops) * ta
escalonRef[int(10):int(20*60)] = sp1
escalonRef[int(20*60):int(40*60)] = sp2
#escalonRef[int(40*60):int(60*60)] = sp3
escalonRef = (escalonRef - t_min) / (t_max-t_min)                      # escalado


# Grafica de las referencias a seguir
plt.figure()
plt.plot(escalonRef, 'b')
plt.xlabel('Tiempo discreto')
plt.ylabel('Aplitud')
plt.show()
#################################################################

NivelQ = np.ones(loops) * OFF                   # vector de potencia del calentador
Error = np.ones(5)*escalonRef[0]

ref = 0.0                                       # setpoin
u = u1 = u2 = u3 = u4 = 0.0                     # señal de control
y = y1 = y2 = y3 = y4 = ta_sc                   # sal del calefactor
y11 = y22 = y33 = y44 = ta_sc                   # sal del RN calefactor
error = 0.0                                     # diferencia entre la simulacion y el calefactor
#Error = np.zeros(30)
######################################################
# Cagar controlador
controlador = keras.models.load_model(model_C_cargar)
print()
print(model_C_cargar," Controlador neuronal cargado")
controlador.summary()
# Cagar planta calefactor
calefactor = keras.models.load_model(model_I_cargar)
print()
print(model_I_cargar," Red neuronal calefactor cargada")
calefactor.summary()
######################################################

print('Corriendo ciclo principal. Ctrl-C to end.')
print(' Tiempo  Control     Ref      Trn      T')
print('{:6.1f}  {:6.2f}     {:6.2f}   {:6.2f}  {:6.2f}'.format(tm[0], \
                                                       NivelQ[0], \
                                                        escalonRef[0]*34+21.0, \
                                                        T_RN[0]*34+21.0, \
                                                       T[0]*34+21.0))


# para salvar los datos
df = pd.DataFrame()
df['tiempo'] = None
df = df.assign(temp=None)
df = df.assign(clft=None)
df = df.assign(refer=None)

# Ciclo principal
start_time = time.time()
prev_time = start_time

ref_ = escalonRef[0]
cambio = False
r = 60
try:
    for i in range(1,loops):
        # Sleep time
        sleep_max = 1.0
        sleep = sleep_max - (time.time() - prev_time)       # tiempor entre ** y ahora
        if sleep>=0.01:
            time.sleep(sleep)
        else:
            time.sleep(0.01)

        # Tiempo de registro y cambio en el tiempo
        t = time.time()
        dtV[i] = t - prev_time
        prev_time = t               # **
        tm[i] = t - start_time

        #########################################################


        #########################################################
        
        if cambio:
            ref = escalonRef[i]
        else:
            ref = escalonRef[i] + np.mean(Error)
        Error = np.roll(Error, 1)
        X_in = np.array([y1, y2, y3, y4 , u1, u2, u3, u4, ref])     # ENTRADA DE RN: setpoint y dos entradas pasadas de y y u
        X_in.shape = (1,9)

        #########################################################

        U = controlador.predict(X_in,verbose=False)

        #########################################################

        u = max(0.0, min(float(U), 1.0))                          # limitacion de u ( entre 0 y 4 v / 100 % )

        if escalonRef[i] < ((ta+1.0 - t_min) / (t_max-t_min)):
            u = OFF
        
        a.Q(u*100.0)                                                      # manipulacion del calefactor
        NivelQ[i] = a.Q()                                                 # lectura de potencia usada

        T[i] = ((round(a.T,2) - t_min) / (t_max-t_min))                   # Leer temperatura y escalarla

        if ref_ != escalonRef[i]:
            cambio = True
        if cambio:
            if (abs(escalonRef[i]-T[i])*34) > 0.5:
                r = 2
            else:
                r = 600
                cambio = False
        
        if i%r == 0:
            U_in = np.array([u1, u2, u3, u4 , y1, y2, y3, y4])
        else:
            U_in = np.array([u1, u2, u3, u4 , y11, y22, y33, y44])

        U_in.shape = (1,8)
        
        #retraso = np.roll(retraso, 1)
        #retraso[0] = round(float(calefactor.predict(U_in,verbose=False)),5)                     # Simular planta
        #T_RN[i] = retraso[15]                                                   # Simular retraso
        T_RN[i] = round(float(calefactor.predict(U_in,verbose=False)),5)                        # Simular planta

        #########################################################
        # Actualizacion
        y1 = y2
        y2 = y3
        y3 = y4
        y4 = T[i]
        y11 = y22
        y22 = y33
        y33 = y44
        y44 = float(T_RN[i])                                                      
        u1 = u2
        u2 = u3
        u3 = u4
        u4 = u
        Error[0] = float(T_RN[i]) - T[i]
        Error = savgol_filter(Error, 5, 3)
        ref_ = escalonRef[i]
        #########################################################

        # Mostrar datos
        print('{:6.1f}  {:6.2f}     {:6.2f}   {:6.2f}  {:6.2f}'.format(tm[i], \
                                                               NivelQ[i], \
                                                                escalonRef[i]*34+21.0, \
                                                                T_RN[i]*34+21.0, \
                                                               T[i]*34+21.0))
        """print("                                                    ",round(u1,2),"  ",round(u2,2),"  ",round(u3,2),"  ",round(u4,2),
        "  ",round(y1,2),"  ",round(y2,2),"  ",round(y3,2),"  ",round(y4,2),
        "  ",round(y11,2),"  ",round(y22,2),"  ",round(y33,2),"  ",round(y44,2))"""


    # Apagar calefactor
    a.Q(OFF)

    # Escalado
    T = T*(t_max-t_min) + t_min
    escalonRef = escalonRef*(t_max-t_min) + t_min

    # Salvar en un archivo de texto
    df['tiempo'] = tm
    df['temp'] = T
    df['clft'] = NivelQ
    df['refer'] = escalonRef
    df.to_csv(ruta+nombre)
        
# Si el bicle se finaliza con Ctrl-C           
except KeyboardInterrupt:
    # Desconectar de Arduino
    a.Q(OFF)
    print('Apagar')
    a.close()
    df['tiempo'] = tm
    df['temp'] = T
    df['clft'] = NivelQ
    df['refer'] = escalonRef
    df.to_csv(ruta+nombre)
    
# Asegurando que la conexión en serie aún se cierre cuando haya un error
except:           
    # Desconectar de Arduino
    a.Q(OFF)
    print('Error: Apagando')
    a.close()
    df['tiempo'] = tm
    df['temp'] = T
    df['clft'] = NivelQ
    df['refer'] = escalonRef
    df.to_csv(ruta+nombre)
    raise
