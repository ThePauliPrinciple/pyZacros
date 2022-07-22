"""Module containing the ZacrosMultiJob class."""

import os
import shutil
import numpy
from collections import OrderedDict

import scm.plams

from .ZacrosJob import *

__all__ = ['ZacrosMultiJob', 'ZacrosMultiResults']


class ZacrosMultiResults( scm.plams.Results ):
    """
    A Class for handling ZacrosMulti Results.
    """

    def turnover_frequency(self, nbatch=20, confidence=0.99, update=None):
        if update:
            output = update
        else:
            output = []

        for pos,idx in enumerate(self.job._indices):
            params = self.job._parameters_values[idx]
            TOFs,_,_ = self.job.children[idx].results.turnover_frequency( nbatch=nbatch, confidence=confidence )

            if update:
                output[pos]['turnover_frequency'] = TOFs
            else:
                output.append( {**params, 'turnover_frequency':TOFs} )

        return output


    def average_coverage(self, last=5, update=None):
        if update:
            output = update
        else:
            output = []

        for pos,idx in enumerate(self.job._indices):
            params = self.job._parameters_values[idx]
            acf = self.job.children[idx].results.average_coverage( last=last )

            if update:
                output[pos]['average_coverage'] = acf
            else:
                output.append( {**params, 'average_coverage':acf} )

        return output


class ZacrosMultiJob( scm.plams.MultiJob ):
    """
    Create a new ZacrosMultiJob object.

    *   ``lattice`` -- Lattice containing the lattice to be used during the calculation.
    *   ``mechanism`` -- Mechanism containing the mechanisms involed in the calculation.
    *   ``cluster_expansion`` -- ClusterExpansion containing the list of Clusters to use during the simulation.
    *   ``initial_state`` -- Initial state of the system. By default the simulation will use an empty lattice.
    *   ``settings`` -- Settings containing the parameters of the Zacros calculation.
    *   ``name`` -- A string containing the name of the job. All zacros input and output files are stored in a folder with this name. If not supplied, the default name is ``plamsjob``.
    *   ``restart`` -- ZacrosMultiJob object from which the calculation will be restarted
    """

    _command = os.environ["AMSBIN"]+'/zacros' if 'AMSBIN' in os.environ else 'zacros.x'
    _result_type = ZacrosMultiResults

    class Parameter:
        INDEPENDENT = 0
        DEPENDENT = 1

        def __init__(self, name_in_settings, values):
            self.name_in_settings = name_in_settings

            self.values = values
            if type(values) not in [list,numpy.ndarray] and not callable(values):
                msg  = "\n### ERROR ### ZacrosMultiJob.Parameter.__init__.\n"
                msg += "              Parameter 'values' should be a 'list', 'numpy.ndarray', or 'function'.\n"
                raise Exception(msg)

            self.kind = None
            if type(values) in [list,numpy.ndarray]:
                self.kind = ZacrosMultiJob.Parameter.INDEPENDENT
            elif callable(values):
                self.kind = ZacrosMultiJob.Parameter.DEPENDENT


    def __init__(self, lattice, mechanism, cluster_expansion, initial_state=None,
                    restart=None, generator=None, generator_parameters=None, **kwargs):
        scm.plams.MultiJob.__init__(self, children=OrderedDict(), **kwargs)

        if generator is not None:
            if len(generator_parameters) == 0:
                msg  = "\n### ERROR ### ZacrosMultiJob.__init__.\n"
                msg += "              Parameter 'generator_parameters' is required if 'generator' different than None\n"
                raise Exception(msg)

            for name,item in generator_parameters.items():
                if type(item) is not ZacrosMultiJob.Parameter:
                    msg  = "\n### ERROR ### ZacrosMultiJob.__init__.\n"
                    msg += "              Parameter 'generator_parameters' should be a list of ZacrosMultiJob.Parameter objects.\n"
                    raise Exception(msg)

        self._lattice = lattice
        self._mechanism = mechanism
        self._cluster_expansion = cluster_expansion
        self._initial_state = initial_state
        self._restart = restart
        self._generator = generator
        self._generator_parameters = generator_parameters

        self._indices = None
        self._parameters_values = None


    def prerun(self):

        path = shutil.which(self._command)
        if( path is None ):
            self._finalize()
            raise ZacrosExecutableNotFoundError( self._command )

        if self._generator_parameters is not None:
            self._indices,self._parameters_values,settings_list = self._generator( self.settings, self._generator_parameters )

            for idx,settings_i in settings_list.items():
                self.children[idx] = ZacrosJob(settings=settings_i, lattice=self._lattice, mechanism=self._mechanism, \
                                                cluster_expansion=self._cluster_expansion, initial_state=self._initial_state, \
                                                restart=self._restart)


    @staticmethod
    def meshGenerator( settings, parameters ):

        independent_params = []
        for name,item in parameters.items():
            if item.kind == ZacrosMultiJob.Parameter.INDEPENDENT:
                independent_params.append( item.values )

        mesh = numpy.meshgrid( *independent_params, sparse=False )

        def name2dict( name ):
            tokens = name.split('.')
            output = ""
            for i,token in enumerate(tokens):
                if i != len(tokens)-1:
                    output += "[\'"+token+"\']"
            return output+".__setitem__(\'"+tokens[-1]+"\',$var_value)"

        indices = [ tuple(idx) for idx in numpy.ndindex(mesh[0].shape) ]
        parameters_values = {}
        settings_list = {}

        for idx in indices:
            settings_i = settings.copy()

            params = {}
            for i,(name,item) in enumerate(parameters.items()):
                if item.kind == ZacrosMultiJob.Parameter.INDEPENDENT:
                    value = mesh[i][idx]
                    eval('settings_i'+name2dict(item.name_in_settings).replace('$var_value',str(value)))
                    params[name] = value

            for i,(name,item) in enumerate(parameters.items()):
                if item.kind == ZacrosMultiJob.Parameter.DEPENDENT:
                    value = item.values(params)
                    eval('settings_i'+name2dict(item.name_in_settings).replace('$var_value',str(value)))
                    params[name] = value

            parameters_values[idx] = params
            settings_list[idx] = settings_i

        return indices,parameters_values,settings_list
