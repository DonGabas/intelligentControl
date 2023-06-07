###############################################################
###
###       Funcionamiento de calefactor bajo escalon
###
###############################################################

import numpy as np
import time
import matplotlib.pyplot as plt
import pandas as pd
import statistics
import tclab

###############

OFF = 0

###############
##########################################

Q1 = 47.4                  # Nivel de potencia
Q2 = 75.3
Q3 = 18.1
run_time = 120.0           # Tiempo de ejecución en minutos
t_off = 10
ruta = '/home/USER/Documentos/PG/Python/Calefactor/Adquisicion/'
nombre = "NAME.csv"

##########################################
# Conecta con Arduino
a = tclab.TCLab()

print()
print("Calefactor bajo escalón al ",Q1," % de potencia")
print('-'*24)

loops = int(60.0*run_time)          # número de ciclos
tm = np.zeros(loops)                # vector de tiempo
dtV = np.zeros(loops)

T = np.ones(loops) * a.T            # Temperatura (Celsius)

# escalón (0 - 100%)
escalon = np.ones(loops) * OFF
escalon[600:1800] = Q1
escalon[1800:3600] = Q2
escalon[3600:5400] = Q3

#############################
NivelQ = np.ones(loops) * OFF       # vector de potencia del calentador
ct = OFF                            # comparador de cambio en el escalon

plt.figure()
plt.plot(escalon, 'b')
plt.xlabel('Tiempo discreto')
plt.ylabel('Amplitud')
plt.show()

print('Corriendo ciclo principal. Ctrl-C to end.')
print(' Tiempo   NivelQ      T')
print('{:6.1f} {:6.2f} {:6.2f}'.format(tm[0], \
                                                       NivelQ[0], \
                                                       T[0]))


# para salvar los datos
df = pd.DataFrame()
df['tiempo'] = None
df = df.assign(temp=None)
df = df.assign(clft=None)

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
                    
        # Leer temperatura 
        T[i] = a.T

        if ct != escalon[i]:
            a.Q(escalon[i])
        
        ct = escalon[i]
        NivelQ[i] = a.Q()

        # Mostrar datos
        print('{:6.1f} {:6.2f} {:6.2f}'.format(tm[i], \
                                                               NivelQ[i], \
                                                               T[i]))


    # Apagar calefactor
    a.Q(OFF)

    # Salvar en un archivo de texto
    df['tiempo'] = tm
    df['temp'] = T
    df['clft'] = NivelQ
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
    df.to_csv(ruta+nombre)
    raise
