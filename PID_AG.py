import planta
import tclab
import numpy as np
import time
import matplotlib.pyplot as plt
from scipy.integrate import odeint
import pandas as pd

###############

OFF = 0.0

###############
##########################################

run_time = 40.0                            # Tiempo de ejecución en minutos
sp1 = 42.0                                # Setpoint temp
sp2 = 35.6 
sp3 = 30.8
#sp4 = 55.0


ruta = '/home/USER/Documentos/PG/Python/AG/Adquisicion/'
nombre = "Defensa_AG_PID.csv"
##########################################

######################################################
# Controlador PID                                    #
######################################################
#
#   u(t)  = u0 + k*{ e(t) + ( 1/tau_i) * Integral( e(t)*dt ) + tau_d * derivada(e(t))/dt }
#   u(t)  = u0 + k*{ u0 + e(k) + sumatoria( (delta_t/2)*( e(k)+e(k-1) ) ) - tau_d * ( T(k)-T(k-1) )/delta_t }
#   u: señal de control     e: error { sp - y }     T ---> y : salida planta = Temperatura      delta_t: periodo muestreo
#       AG -> [22.25684101  0.07135554  0.08474443]
######################################################
# Entradas -----------------------------------
# sp = setpoint
# temp = temperatura actual
# temp_a = temperatura anterior
# ierr = integral del error
# dt = delta_t incremento del timepo entre mediciones
# Salidas ----------------------------------
# U = salida del controlador PID
# P = contribución proporcional
# I = contribucion integral
# D = contribucion derivativa
def pid(sp,temp,temp_last,ierr,dt):
    # Parámetros en términos de coeficientes PID
    KP = 19.69376155
    KI = 0.09487479
    KD = 0.02337229
    # u inicial
    U0 = 0 
    # límites superior e inferior en el nivel del calentador
    Uhi = 100
    Ulo = 0
    # calcular el error
    error = sp-temp
    # calcular el error integral
    ierr = ierr + KI * error * dt
    # calcular la derivada de la medida
    dtemp = (temp - temp_last) / dt
    # calcular la salida PID
    P = KP * error
    I = ierr
    D = -KD * dtemp
    U = U0 + P + I + D
    # implementar anti-reset windup
    if U < Ulo or U > Uhi:
        I = I - KI * error * dt
        # acotar
        U = max(Ulo,min(Uhi,U))
    # salida del controlador con términos PID
    #return [U,P,I,D]
    return [U,I]


# Conecta con Arduino
a = tclab.TCLab()

print()
print("Calefactor bajo PID ")
print('-'*35)

loops = int(60.0*run_time)                  # número de ciclos
tm = np.zeros(loops)                        # vector de tiempo

ta = a.T                                   # temperatura ambiente
Tsp = np.ones(loops) * ta                  # setpoint de temperatura (Celsius)
Tsp[int(10):int(40*60)] = sp1
#Tsp[int(40*60):int(60*60)] = sp2
#Tsp[int(40*60):] = sp3
#Tsp[int(50*60):int(65*60)] = sp4
T = np.ones(loops) * ta                     # Temperatura (Celsius)
error_sp = np.zeros(loops)                  # error entre ref y temp

Q = np.ones(loops) * 0.0                    # vector de potencia del calentador

print('Corriendo ciclo principal. Ctrl-C para terminar.')
print(' Tiempo    SP   Temp     Control')
print(('{:6.1f}  {:6.2f} {:6.2f}   {:6.2f}').format( \
           tm[0],Tsp[0],T[0], Q[0]))

# para salvar los datos
df = pd.DataFrame()
df['tiempo'] = None
df = df.assign(temp=None)
df = df.assign(clft=None)
df = df.assign(refer=None)

# Ciclo principal
start_time = time.time()
prev_time = start_time
dt_error = 0.0
# Integral error
ierr = 0.0
try:
    for i in range(1,loops):
        # Sleep time
        sleep_max = 1.0
        sleep = sleep_max - (time.time() - prev_time) - dt_error
        #print("  sleep sleep_max  time.time()-prev_time   dt_error")
        #print(('{:6.1f}  {:6.2f}           {:6.2f}          {:6.2f}').format( \
        #   sleep,sleep_max,time.time()-prev_time,dt_error))
        if sleep>=1e-4:
            time.sleep(sleep-1e-4)
        else:
            print('excedió el tiempo de ciclo máximo por ' + str(abs(sleep)) + ' seg')
            time.sleep(1e-4)

        # Tiempo de registro y cambio en el tiempo
        t = time.time()
        dt = t - prev_time
        if (sleep>=1e-4):
            dt_error = dt-1.0+0.009
        else:
            dt_error = 0.0
        #print("   dt  dt_error")
        #print(('{:6.1f}  {:6.2f} ').format(dt,dt_error))
        prev_time = t
        tm[i] = t - start_time
                    
        # Leer temperatura
        T[i] = a.T

        # Calcula salida PID
        #[Q[i],P,ierr,D] = pid(Tsp[i],T[i],T[i-1],ierr,dt)
        [U, ierr] = pid(Tsp[i],T[i],T[i-1],ierr,dt)


        if i > 9:
            a.Q(U)                                              # manipulacion del calefactor (0-100)
            Q[i] = a.Q()                                        # lectura de potencia usada

        # mostrar data
        print(('{:6.1f}  {:6.2f} {:6.2f}   {:6.2f}').format( \
                  tm[i],Tsp[i],T[i], Q[i]))
        

   # Apagar calefactor
    a.Q(OFF)

    # Salvar en un archivo de texto
    df['tiempo'] = tm
    df['temp'] = T
    df['clft'] = Q
    df['refer'] = Tsp
    df.to_csv(ruta+nombre)
        
# # Si el bucle se finaliza con Ctrl-C      
except KeyboardInterrupt:
    # Desconectar de Arduino
    a.Q(OFF)
    print('Apagar')
    a.close()
    df['tiempo'] = tm
    df['temp'] = T
    df['clft'] = Q
    df['refer'] = Tsp
    df.to_csv(ruta+nombre)
    
# Make sure serial connection still closes when there's an error
except:           
    # Desconectar de Arduino
    a.Q(OFF)
    print('Apagar')
    a.close()
    df['tiempo'] = tm
    df['temp'] = T
    df['clft'] = Q
    df['refer'] = Tsp
    df.to_csv(ruta+nombre)
    raise
    
