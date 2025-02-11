.. _zacrosjob:

ZacrosJob
---------

.. currentmodule:: scm.pyzacros.core.ZacrosJob

The ``ZacrosJob`` class represents a single zacros calculation. This class is an extension of the `PLAMS Job <../../plams/components/jobs.html>`_ class and so it inherits all its powerful features like e.g. being executed locally or submitted to some external queueing system in a transparent way, or executing your jobs in parallel with a predefined dependency structure. See all configure possibilities on the PLAMS Job class documentation in this link: `PLAMS.Job <../../plams/components/jobs.html>`_.

The ``ZacrosJob`` class constructor requires a Settings object, and the set of objects that defines the system, namely: lattice, mechanism, and the cluster expansion Hamiltonian. See the following lines from our example (see :ref:`use case system <use_case_model_zgb>`)

.. code-block:: python
  :linenos:

   job = pz.ZacrosJob( settings=sett, lattice=lat,
                       mechanism=[CO_ads, O2_ads, CO_oxi],
                       cluster_expansion=[CO_p, O_p] )

   print(job)

In the previous code, we used the function print() to see the content of the files that are going to be used with Zacros. This output information is separated into 4 sections, each corresponding to the zacros input files: ``simulation_input.dat``, ``lattice_input.dat``, ``energetics_input.dat``, and ``mechanism_input.dat``.

.. code-block:: none

   ---------------------------------------------------------------------
   simulation_input.dat
   ---------------------------------------------------------------------
   random_seed         953129
   temperature          500.0
   pressure               1.0

   snapshots                 on time       0.1
   process_statistics        on time       0.1
   species_numbers           on time       0.1
   event_report      off
   max_steps         infinity
   max_time          1.0

   n_gas_species    3
   gas_specs_names              CO           O2          CO2
   gas_energies        0.00000e+00  0.00000e+00 -2.33700e+00
   gas_molec_weights   2.79949e+01  3.19898e+01  4.39898e+01
   gas_molar_fracs     4.50000e-01  5.50000e-01  0.00000e+00

   n_surf_species    2
   surf_specs_names         CO*        O*
   surf_specs_dent            1         1

   finish
   ---------------------------------------------------------------------
   lattice_input.dat
   ---------------------------------------------------------------------
   lattice default_choice
     triangular_periodic 1.0 10 3
   end_lattice
   ---------------------------------------------------------------------
   energetics_input.dat
   ---------------------------------------------------------------------
   energetics

   cluster CO*_0-0
     sites 1
     lattice_state
       1 CO* 1
     site_types 1
     graph_multiplicity 1
     cluster_eng -1.30000e+00
   end_cluster

   cluster O*_0-0
     sites 1
     lattice_state
       1 O* 1
     site_types 1
     graph_multiplicity 1
     cluster_eng -2.30000e+00
   end_cluster

   end_energetics
   ---------------------------------------------------------------------
   mechanism_input.dat
   ---------------------------------------------------------------------
   mechanism

   step CO_adsorption
     gas_reacs_prods CO -1
     sites 1
     initial
       1 * 1
     final
       1 CO* 1
     site_types 1
     pre_expon  1.00000e+01
     activ_eng  0.00000e+00
   end_step

   step O2_adsorption
     gas_reacs_prods O2 -1
     sites 2
     neighboring 1-2
     initial
       1 * 1
       2 * 1
     final
       1 O* 1
       2 O* 1
     site_types 1 1
     pre_expon  2.50000e+00
     activ_eng  0.00000e+00
   end_step

   step CO_oxidation
     gas_reacs_prods CO2 1
     sites 2
     neighboring 1-2
     initial
       1 CO* 1
       2 O* 1
     final
       1 * 1
       2 * 1
     site_types 1 1
     pre_expon  1.00000e+20
     activ_eng  0.00000e+00
   end_step

   end_mechanism

When running the ``ZacrosJob`` calculation (see :meth:`~ZacrosJob.run` method), all necessary input files for zacros are generated in the job directory (see option ``name`` in the constructor), and Zacros is internally executed. Then, all output files generated by Zacros are stored for future reference in the same directory. The information contained in the output files can be easily accessed by using the class ``ZacrosResults``.

API
~~~

.. autoclass:: ZacrosJob
    :exclude-members: _result_type, __init__, _get_ready, __str__, __recreate_energetics_input, __recreate_initial_state_input, __recreate_lattice_input, __recreate_mechanism_input, __recreate_simulation_input
