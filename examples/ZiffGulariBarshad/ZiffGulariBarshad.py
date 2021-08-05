"""
This example reproduces the Zacros example described in:
https://zacros.org/tutorials/4-tutorial-1-ziff-gulari-barshad-model-in-zacros
"""

import pyzacros as pz

#---------------------------------------------
# Species:
#---------------------------------------------
# - Gas-species:
CO_gas = pz.Species("CO")
O2_gas = pz.Species("O2")
CO2_gas = pz.Species("CO2", gas_energy=-2.337)

# -) Surface species:
s0 = pz.Species("*", 1)      # Empty adsorption site
CO_ads = pz.Species("CO*", 1)
O_ads = pz.Species("O*", 1)

#---------------------------------------------
# Lattice setup:
#---------------------------------------------
myLattice = pz.Lattice(lattice_type="default_choice",
                    default_lattice=["rectangular_periodic", 1.0, 50, 50])

#---------------------------------------------
# Clusters:
#---------------------------------------------
CO_point = pz.Cluster(site_types=["1"], species=[CO_ads], cluster_energy=-1.3)
O_point = pz.Cluster(site_types=["1"], species=[O_ads], cluster_energy=-2.3)

#---------------------------------------------
# Elementary Reactions
#---------------------------------------------
# CO_adsorption:
CO_adsorption = pz.ElementaryReaction(site_types=["1"],
                                   initial=[s0,CO_gas],
                                   final=[CO_ads],
                                   reversible=False,
                                   pre_expon=10.0,
                                   activation_energy=0.0)

# O2_adsorption:
O2_adsorption = pz.ElementaryReaction(site_types=["1", "1"],
                                    initial=[s0,s0,O2_gas],
                                    final=[O_ads,O_ads],
                                    neighboring=[(1, 2)],
                                    reversible=False,
                                    pre_expon=2.5,
                                    activation_energy=0.0)

# CO_oxidation:
CO_oxidation = pz.ElementaryReaction(site_types=["1", "1"],
                                  initial=[CO_ads, O_ads],
                                  final=[s0, s0, CO2_gas],
                                  neighboring=[(1, 2)],
                                  reversible=False,
                                  pre_expon=1.0e+20,
                                  activation_energy=0.0)

# Settings:
sett = pz.KMCSettings()
sett.molar_fraction.CO = 0.45
sett.molar_fraction.O2 = 0.55
sett.random_seed = 953129
sett.temperature = 500.0
sett.pressure = 1.0
sett.snapshots = ('time', 5.e-1)
sett.process_statistics = ('time', 1.e-2)
sett.species_numbers = ('time', 1.e-2)
sett.event_report = 'off'
sett.max_steps = 'infinity'
sett.max_time = 25.0
sett.wall_time = 3600

myJob = pz.KMCJob( settings=sett,
                    lattice=myLattice,
                    mechanism=[CO_adsorption, O2_adsorption, CO_oxidation],
                    cluster_expansion=[CO_point, O_point] )

print(myJob)
myJob.run()
