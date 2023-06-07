###############################################################
###
###       Control difuso
###
###############################################################
import planta
import tclab
import numpy as np
import time
import matplotlib.pyplot as plt
import pandas as pd 
import statistics
from scipy.signal import savgol_filter
import fuzzyc

###############

OFF = 0

###############
##########################################

run_time = 40.0                            # Tiempo de ejecución en minutos
sp1 = 44.3                                # Setpoint temp
sp2 = 33.3 
sp3 = 30.8
#sp4 = 26.5

ruta = '/home/USER/Documentos/PG/Python/Fuzzy/'
nombre = "XXX_LD.csv"
##########################################
# Conecta con Arduino
a = tclab.TCLab()

print()
print("Calefactor bajo control difuso ")
print('-'*35)

loops = int(60.0*run_time)                      # número de ciclos
tm = np.zeros(loops)                            # vector de tiempo
dtV = np.zeros(loops)

ta = a.T                                        # Temperatura ambiente 60
T = np.ones(loops) * ta                         # Temperatura esclada (Celsius)

escalonRef = np.ones(loops) * ta
escalonRef[int(15):int(40*60)] = sp1
escalonRef[int(20*60):int(40*60)] = sp2
escalonRef[int(40*60):int(60*60)] = sp3
#escalonRef[int(45*30):int(60*30)] = sp4

# Grafica de las referencias a seguir
plt.figure()
plt.plot(escalonRef, 'b')
plt.xlabel('Tiempo discreto')
plt.ylabel('Aplitud')
plt.show()
#################################################################

NivelQ = np.ones(loops) * OFF                   # vector de potencia del calentador
filtro = np.ones(11)*escalonRef[0]

error = 0.0                                     # error entre ref y temp
error_a = 0.0                                   # error instante anterior
delta_e = 0.0                                   # tasa de cambio del error: delta_error/delta_tiempo

factor_e = 0.0
factor_c = 0.0
error_ = 0.0
######################################################
# Creacion del controlador difuso
controlador = fuzzyc.FuzzyC()

######################################################

print('Corriendo ciclo principal. Ctrl-C to end.')
print(' Tiempo  Control     Ref     error   delta    T')
print('{:6.1f}  {:6.2f}     {:6.2f}  {:6.2f}  {:6.2f}   {:6.2f}'.format(tm[0], \
                                                       NivelQ[0], \
                                                        escalonRef[0], \
                                                        error, \
                                                        delta_e, \
                                                       T[0]))


# para salvar los datos
df = pd.DataFrame()
df['tiempo'] = None
df = df.assign(temp=None)
df = df.assign(clft=None)
df = df.assign(refer=None)

# Ciclo principal
start_time = time.time()
prev_time = start_time
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

        T[i] = round(a.T,2)
        filtro[0] = T[i]                            # Leer temperatura
        filtro = savgol_filter(filtro, 11, 3)
        #T_aux = filtro[0]
        T_aux = np.mean(filtro)
        filtro = np.roll(filtro, 1)

        #########################################################

        error = escalonRef[i] - T_aux
        error = max(-34.99, min(error, 35))
        delta_e = error - error_a
        delta_e = max(-2, min(delta_e, 2))

        #########################################################

        if escalonRef[i] > 42.0:
            factor_e = escalonRef[i]*0.16 - 6.16
            factor_c = 10.0
            if escalonRef[i] > 52.0:
                factor_c = factor_c  + 10.0
        else:
            if escalonRef[i] < 30.0:
                factor_c = -5.0
            else:
                factor_e = factor_c = 0.0
        
        error_ = error + factor_e
        
        U = controlador(error_,delta_e) + factor_c
        U = max(0.0, min(U, 100.0))
        if escalonRef[i] <= ta+1.5:
            U = 0

        #########################################################
  
        a.Q(U)                                                            # manipulacion del calefactor
        NivelQ[i] = a.Q()                                                 # lectura de potencia usada     

        #########################################################
        # Actualizacion
        error_a = error

        #########################################################

        # Mostrar datos
        print('{:6.1f}  {:6.2f}     {:6.2f}  {:6.2f}  {:6.2f}   {:6.2f}'.format(tm[i], \
                                                               NivelQ[i], \
                                                                escalonRef[i], \
                                                                error, \
                                                                delta_e, \
                                                               T[i]))

    # Apagar calefactor
    a.Q(OFF)

    # Salvar en un archivo de texto
    df['tiempo'] = tm
    df['temp'] = T
    df['clft'] = NivelQ
    df['refer'] = escalonRef
    #df.to_csv(ruta+nombre)
        
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
    #df.to_csv(ruta+nombre)
    
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
    #df.to_csv(ruta+nombre)
    raise
