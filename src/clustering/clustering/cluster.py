import os
from nipype.interfaces.base import BaseInterface, \
    BaseInterfaceInputSpec, traits, File, TraitedSpec
from nipype.utils.filemanip import split_filename

from sklearn.cluster import spectral_clustering as spectral
from sklearn.cluster import KMeans as km
from sklearn.cluster import Ward
from sklearn.cluster import DBSCAN
import numpy as np
import nibabel as nb
import os

class ClusterInputSpec(BaseInterfaceInputSpec):
    in_File = File(exists=True, desc='surface to be clustered', mandatory=True)
    hemi = traits.String(exists=True, desc='hemisphere', mandatory=True)
    cluster_type = traits.String(exists=True, desc='spectral, hiercluster, kmeans, or dbscan', mandatory=True)
    n_clusters = traits.Int(exists=True, desc='number of clusters', mandatory=True)
    epsilon = traits.Float(exists=True, desc='epsilon parameter for dbscan', mandatory=False)

class ClusterOutputSpec(TraitedSpec):
    out_File = File(exists=True, desc="clustered volume")

class Cluster(BaseInterface):
    input_spec = ClusterInputSpec
    output_spec = ClusterOutputSpec

    def _run_interface(self, runtime):        
        #load data
        data = nb.load(self.inputs.in_File).get_data()
        corrmatrix = np.squeeze(data)
        if self.inputs.cluster_type == 'spectral':
            positivecorrs = np.where(corrmatrix>0,corrmatrix,0) #threshold at 0 (spectral uses non-negative values)
            newmatrix = np.asarray(positivecorrs,dtype=np.double) #spectral expects dtype=double values
            labels = spectral(newmatrix, n_clusters=self.inputs.n_clusters, eigen_solver='arpack', assign_labels='discretize')
        if self.inputs.cluster_type == 'hiercluster':
            labels = Ward(n_clusters=self.inputs.n_clusters).fit_predict(corrmatrix)
        if self.inputs.cluster_type == 'kmeans':
            labels = km(n_clusters=self.inputs.n_clusters).fit_predict(corrmatrix)
        if self.inputs.cluster_type == 'dbscan':
            labels = DBSCAN(eps=self.inputs.epsilon).fit_predict(corrmatrix)

        new_img = nb.Nifti1Image(labels+1, None) #+1 because cluster labels start at 0
        _, base, _ = split_filename(self.inputs.in_File)
        nb.save(new_img, os.path.abspath(base+'_'+str(self.inputs.n_clusters)+'_'+self.inputs.cluster_type+'_'+self.inputs.hemi+'.nii'))

        return runtime

    def _list_outputs(self):
        outputs = self._outputs().get()
        fname = self.inputs.in_File
        _, base, _ = split_filename(fname)
        outputs["out_File"] = os.path.abspath(base+'_'+str(self.inputs.n_clusters)+'_'+self.inputs.cluster_type+'_'+self.inputs.hemi+'.nii')
        return outputs
