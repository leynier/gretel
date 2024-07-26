from typing import List
import numpy as np

from src.core.explainer_base import Explainer
from src.explainer.future.ensemble.explainer_ensemble_base import ExplainerEnsemble
from src.core.factory_base import get_class, get_instance_kvargs
from src.utils.cfg_utils import  inject_dataset, inject_oracle
from src.utils.cfg_utils import init_dflts_to_of

from src.explainer.future.ensemble.aggregators.multi_criteria.algorithm import find_best
from src.explainer.future.ensemble.aggregators.multi_criteria.criterias.base_criteria import (
    BaseCriteria,
)
from src.explainer.future.ensemble.aggregators.multi_criteria.distances.base_distance import (
    BaseDistance,
)
from src.future.explanation.local.graph_counterfactual import (
    LocalGraphCounterfactualExplanation,
)



class DatasetLevelExplainerSelector(ExplainerEnsemble):
    """
    This explainer determines wich base explainer is the best for a given dataset and uses it for explaining all instances
    """

    def check_configuration(self):
        super().check_configuration()

        # Injecting the oracle and dataset into the component classes
        inject_dataset(self.local_config['parameters']['aggregator'], self.dataset)
        inject_oracle(self.local_config['parameters']['aggregator'], self.oracle)

        for exp in self.local_config['parameters']['explainers']:
            exp['parameters']['fold_id'] = self.local_config['parameters']['fold_id']
            # In any case we need to inject oracle and the dataset to the model
            inject_dataset(exp, self.dataset)
            inject_oracle(exp, self.oracle)

        # Initializing the distance for the multi-criteria selection
        default_distance = "src.explainer.ensemble.aggregators.multi_criteria.distances.euclidean_distance.EuclideanDistance"
        init_dflts_to_of(self.local_config, "distance", default_distance)


    def init(self):
        super().init()
        
        # Initializing base explainers
        self.base_explainers = [ get_instance_kvargs(exp['class'],
                    {'context':self.context,'local_config':exp}) for exp in self.local_config['parameters']['explainers']]
        
        # Inizializing performance criterias
        self.criterias: List[BaseCriteria] = [
            get_instance_kvargs(
                exp["class"], {"context": self.context, "local_config": exp}
            )
            for exp in self.local_config["parameters"]["criterias"]
        ]

        # Inizializing distance
        self.distance: BaseDistance = get_instance_kvargs(
            self.local_config["parameters"]["distance"]["class"],
            {
                "context": self.context,
                "local_config": self.local_config["parameters"]["distance"],
            },
        )


    def explain(self, instance):
        input_label = self.oracle.predict(instance)

        explanations = []
        for explainer in self.base_explainers:
            exp = explainer.explain(instance)
            exp.producer = explainer
            explanations.append(exp)

        result = self.explanation_aggregator.aggregate(explanations)
        result.explainer = self

        return result
    

    def real_fit(self):
        pass


    def write(self):
        pass
      
    def read(self):
        pass

    @property
    def name(self):
        alias = get_class( self.local_config['parameters']['aggregator']['class'] ).__name__
        return self.context.get_name(self,alias=alias)