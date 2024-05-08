from typing import List
import copy
import numpy as np

from src.dataset.instances.graph import GraphInstance
from src.dataset.instances.base import DataInstance
from src.explainer.ensemble.aggregators.base import ExplanationAggregator
from src.utils.utils import pad_adj_matrix


class ExplanationUnion(ExplanationAggregator):

    def real_aggregate(self, instance: DataInstance, explanations: List[DataInstance]):
        # If the correctness filter is active then consider only the correct explanations in the list
        if self.correctness_filter:
            filtered_explanations = self.filter_correct_explanations(instance, explanations)
        else:
            # Consider all the explanations in the list
            filtered_explanations = explanations

        if len(filtered_explanations) < 1:
            return copy.deepcopy(instance)

        # Get the number of nodes of the bigger explanation instance
        max_dim = max(instance.data.shape[0], max([exp.data.shape[0] for exp in filtered_explanations]))

        # Get all the changes in all explanations
        mod_edges, _, _ = self.get_all_edge_differences(instance, filtered_explanations)
        # Apply those changes to the original matrix
        union_matrix = pad_adj_matrix(copy.deepcopy(instance.data), max_dim)
        for edge in mod_edges:
            union_matrix[edge[0], edge[1]] = abs(union_matrix[edge[0], edge[1]] - 1 )

        # Create the aggregated explanation
        aggregated_explanation = GraphInstance(id=instance.id, label=1-instance.label, data=union_matrix)
        self.dataset.manipulate(aggregated_explanation)
        aggregated_explanation.label = self.oracle.predict(aggregated_explanation)

        return aggregated_explanation