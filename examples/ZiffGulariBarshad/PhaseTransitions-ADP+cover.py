import multiprocessing
import numpy

import scm.plams
import scm.pyzacros as pz
import scm.pyzacros.models

import adaptiveDesignProcedure as adp

#-------------------------------------
# Calculating the rates with pyZacros
#-------------------------------------
def getRate( conditions ):

    print("")
    print("  Requesting:")
    for cond in conditions:
        print("    xCO = ", cond[0])
    print("")

    #---------------------------------------
    # Zacros calculation
    #---------------------------------------
    zgb = pz.models.ZiffGulariBarshad()

    z_sett = pz.Settings()
    z_sett.random_seed = 953129
    z_sett.temperature = 500.0
    z_sett.pressure = 1.0
    z_sett.species_numbers = ('time', 0.1)
    z_sett.max_time = 10.0

    z_job = pz.ZacrosJob( settings=z_sett, lattice=zgb.lattice,
                          mechanism=zgb.mechanism,
                          cluster_expansion=zgb.cluster_expansion )

    #---------------------------------------
    # Parameters scan calculation
    #---------------------------------------
    ps_params = pz.ZacrosParametersScanJob.Parameters()
    ps_params.add( 'x_CO', 'molar_fraction.CO', [ cond[0] for cond in conditions ] )
    ps_params.add( 'x_O2', 'molar_fraction.O2', lambda params: 1.0-params['x_CO'] )

    ps_job = pz.ZacrosParametersScanJob( reference=z_job, parameters=ps_params )

    results = ps_job.run()

    tof = numpy.nan*numpy.empty((len(conditions),3))
    if( results.job.ok() ):
        results_dict = results.turnover_frequency()
        results_dict = results.average_coverage( last=20, update=results_dict )

        for i in range(len(results_dict)):
            tof[i,0] = results_dict[i]['average_coverage']['O*']
            tof[i,1] = results_dict[i]['average_coverage']['CO*']
            tof[i,2] = results_dict[i]['turnover_frequency']['CO2']

    return tof


scm.pyzacros.init( folder="PhaseTransitions-ADP+cover" )

# Run as many job simultaneously as there are cpu on the system
maxjobs = multiprocessing.cpu_count()
scm.plams.config.default_jobrunner = scm.plams.JobRunner(parallel=True, maxjobs=maxjobs)
scm.plams.config.job.runscript.nproc = 1
print('Running up to {} jobs in parallel simultaneously'.format(maxjobs))

#-----------------
# Surrogate model
#-----------------
input_var = ( { 'name'    : 'CO',
                'min'     : 0.2,
                'max'     : 0.8,
                'num'     : 5,
                'typevar' : 'lin' }, )

tab_var = ( {'name':   'ac_O', 'typevar':'lin'},
            {'name':  'ac_CO', 'typevar':'lin'},
            {'name':'TOF_CO2', 'typevar':'lin'} )

outputDir = scm.pyzacros.workdir()+'/adp.results'

adpML = adp.adaptiveDesignProcedure( input_var, tab_var, getRate,
                                     algorithmParams={'dth':0.01,'d2th':0.10}, # Quality Very Good
                                     outputDir=outputDir,
                                     randomState=10 )

adpML.createTrainingDataAndML()

x_CO,ac_O,ac_CO,TOF_CO2 = adpML.trainingData.T

print( "-------------------------------------------------" )
print( "%4s"%"cond", " %8s"%"x_CO", " %10s"%"ac_O", "%10s"%"ac_CO", "%12s"%"TOF_CO2" )
print( "-------------------------------------------------" )
for i in range(len(x_CO)):
    print( "%4d"%i, "%8.3f"%x_CO[i], "%10.6f"%ac_O[i], "%10.6f"%ac_CO[i], "%12.6f"%TOF_CO2[i] )

scm.pyzacros.finish()

#---------------------------------------------
# Plotting the results
#---------------------------------------------
try:
    import matplotlib.pyplot as plt
except ImportError as e:
    print('Consider to install matplotlib to visualize the results!')
    exit(0)

fig = plt.figure()

x_CO_model = numpy.linspace(0.2,0.8,201)
ac_O_model,ac_CO_model,TOF_CO2_model = adpML.predict( x_CO_model ).T

ax = plt.axes()
ax.set_xlabel('Molar Fraction CO', fontsize=14)

ax.set_ylabel("Coverage Fraction (%)", color="blue", fontsize=14)
ax.plot(x_CO_model, ac_O_model, color="blue", linestyle="-.", lw=2, zorder=1)
ax.plot(x_CO, ac_O, marker='$\u25EF$', color='blue', markersize=4, lw=0, zorder=1)
ax.plot(x_CO_model, ac_CO_model, color="blue", linestyle="-", lw=2, zorder=2)
ax.plot(x_CO, ac_CO, marker='$\u25EF$', color='blue', markersize=4, lw=0, zorder=1)
plt.text(0.3, 0.9, 'O', fontsize=18, color="blue")
plt.text(0.7, 0.9, 'CO', fontsize=18, color="blue")

ax2 = ax.twinx()
ax2.set_ylabel("TOF (mol/s/site)",color="red", fontsize=14)
ax2.plot(x_CO_model, TOF_CO2_model, color='red', linestyle='-', lw=2, zorder=0)
ax2.plot(x_CO, TOF_CO2, marker='$\u25EF$', color='red', markersize=4, lw=0, zorder=1)
plt.text(0.37, 1.5, 'CO$_2$', fontsize=18, color="red")

plt.show()
