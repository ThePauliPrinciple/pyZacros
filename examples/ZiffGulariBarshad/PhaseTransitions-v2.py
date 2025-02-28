import multiprocessing
import numpy

import scm.plams
import scm.pyzacros as pz
import scm.pyzacros.models

scm.pyzacros.init()

#==============================================
# Initializing the ZGB model
#==============================================

zgb = pz.models.ZiffGulariBarshad()

#==============================================
# Calculation Settings and Execution
#==============================================

# Configuring parallel execution
#--------------------------------
maxjobs = multiprocessing.cpu_count()
scm.plams.config.default_jobrunner = scm.plams.JobRunner(parallel=True, maxjobs=maxjobs)
scm.plams.config.job.runscript.nproc = 1
print('Running up to {} jobs in parallel simultaneously'.format(maxjobs))

# Settings for ZacrosJob
#------------------------
sett = pz.Settings()
sett.molar_fraction.CO = 0.45
sett.molar_fraction.O2 = 0.55
sett.temperature = 500.0
sett.pressure = 1.0
sett.max_time = 10.0
sett.snapshots = ('time', 0.5)
sett.species_numbers = ('time', 0.1)
sett.random_seed = 953129

job = pz.ZacrosJob( settings=sett,
                    lattice=zgb.lattice,
                    mechanism=zgb.mechanism,
                    cluster_expansion=zgb.cluster_expansion )

# Settings for ZacrosParametersScanJob
#--------------------------------------

parameters = pz.ZacrosParametersScanJob.Parameters()
parameters.add( 'x_CO', 'molar_fraction.CO', numpy.arange(0.2, 0.8, 0.01) )
parameters.add( 'x_O2', 'molar_fraction.O2', lambda params: 1.0-params['x_CO'] )

mjob = pz.ZacrosParametersScanJob( reference=job,
                                   parameters=parameters )

# Running the calculations
#--------------------------

results = mjob.run()

if not results.job.ok():
    print('Something went wrong!')

#==============================================
# Getting the Results
#==============================================

x_CO = []
ac_O = []
ac_CO = []
TOF_CO2 = []

results_dict = results.turnover_frequency()
results_dict = results.average_coverage( update=results_dict )

for i,idx in enumerate(results.indices()):
    x_CO.append( results_dict[i]['x_CO'] )
    ac_O.append( results_dict[i]['average_coverage']['O*'] )
    ac_CO.append( results_dict[i]['average_coverage']['CO*'] )
    TOF_CO2.append( results_dict[i]['turnover_frequency']['CO2'] )

print("----------------------------------------------")
print("%4s"%"cond", "%8s"%"x_CO", "%10s"%"ac_O", "%10s"%"ac_CO", "%10s"%"TOF_CO2")
print("----------------------------------------------")
for i in range(len(x_CO)):
    print("%4d"%i, "%8.2f"%x_CO[i], "%10.6f"%ac_O[i], "%10.6f"%ac_CO[i], "%10.6f"%TOF_CO2[i])

#==============================================
# Visualizing the Results
#==============================================
try:
    import matplotlib.pyplot as plt
except ImportError as e:
    print('Consider to install matplotlib to visualize the results!')
    exit(0)

# Coverage and TOF plot
#-----------------------
fig = plt.figure()

ax = plt.axes()
ax.set_xlabel('Molar Fraction CO', fontsize=14)
ax.set_ylabel("Coverage Fraction (%)", color="blue", fontsize=14)
ax.plot(x_CO, ac_O, color="blue", linestyle="-.", lw=2, zorder=1)
ax.plot(x_CO, ac_CO, color="blue", linestyle="-", lw=2, zorder=2)
plt.text(0.3, 0.9, 'O', fontsize=18, color="blue")
plt.text(0.7, 0.9, 'CO', fontsize=18, color="blue")

ax2 = ax.twinx()
ax2.set_ylabel("TOF (mol/s/site)",color="red", fontsize=14)
ax2.plot(x_CO, TOF_CO2, color="red", lw=2, zorder=5)
plt.text(0.37, 1.5, 'CO$_2$', fontsize=18, color="red")

plt.show()

cresults = results.children_results()

# Lattice states for x_CO=0.54 and CO=0.55
#------------------------------------------
cresults[33].last_lattice_state().plot()
cresults[34].last_lattice_state().plot()

# Molecule numbers for x_CO=0.54 and CO=0.55
#--------------------------------------------
cresults[33].plot_molecule_numbers( ["CO2"], normalize_per_site=True )
cresults[34].plot_molecule_numbers( ["CO2"], normalize_per_site=True )

# Molecule numbers for x_CO=0.54 and CO=0.55. First Derivative
#-------------------------------------------------------------
cresults[33].plot_molecule_numbers( ["CO2"], normalize_per_site=True, derivative=True )
cresults[34].plot_molecule_numbers( ["CO2"], normalize_per_site=True, derivative=True )

scm.pyzacros.finish()
