from threading import Thread
from queue import Queue
import os
import tempfile
import numpy as np
from subprocess import Popen, check_output, PIPE
import matplotlib.pyplot as plt
import time

import os
import re

def ListAllTargets():
    if "SLURM_JOB_NODELIST" not in os.environ:
        return ["localhost", "localhost"]
    # return ["localhost"] * 4
    node_list = os.environ["SLURM_JOB_NODELIST"].split(",")
    in_cpus_node = os.environ["SLURM_JOB_CPUS_PER_NODE"].split(",")

    cpus_nodes = []
    for item in in_cpus_node:
        if '(' in item:
            m = re.fullmatch("(\d*)\(x(\d*)\)", item)
            cpus,nodes = m.groups()
            nodes = int(nodes)
            cpus_nodes.extend([int(cpus)] * nodes)
        else:
            cpus_nodes.append(int(item))

    targets = []
    for node,cpus in zip(node_list, cpus_nodes):
        targets.extend([node]*cpus)
        
    return targets


class ProcessThread(Thread):
    def __init__(self, func, node_target, q_in, q_out):
        self.node_target = node_target
        self.func = func
        self.q_in = q_in
        self.q_out = q_out
        # print("In init with {}".format(node_target))
        Thread.__init__(self)

    def run(self):
        # print("Queue start with target={}".format(self.node_target))
        while not self.q_in.empty():
            item = self.q_in.get(False)
            #print("Got item", item)
            out = self.func(self.node_target, item)
            #print("Found out",out)
            self.q_out.put(out)

def RunJobs(target_list, itr, func):

    q_in = Queue()
    q_out = Queue()
    
    n = 0
    for item in itr:
        q_in.put(item)
        n += 1

    thread_list = []
    for target in target_list:
        thread = ProcessThread(func,target,q_in,q_out)
        thread_list.append(thread)
        thread.start()

    out = []
    while n > 0:
        out.append(q_out.get())
        n -= 1

    [thread.join() for thread in thread_list]

    return out




'''
def TestJob(target, x):
    out = subprocess.check_output(["ssh", target, "bash -c 'sleep {} ;echo asdf{}'".format(x,x)])
    return target,x,100 + x,out
'''

def surge_exp(E,p,lmbd,E_th):
    x=E-E_th
    return np.heaviside(x,1)*((e/lmbd)**p)*(x**p)*np.exp(-p*x/lmbd)
    
def surge_pwr(E,p,lmbd,E_th):
    x=E-E_th
    return np.heaviside(x,1)*(lmbd**p)*(p+1)**(p+1)*x/(x+p*lmbd)**(p+1)

def Input(input_file,Y):
    A=Y[:m]
    p=Y[m:2*m]
    lmbd=Y[2*m:3*m]
    E_th=Y[3*m:]
    
    n=500
    E=np.logspace(-1,3,n)
    
    sigma_m=0
    for i in range(m):
        sigma_m+=A[i]*1e-20*surge_pwr(E,p[i],lmbd[i],E_th[i])

    with open(input_file, "w") as f:

        f.write('----------------------\n')
        f.write('ELASTIC\nSurge\n')
        f.write('1.371541e-4 / mass ratio\n')
        f.write('----------------------\n')
    
        for i in range(n):
            f.write(str(E[i])+' '+str(sigma_m[i])+'\n')
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

def Ex(ex_file, dirname, grid=100, E_min=0.1, E_max=1e3, n=1000):
    with open(ex_file, "w") as f:
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
        
def Output(dirname,n=1000):
    output_data = []
    
    with open(os.path.join(dirname, "Surge.dat")) as f:
        #output_data += [f.read()]
            
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
    return np.log10(out)


cross=open('Y.csv','wb')
trans=open('X.csv','wb')
    
target_list = ListAllTargets()

tempdir_list = []
joblist = []
    
n=3
m=1 #no. of Surge functions

A=10**(np.random.rand(n,m)*4-2) # in range (0.01 to 100) (Angstrom)^2
p=np.random.rand(n,m)*2  #in (0 to 2) 
lmbd=10**(np.random.rand(n,m)*2) #in (1 to 100) (eV)
E_th=-10**(np.random.rand(n,m)*2) # in (-1 to -100) (eV)
Y=np.zeros((n,4*m))
Y[:,:m]=A
Y[:,m:2*m]=p
Y[:,2*m:3*m]=lmbd
Y[:,3*m:]=E_th
    
for i in range(n):
    tempdir = tempfile.TemporaryDirectory(dir="")

    dirname = tempdir.name
    #print(dirname)
    input_file = os.path.join(dirname, "LXCat.txt")
    Input(input_file,Y[i,:])
        
    ex_file = os.path.join(dirname, "ex.dat")
    Ex(ex_file,dirname)
        
    # Copy Bolsig into this dir
    import shutil
    shutil.copy("bolsigminus", dirname)
    #os.popen('cp bolsigminus '+dirname)

    tempdir_list += [tempdir]
    joblist += [os.path.abspath(dirname)]

def SingleJob(target, dirname):
    #print(os.path.basename(dirname))
    os.chdir(dirname)
        
    #process = Popen(['./bolsigminus', 'ex.dat'], stdout=PIPE, stderr=PIPE)
    #stdout,stderr=process.communicate()
    #out = check_output(["ssh", "-o", "StrictHostKeyChecking=no", target, "bash -c 'cd {}; ./bolsigminus ex.dat'".format(dirname)])
    out = check_output(["ssh", "-o", "StrictHostKeyChecking=no", target, "bash -c 'cd {}; zsh ../runbolsigonfile.sh'".format(dirname)])
    #out = check_output(["ssh", "-o", "StrictHostKeyChecking=no", target, "".format(dirname)])

    #print("The output from dirname={} was out={}".format(dirname,out))
        
    print('|',end='')
        
    os.chdir('/home/vsingh/bolsigplus')

t=time.time()
RunJobs(target_list, joblist, SingleJob)
    
for i in range(n):
    tempdir=tempdir_list[i]
    dirname = tempdir.name
    X=Output(dirname,1000)
    np.savetxt(cross,np.reshape(Y[i,:],(1,-1)),delimiter=',')
    np.savetxt(trans,np.reshape(X,(1,-1)),delimiter=',')
    # Clean up dir
    tempdir.cleanup()
cross.close()
trans.close()
print(time.time()-t)
        
