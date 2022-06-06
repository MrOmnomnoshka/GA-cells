import os
import glob

import numpy as np
import pandas as pd
import ansys.mapdl.reader as pyansys
from matplotlib import pyplot
from pandas import DataFrame
from sklearn.cluster import KMeans

from src.clusterization.ClusterDataEntry import ClusterDataEntry


class ResearchesClusterization:
    def __init__(self, researches_folder):
        self.researches_folder = researches_folder
        self.RESEARCH_ID_COLUMN = "research_id"
        self.AVG_STRESS_COLUMN = "avg_stress"
        self.MAX_STRESS_COLUMN = "max_stress"

    def plot_cluster_data(self):
        research_data = self.collect_data()
        avg_max_stress = research_data.to_numpy()[:, [4, 6, 8]]
        model = KMeans(n_clusters=2)
        model.fit(X=avg_max_stress[:, [1, 2]])
        yhat = model.predict(avg_max_stress[:, [1, 2]])
        # retrieve unique clusters
        clusters = np.unique(yhat)
        # create scatter plot for samples from each cluster
        for cluster in clusters:
            # get row indexes for samples with this cluster
            row_ix = np.where(yhat == cluster)
            # create scatter of these samples
            pyplot.scatter(avg_max_stress[row_ix, 1], avg_max_stress[row_ix, 2])

        for i in range(len(avg_max_stress)):
            pyplot.annotate(text=str(avg_max_stress[i, 0]),
                            xy=(avg_max_stress[i, 1], avg_max_stress[i, 2]))

        # show the plot
        pyplot.show()

    def collect_data(self) -> DataFrame:
        stress_files = self.get_list_of_rst_researches()
        research_data = pd.DataFrame(columns=[self.RESEARCH_ID_COLUMN, self.AVG_STRESS_COLUMN, self.MAX_STRESS_COLUMN])

        for stress_file in stress_files:
            entry: ClusterDataEntry = self.__get_research_data(stress_file)
            print(entry)
            series = pd.Series(data=[
                self.RESEARCH_ID_COLUMN, entry.research_id,
                self.AVG_STRESS_COLUMN, entry.avg_stress,
                self.MAX_STRESS_COLUMN, entry.max_stress
            ])
            research_data = research_data.append(series, ignore_index=True)

        return research_data

    def __get_research_data(self, stress_file: str):
        research_id = self.__get_research_id_from_path(stress_file)
        avg_stress, max_stress = self.__calculate_avg_and_max_stress(stress_file)
        return ClusterDataEntry(
            research_id=research_id,
            avg_stress=avg_stress,
            max_stress=max_stress)

    def get_list_of_rst_researches(self):
        rst_pattern = self.researches_folder + os.sep + "*.rst"
        all_researches = glob.glob(rst_pattern)
        if "file" in all_researches[-1]:  # Deleting Ansys standard file
            del all_researches[-1]
        return all_researches

    def __get_research_id_from_path(self, rst_file: str) -> str:
        nodes = rst_file.split(os.sep)
        return nodes[-1]

    def __calculate_avg_and_max_stress(self, stress_file: str) -> [float, float]:
        _, stress = pyansys.read_binary(stress_file).principal_nodal_stress(0)
        stress = stress[:, 4]
        stress = stress[~np.isnan(stress)]

        avg_stress = np.average(stress)
        max_stress = np.max(stress)

        return avg_stress, max_stress
