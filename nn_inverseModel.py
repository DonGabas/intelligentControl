###############################################################
###   Identificacion de modelo inverso con modelo ARX utilizando 
###   una arquitectura de red de perceptron multicapa (MLP) 
###   implementada en Keras
###############################################################

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from numpy import linalg as LA
from tensorflow import keras
from keras.models import Sequential
from keras.layers import Dense
from keras.layers import LeakyReLU
from keras.callbacks import ModelCheckpoint

###############################################################
#model_cargar = 'RN_entrenadas/ModInvPlus_mlp_9-4-2-1_L-L_sc_v2.h5'
model_salvado = 'RN_entrenadas/ModInvPlus_mlp_9-4-2-1_L-L_sc_v2.h5'

temper = 'temp_s'
url = '/home/USER/Documentos/PG/Python/Calefactor/Adquisicion/'
nombreE = "step_py_6h_s_sp_12_control_scalado.csv"                # Entrenamiento
nombreV = "step_py_6h_s_sp_13_control_scalado.csv"                # Validacion
nombreP = "step_py_6h_s_sp_14_control_scalado.csv"                # Prueba


############################################################

###############################################################################
#       Esta función da formato a los datos de entrada y salida (ARX)
#           |u1 u2 ... up    y1 y2 ... yp   |       |yp+1|
#       X = |u2 u3 ... up+1  y2 y3 ... yp+1 |   y = |yp+2|
#           |...                            |       |    |
#           |...                            |       |... |
#                (tam(input_seq)-p)x(2*p)       (tam(input_seq)-p)x1  
###############################################################################
def form_data(input_sec, output_sec,past):
    data_len=np.max(input_sec.shape)
    X=np.zeros(shape=(data_len-past,2*past))
    Y=np.zeros(shape=(data_len-past,))
    for i in range(0,data_len-past):
        X[i,0:past]=input_sec[i:i+past,0]
        X[i,past:]=output_sec[i:i+past,0]
        Y[i]=output_sec[i+past,0]
    return X,Y

##############################################################################

###############################################################################
#                  Data de entranamiento
###############################################################################

# cargar datos y analizar en columnas
data = pd.read_csv(url+nombreE)
u = data[temper]
y = data['clft']
sp = data['sp']
past = 4

in_train = np.array([u])    # forma: (1,tam(u))
in_train = in_train.T       # forma: (tam(u),1)

out_train = np.array([y])   # forma: (1,tam(y))
out_train = out_train.T     # forma: (tam(y),1)

sp_train = np.array([sp])
for i in range(past):                                            # eliminar past primeros elementos
    sp_train = np.delete(sp_train, 0)
sp_train.shape = (len(sp_train),1)

X_train,Y_train= form_data(in_train, out_train, past) # forma: (tam(u)-2, 4) , (tam(y)-2, 4)
X_train = np.append(X_train,sp_train, axis = 1)       # anexar setpoint a la data [y1, y2, y3, y4 , u1, u2, u3, u4, ref]
print("Data de entranamiento...OK")
###############################################################################
#                  Data de validacion
###############################################################################

data = pd.read_csv(url+nombreV)
u = data[temper]
y = data['clft']
sp = data['sp']

in_valid = np.array([u])    # forma: (tam(u),1)
in_valid = in_valid.T       # forma: (tam(u),1)

out_valid = np.array([y])   # forma: (1,tam(y))
out_valid = out_valid.T     # forma: (tam(y),1)

sp_valid = np.array([sp])
for i in range(past):                                            # eliminar past primeros elementos
    sp_valid = np.delete(sp_valid, 0)
sp_valid.shape = (len(sp_valid),1)

X_valid,Y_valid= form_data(in_valid, out_valid, past) # forma: (tam(u)-2, 4) , (tam(y)-2, 4)
X_valid = np.append(X_valid,sp_valid, axis = 1)       # anexar setpoint a la data [y1, y2, y3, y4 , u1, u2, u3, u4, ref]
print("Data de validacion...OK")
###############################################################################
#                  Data de test
###############################################################################

data = pd.read_csv(url+nombreP)
u = data[temper]
#u = data['temp_s']
y = data['clft']
sp = data['sp']

in_test = np.array([u])    # forma: (1,tam(y))
in_test = in_test.T       # forma: (tam(u),1)

out_test = np.array([y])   # forma: (1,tam(y))
out_test = out_test.T     # forma: (tam(y),1)

sp_test = np.array([sp])
for i in range(past):                                        # eliminar past primeros elementos
    sp_test = np.delete(sp_test, 0)
sp_test.shape = (len(sp_test),1)

X_test,Y_test= form_data(in_test, out_test, past) # forma: (tam(u)-2, 4) , (tam(y)-2,)
X_test = np.append(X_test,sp_test, axis = 1)      # anexar setpoint a la data [y1, y2, y3, y4 , u1, u2, u3, u4, ref]
print("Data de test...OK")
###############################################################################
#                        RNA
#  batch_size: numero de muestras que se propagaran/retropropagaran a traves de la red
#  batch size = n de muestras : mejor estimación del gradiente vs mayor coste computacional
#  batch size < n de muestras : peor estimación del gradiente vs menor coste computacional
#  se requieren (n muestras)/batch size iteraciones para completar 1 epoch
###############################################################################

model = Sequential()        # serie de capas de neuronas secuenciales

model.add(Dense(2, activation=LeakyReLU(alpha=0.08), input_dim=(2*past+1)))
model.add(Dense(4, activation=LeakyReLU(alpha=0.08)))
model.add(Dense(1))

#model = keras.models.load_model(model_cargar)
model.compile(optimizer='adam', loss='mse')
model.summary()
########################
checkpoint = ModelCheckpoint(model_salvado, monitor="loss", verbose=1, save_best_only=True, mode="min")
callbacks_list = [checkpoint]

history=model.fit(X_train, Y_train, epochs=10, batch_size=20, callbacks=callbacks_list, 
                                                validation_data=(X_valid,Y_valid), verbose=2, shuffle=True)

model.summary()
############################################################################### batch_size=1,
#  utilizar los datos de prueba para investigar el rendimiento de la predicción
###############################################################################
prediccion_RNA = model.predict(X_test)

# Guardar el modelo RNA
model.save(model_salvado)

# ploteo
plt.figure()
plt.subplot(2,1,1)
plt.plot(Y_test, 'b', label='Salida real')
plt.plot(prediccion_RNA,'--r', label='Salida predicha')
plt.legend()
plt.subplot(2,1,2)
plt.plot(in_test,'g', label='Temperatura')
plt.plot(sp_test,'k--', label='setpoint')
plt.xlabel('Tiempo discreto')
plt.ylabel('Salida')
plt.legend()
#plt.show()

###############################################################################
#       graficar entrenamiento y validación
###############################################################################

loss=history.history['loss']
val_loss=history.history['val_loss']
epochs=range(1,len(loss)+1)
plt.figure()
plt.plot(epochs, loss,'b', label='funcion perdida de entrenamiento')
plt.plot(epochs, val_loss,'r', label='Validacion de la funcion perdida')
plt.title('Entrenamiento y validacion de la funcion de perdida')
plt.xlabel('Entrenamientos')
plt.ylabel('Funcion de perdida')
plt.xscale('log')
#plt.yscale('log')
plt.legend()
plt.show()
