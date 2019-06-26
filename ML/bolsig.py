import numpy as np
import matplotlib.pyplot as plt
import time
from subprocess import Popen, PIPE

class bolsig:
    def surge_exp(E,p,lmbd,E_th):
        x=np.heaviside(E-E_th,1)*(E-E_th)
        return ((e/lmbd)**p)*(x**p)*np.exp(-p*x/lmbd)
    
    def surge_pwr(E,p,lmbd,E_th):
        x=np.heaviside(E-E_th,1)*(E-E_th)
        return (lmbd**p)*(p+1)**(p+1)*x/(x+p*lmbd)**(p+1)
    
    def Input(E,Y,n=500):
        f=open("LXCat.txt","w")
        f.write('----------------------\n')
        f.write('ELASTIC\nSurge\n')
        f.write('1.371541e-4 / mass ratio\n')
        f.write('----------------------\n')
    
        for i in range(n):
            f.write(str(E[i])+' '+str(Y[i])+'\n')

        '''
        f.write('----------------------\n')
        f.write('EXCITATION\nSurge\n')
        f.write(str(E_th)+' / Thresold Energy\n')
        f.write('1.371541e-4 / mass ratio\n')
        f.write('----------------------\n')
        sigma_exc=slope*(E-E_th)*np.heaviside(E-E_th,1)
        for i in range(n):
            f.write(str(E[i])+' '+str(sigma_exc[i])+'\n')
        '''
        f.close()
    
    def ex(grid=100,E_min=1e-3,E_max=1e3,n=1000):
        f=open("ex.dat","w")
        f.write("READCOLLISIONS\n")
        f.write("LXCat.txt\nSurge\n1\n")
        f.write("CONDITIONS\n")
        f.write("1       / Electric field / N (Td)\n")
        f.write("0        / Angular field frequency / N (m3/s)\n")
        f.write("0.        / Cosine of E-B field angle\n")
        f.write("0.       / Gas temperature (K)\n")
        f.write("300.      / Excitation temperature (K)\n")
        f.write("0.        / Transition energy (eV)\n")
        f.write("0.        / Ionization degree\n")
        f.write("1e-6      / Plasma density (1/m3)\n")
        f.write("1.        / Ion charge parameter\n")
        f.write("1.        / Ion/neutral mass ratio\n")
        f.write("1         / e-e momentum effects: 0=No; 1=Yes*\n")
        f.write("1         / Energy sharing: 1=Equal*; 2=One takes all\n")
        f.write("1         / Growth: 1=Temporal*; 2=Spatial; 3=Not included; 4=Grad-n expansion\n")
        f.write("0.        / Maxwellian mean energy (eV) \n")
        f.write(str(grid)+"      / # of grid points\n")
        f.write("0         / Manual grid: 0=No; 1=Linear; 2=Parabolic \n")
        f.write("1000.      / Manual maximum energy (eV)\n")
        f.write("1e-10     / Precision\n")
        f.write("1e-5      / Convergence\n")
        f.write("1000      / Maximum # of iterations\n")
        f.write("1        / Gas composition fractions\n")
        f.write("1         / Normalize composition to unity: 0=No; 1=Yes\n")
        f.write("RUNSERIES\n")
        f.write("1          / Variable: 1=E/N; 2=Mean energy; 3=Maxwellian energy \n")
        f.write(str(E_min)+" "+str(E_max)+"  / Min Max\n")
        f.write(str(n)+"         / Number \n")
        f.write("3          / Type: 1=Linear; 2=Quadratic; 3=Exponential\n")
        f.write("SAVERESULTS\n")
        f.write("Surge.dat        / File \n")
        f.write("3        / Format: 1=Run by run; 2=Combined; 3=E/N; 4=Energy; 5=SIGLO; 6=PLASIMO\n")
        f.write("1        / Conditions: 0=No; 1=Yes\n")
        f.write("1        / Transport coefficients: 0=No; 1=Yes\n")
        f.write("1        / Rate coefficients: 0=No; 1=Yes\n")
        f.write("0        / Reverse rate coefficients: 0=No; 1=Yes\n")
        f.write("0        / Energy loss coefficients: 0=No; 1=Yes\n")
        f.write("1        / Distribution function: 0=No; 1=Yes \n")
        f.write("0        / Skip failed runs: 0=No; 1=Yes\n")
        f.write("END")
        f.close()
        
    def Bolsig():
        t=time.time()
        process = Popen(['./bolsigminus', 'ex.dat'], stdout=PIPE, stderr=PIPE)
        stdout, stderr = process.communicate()
        #print (stdout)
    
    def Output(n=1000):
        f=open("Surge.dat","r")
    
        E=np.zeros(n)
        out=np.zeros((n,4))
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
    
        out[:,3]=out[:,2]/out[:,1] #Characteristic Energy = Diffusion/ Mobility
    
        out[:,1]=out[:,1]*E*1e-21 #Drift Velocity
        out[:,2]=out[:,2]*1e-24 #Diffusion coefficient
    
        if np.sum(out<0)>0:
            plt.loglog(E,out[:,0])
            plt.loglog(E,out[:,1])
            plt.loglog(E,out[:,2])
            plt.loglog(E,out[:,3])
            plt.show()
    
        #print('time:',time.time()-t)
        return out
