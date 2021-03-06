import sys, os
BIN=os.path.expanduser('../../')
sys.path.append(BIN)
BIN=os.path.expanduser('../../PyHEADTAIL/testing/script-tests/')
sys.path.append(BIN)
from LHC import LHC
import PyPIC.geom_impact_ellip as ell
from PyPIC.MultiGrid import AddTelescopicGrids
import PyPIC.FiniteDifferences_ShortleyWeller_SquareGrid as PIC_FDSW
import numpy as np
import pylab as pl
import mystyle as ms
from scipy.constants import e, epsilon_0


qe = e
eps0 = epsilon_0

# chamber parameters
x_aper = 25e-3
y_aper = 25e-3
Dh_single = 0.5e-3
#~ # machine parameters 
optics_mode = 'smooth'
n_segments=1
# beam parameters
n_macroparticles=1000000


#LHC
machine_configuration='6.5_TeV_collision_tunes'
intensity=1.2e11
epsn_x=.5e-6
epsn_y=3e-6
sigma_z=7e-2
machine = LHC(machine_configuration = machine_configuration, optics_mode = optics_mode, n_segments = n_segments)


# build chamber
chamber = ell.ellip_cham_geom_object(x_aper = x_aper, y_aper = y_aper)
Vx, Vy = chamber.points_on_boundary(N_points=200)


# generate beam for multigrid
bunch = machine.generate_6D_Gaussian_bunch(n_macroparticles = n_macroparticles, intensity = intensity, 
                            epsn_x = epsn_x, epsn_y = epsn_y, sigma_z = sigma_z)


# generate beam 1 for state1 
bunch1 = machine.generate_6D_Gaussian_bunch(n_macroparticles = n_macroparticles, intensity = 2*intensity, 
                            epsn_x = epsn_x, epsn_y = epsn_y, sigma_z = sigma_z)


# generate beam 2 for state 2
bunch2 = machine.generate_6D_Gaussian_bunch(n_macroparticles = n_macroparticles, intensity = 3*intensity, 
                            epsn_x = epsn_x, epsn_y = epsn_y, sigma_z = sigma_z)
                            
# generate beam 3 for state3 
bunch3 = machine.generate_6D_Gaussian_bunch(n_macroparticles = n_macroparticles, intensity = 5*intensity, 
                            epsn_x = epsn_x, epsn_y = epsn_y, sigma_z = sigma_z)


#  Multi grid parameters
Sx_target = 10*bunch.sigma_x()
Sy_target = 10*bunch.sigma_y()
Dh_target = 0.5*bunch.sigma_x()
sparse_solver = 'PyKLU'

pic_singlegrid = PIC_FDSW.FiniteDifferences_ShortleyWeller_SquareGrid(chamb = chamber, Dh = Dh_single)

# build telescope
pic_multigrid = AddTelescopicGrids(pic_main = pic_singlegrid, f_telescope = 0.3, 
    target_grid = {'x_min_target':-Sx_target/2., 'x_max_target':Sx_target/2.,'y_min_target':-Sy_target/2.,'y_max_target':Sy_target/2.,'Dh_target':Dh_target}, 
    N_nodes_discard = 3., N_min_Dh_main = 10, sparse_solver=sparse_solver)
#scatter and solve multigrid
pic_multigrid.scatter(bunch.x, bunch.y, bunch.particlenumber_per_mp+bunch.y*0., charge=qe)
pic_multigrid.solve()

#states
state1 = pic_multigrid.get_state_object()
state2 = pic_multigrid.get_state_object()
state3 = pic_multigrid.get_state_object()

#scatter states
state1.scatter(bunch1.x, bunch1.y, bunch1.particlenumber_per_mp+bunch1.y*0., charge=qe)
state2.scatter(bunch2.x, bunch2.y, bunch2.particlenumber_per_mp+bunch2.y*0., charge=qe)
state3.scatter(bunch3.x, bunch3.y, bunch3.particlenumber_per_mp+bunch3.y*0., charge=qe)
#solve states
pic_multigrid.solve_states([state1, state2, state3])




#plot electric field for each state and singlegrid
pl.close('all')

# prepare probes
theta_probes=np.linspace(0., 2*np.pi, 100)
r_probes= 0.2e-3
x_probes = r_probes*np.cos(theta_probes)
y_probes = r_probes*np.sin(theta_probes)

# get field at probes
Ex_multigrid, Ey_multigrid = pic_multigrid.gather(x_probes, y_probes)
Ex_state1, Ey_state1 = state1.gather(x_probes, y_probes)
Ex_state2, Ey_state2 = state2.gather(x_probes, y_probes)
Ex_state3, Ey_state3 = state3.gather(x_probes, y_probes)

#~ #plot at probes
pl.close('all')
ms.mystyle_arial(fontsz=12)
pl.figure(4, figsize=(8,6)).patch.set_facecolor('w')
sp1=pl.subplot(2,1,1)
pl.plot(theta_probes, Ex_multigrid, '--k', label = 'Multigrid (I)')
pl.plot(theta_probes, Ex_state1, '.-m', label = 'State 1 (2I)')
pl.plot(theta_probes, Ex_state2, '.-y', label = 'State 2 (3I)')
pl.plot(theta_probes, Ex_state3, '.-g', label = 'State 3 (5I)')
pl.xlabel('theta[deg]')
pl.ylabel('Ex [V/m] ')
pl.ticklabel_format(style='sci', scilimits=(0,0),axis='x') 
pl.ticklabel_format(style='sci', scilimits=(0,0),axis='y')
pl.legend(loc = 'best')
pl.grid('on')
pl.subplot(2,1,2, sharex=sp1)
pl.plot(theta_probes, Ey_multigrid, '--k', label = 'Multigrid (I)')  
pl.plot(theta_probes, Ey_state1, '.-m', label = 'State 1 (2I)')
pl.plot(theta_probes, Ey_state2, '.-y', label = 'State 2 (3I)')
pl.plot(theta_probes, Ey_state3, '.-g', label = 'State 3 (5I)') 
pl.xlabel('theta[deg]')
pl.ylabel('Ey [V/m] ')
pl.ticklabel_format(style='sci', scilimits=(0,0),axis='x') 
pl.ticklabel_format(style='sci', scilimits=(0,0),axis='y')  
pl.legend(loc = 'best')
pl.suptitle('Test states for MultiGrid')
pl.grid('on')
pl.show()
