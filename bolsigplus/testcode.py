from threading import Thread
from queue import Queue
import os
import tempfile
import numpy as np
from subprocess import Popen, check_output, PIPE

import os
import re

def ListAllTargets():
    if "SLURM_JOB_NODELIST" not in os.environ:
        return ["localhost"]
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
            print("Got item", item)
            out = self.func(self.node_target, item)
            print("Found out",out)
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


def Input(input_file,Y):
    sigma_m=Y[0]*1e-20
    E_th=Y[1]
    slope=Y[2]*1e-20
    
    n=500
    E=np.logspace(-2,2,n)

    with open(input_file, "w") as f:

        f.write('----------------------\n')
        f.write('ELASTIC\nSurge\n')
        f.write('1.371541e-4 / mass ratio\n')
        f.write('----------------------\n')
    
        for i in range(n):
            f.write(str(E[i])+' '+str(sigma_m)+'\n')

        f.write('----------------------\n')
        f.write('EXCITATION\nSurge\n')
        f.write(str(E_th)+' / Thresold Energy\n')
        f.write('1.371541e-4 / mass ratio\n')
        f.write('----------------------\n')
        sigma_exc=slope*(E-E_th)*np.heaviside(E-E_th,1)
        for i in range(n):
            f.write(str(E[i])+' '+str(sigma_exc[i])+'\n')
        f.close()

def Ex(ex_file, grid=100, E_min=0.1, E_max=1e3, n=1000):
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
        
def ExampleProg():
    target_list = ListAllTargets()

    tempdir_list = []
    joblist = []
    
    n=1
    
    sigma_m=10**(np.random.rand(n)) #in (1 to 10) (Angstrom)^2
    E_th=10**(np.random.rand(n)-1)  #in (0.1 to 1) eV 
    slope=10**(np.random.rand(n)*2) #in (1 to 100) (Angstrom)^2
    Y=np.zeros((n,3))
    Y[:,0]=sigma_m
    Y[:,1]=E_th
    Y[:,2]=slope

    for i in range(n):
        # dirname = "Job_p{}".format(param)
        # os.mkdir(dirname)
        tempdir = tempfile.TemporaryDirectory(dir="")

        dirname = tempdir.name
        print(dirname)
        input_file = os.path.join(dirname, "LXCat.txt")
        Input(input_file,Y[i,:])
        
        ex_file = os.path.join(dirname, "ex.dat")
        Ex(ex_file)
        
        # Copy Bolsig into this dir
        os.popen('cp bolsigminus '+dirname)
        
        process = Popen(['ls',dirname], stdout=PIPE, stderr=PIPE)
        stdout,stderr=process.communicate()
        #print(stdout,stderr)

        tempdir_list += [tempdir]
        joblist += [os.path.abspath(dirname)]

    def SingleJob(target, dirname):
        print(dirname)
        '''
        os.chdir(dirname)
        process = Popen('ls', stdout=PIPE, stderr=PIPE)
        stdout,stderr=process.communicate()
        print(stdout,stderr)
        
        out = check_output(['./bolsigminus', 'ex.dat'])
        '''
        out = check_output(['.'+dirname+'/bolsigminus', 'ex.dat'])
        #out = subprocess.check_output(["ssh", "-o", "StrictHostKeyChecking=no", target, "./bolsig","ex.dat"])
        #out = subprocess.check_output(["ssh", "-o", "StrictHostKeyChecking=no", target, "bash -c 'cd {}; cat infile.txt > outfile.txt'".format(dirname)])

    RunJobs(target_list, joblist, SingleJob)
    '''
    output_data = []

    for tempdir in tempdir_list:
        dirname = tempdir.name
        with open(os.path.join(dirname, "Surge.txt")) as file:
            output_data += [file.read()]
        # Clean up dir
        tempdir.cleanup()
    
    return output_data
    '''
    
ExampleProg()

        
