import numpy as np
import matplotlib.pyplot as plt
import time
from subprocess import Popen, PIPE

def Bolsig(sigma_m,E_th,slope):
    sigma_m=sigma_m*1e-20
    slope=slope*1e-20
    f=open("LXCat0.txt","w")
    n=500
    E=np.logspace(-3,1,n)

    f.write('----------------------\n')
    f.write('ELASTIC\nReid\n')
    f.write('1.371541e-4 / mass ratio\n')
    f.write('----------------------\n')
    
    for i in range(n):
        f.write(str(E[i])+' '+str(sigma_m)+'\n')

    f.write('----------------------\n')
    f.write('EXCITATION\nReid\n')
    f.write(str(E_th)+' / Thresold Energy\n')
    f.write('1.371541e-4 / mass ratio\n')
    f.write('----------------------\n')
    sigma_exc=slope*(E-E_th)*np.heaviside(E-E_th,1)
    for i in range(n):
        f.write(str(E[i])+' '+str(sigma_exc[i])+'\n')
    
    #plt.loglog(E,(sigma_m+sigma_exc)*1e20)
    #plt.show()

    f.close()
    
    t=time.time()
    process = Popen(['./bolsigminus', 'ex.dat'], stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    #print (stdout)
    
    f=open("Reid.dat","r")
    n=128
    
    E=np.zeros(n)
    out=np.zeros((n,3))
    for line in f:
        if line[:8]=='E/N (Td)' and line[8:].strip()=='Mean energy (eV)':
            for i in range(n):
                l=f.readline().strip()
                if len(l)==0: break
                E[i], out[i,0] = [float(x) for x in l.split()]
        if line[:8]=='E/N (Td)' and line[8:].strip()=='Mobility *N (1/m/V/s)':
            for i in range(n):
                l=f.readline().strip()
                if len(l)==0: break
                E[i], out[i,1] = [float(x) for x in l.split()]
        if line[:8]=='E/N (Td)' and line[8:].strip()=='Diffusion coefficient *N (1/m/s)':
            for i in range(n):
                l=f.readline().strip()
                if len(l)==0: break
                E[i], out[i,2] = [float(x) for x in l.split()]

    out[:,1]=out[:,1]*E*1e-21 #Drift Velocity
    out[:,2]=out[:,2]*1e-24 #Diffusion coefficient
    
    #plt.loglog(E,out[:,0])
    #plt.show()
    #plt.loglog(E,out[:,1])
    #plt.show()
    #plt.loglog(E,out[:,2])
    #plt.show()
    
    #print('time:',time.time()-t)
    return np.log10(out)

cross=open('Y_train.csv','wb')
trans=open('X_train.csv','wb')

n=20
sigma_m=np.random.rand(n)*9+1 #in (Angstrom)^2
E_th=np.random.rand(n)*0.9+0.1  # in eV 
slope=np.random.rand(n)*9+1 #in (Angstrom)^2
Y=np.zeros((n,3))
Y[:,0]=sigma_m
Y[:,1]=E_th
Y[:,2]=slope

t=time.time()
np.savetxt(cross,Y,delimiter=',')
for i in range(n):
    X=Bolsig(Y[i,0],Y[i,1],Y[i,2])
    np.savetxt(trans,np.reshape(X,(1,-1)),delimiter=',')
    print(i,end=' ')
print(time.time()-t)
cross.close()
trans.close()


cross=open('Y_test.csv','wb')
trans=open('X_test.csv','wb')

n=n//4
sigma_m=np.random.rand(n)*9+1 #in (Angstrom)^2
E_th=np.random.rand(n)*0.9+0.1  # in eV 
slope=np.random.rand(n)*9+1 #in (Angstrom)^2
Y=np.zeros((n,3))
Y[:,0]=sigma_m
Y[:,1]=E_th
Y[:,2]=slope

t=time.time()
np.savetxt(cross,Y,delimiter=',')
for i in range(n):
    X=Bolsig(Y[i,0],Y[i,1],Y[i,2])
    np.savetxt(trans,np.reshape(X,(1,-1)),delimiter=',')
    print(i,end=' ')
print(time.time()-t)
cross.close()
trans.close()
