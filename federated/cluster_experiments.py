"""
    File name: cluster_experiments.py
    Author: Amin Abyaneh
    Email: aminabyaneh@gmail.com
    Date created: 15/07/2021
    Python Version: 3.8
    Description: Experiments for the Tuebingen cluster.
"""

# ========================================================================
# Copyright 2021, The CFL Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# You may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ========================================================================

from re import split
import sys
import argparse
import numpy as np

from federated_simulation import FederatedSimulator
from logging_settings import logger
from utils import split_variables_set


global PROCESS_ID


class ParallelExperiments:
    def __init__(self, experiment_id: int, num_clients: int, num_vars: int, graph_type: str, num_rounds: int):
        """ This class handles all the experiments depicted in the main paper and more.

        TODO: Huge refactor later! Merge all the scattered methods and parameters into one class.

        Args:
            process_id (int): Process id is used for parallel execution if the jobs are handled by the cluster.
            num_clients (int): Total number of clients in the federated setup.
            num_vars (int): Number of variables of the underlying data generating graph.
            graph_type (str): Type of the graphs under experiment: 'str' or 'rnd'.
            num_rounds (int): Number of federated rounds.
        """

        self.__process_id = experiment_id
        self.__num_clients = num_clients
        self.__num_vars = num_vars
        self.__graph_type = graph_type
        self.__num_rounds = num_rounds

        self.__str_graphs = ["collider", "bidiag", "full", "chain", "jungle"]
        self.__rnd_graphs = [0.1, 0.2, 0.4, 0.6, 0.8]

        self.__naive_aggregation = "naive"
        self.__locality_aggregation = "locality"

        self.__default_obs_data_size = 10000
        self.__default_int_data_sizes = [12, 24, 48, 96, 144, 192, 240]


def parallel_experiments_sweep_clients_str(nodiv: bool = True):
    """ A method to handle parallel MPI cluster experiments.
    """
    process = PROCESS_ID
    logger.info(f'Starting the experiment sequence for process {process}\n')

    # Id
    experiment_id = process
    repeat_count = 5

    # Federated
    num_rounds = 10
    num_clients = [1, 2, 4, 6, 8]

    # Graph
    num_vars = 20
    obs_sample_size = 10000
    graph_types = ["collider", "bidiag", "full", "chain", "jungle"]
    specifiers = [12, 24, 48, 96, 144, 192, 240]
    specifier = specifiers[experiment_id]
    aggregation_method = "naive"

    for graph_type in graph_types:
        for idx, num_client in enumerate(num_clients):
            logger.info(f'NUMBER OF SAMPLES: {specifier}- NUMBER OF CLIENTS: {num_client}')

            obs_data_size = obs_sample_size * num_client
            int_data_size = specifier * num_vars * num_client if nodiv else specifier * num_vars
            interventions_dict = {cid: [v for v in range(num_vars)] for cid in range(num_client)}
            folder_name = f'ClientSweepNodiv-{graph_type}-{num_vars}-{specifier}' if nodiv else f'ClientSweepDiv-{graph_type}-{num_vars}-{specifier}'

            for seed in range(repeat_count):
                federated_model = FederatedSimulator(interventions_dict, num_clients=num_client,
                                                        num_rounds=num_rounds, experiment_id=idx,
                                                        repeat_id=seed, output_dir=folder_name)
                federated_model.initialize_clients_data(num_vars=num_vars, graph_type=graph_type,
                                                        obs_data_size=obs_data_size,
                                                        int_data_size=int_data_size,
                                                        seed=seed)
                if aggregation_method == "naive":
                    federated_model.execute_simulation(aggregation_method=aggregation_method)

    logger.info(f'Ending the experiment sequence for process {process}\n')

def parallel_experiments_sweep_clients_rnd(nodiv: bool = True):
    """ A method to handle parallel MPI cluster experiments.
    """
    process = PROCESS_ID
    logger.info(f'Starting the experiment sequence for process {process}\n')

    # Id
    experiment_id = process
    repeat_count = 5

    # Federated
    num_rounds = 10
    num_clients = [1, 2, 4, 6, 8]

    # Graph
    num_vars = 20
    obs_sample_size = 15000
    graph_types = [0.1, 0.2, 0.4, 0.6, 0.8]
    specifiers = [12, 24, 48, 96, 144, 192, 240]
    specifier = specifiers[experiment_id]
    aggregation_method = "naive"

    for graph_type in graph_types:
        for idx, num_client in enumerate(num_clients):
            logger.info(f'NUMBER OF SAMPLES: {specifier}- NUMBER OF CLIENTS: {num_client}')
            obs_data_size = graph_type * obs_sample_size * num_client
            int_data_size = specifier * num_vars * num_client if nodiv else specifier * num_vars
            interventions_dict = {cid: [v for v in range(num_vars)] for cid in range(num_client)}
            folder_name = f'ClientSweepNodiv-{graph_type}-{num_vars}-{specifier}' if nodiv else f'ClientSweepDiv-{graph_type}-{num_vars}-{specifier}'

            for seed in range(repeat_count):
                federated_model = FederatedSimulator(interventions_dict, num_clients=num_client,
                                                        num_rounds=num_rounds, experiment_id=idx,
                                                        repeat_id=seed, output_dir=folder_name)
                federated_model.initialize_clients_data(num_vars=num_vars, graph_type="random",
                                                        obs_data_size=obs_data_size,
                                                        int_data_size=int_data_size, edge_prob=graph_type,
                                                        seed=seed)
                if aggregation_method == "naive":
                    federated_model.execute_simulation(aggregation_method=aggregation_method)

    logger.info(f'Ending the experiment sequence for process {process}\n')


def parallel_experiments_balanced_int_str():
    """ A method to handle parallel MPI cluster experiments.
    """
    process = PROCESS_ID
    logger.info(f'Starting the experiment sequence for process {process}\n')

    # Id
    experiment_id = process
    repeat_count = 5

    # Federated
    num_rounds = 10
    num_clients = [1, 2, 0]

    # Graph
    num_vars = 20
    graph_types = ["jungle", "collider", "chain", "full", "bidiag"]
    specifiers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    # Dataset
    int_sample_sizes = [2, 2, 2, 4, 2]
    obs_sample_sizes = [10000, 5000, 5000, 20000, 5000]
    aggregation_method = "naive"

    num_client = num_clients[experiment_id]
    data_weight = num_client

    if not num_client:
        num_client = 1
        data_weight = 2

    interventions_dict = {cid: [v for v in range(num_vars)] for cid in range(num_client)}

    for specifier in specifiers:
        for idx, graph_type in enumerate(graph_types):
            obs_data_size = obs_sample_sizes[idx] * data_weight
            int_data_size = int_sample_sizes[idx] * data_weight * specifier * num_vars
            folder_name = f'BalancedSetup-{graph_type}-{num_vars}-{specifier}'

            for seed in range(repeat_count):
                federated_model = FederatedSimulator(interventions_dict, num_clients=num_client,
                                                     num_rounds=num_rounds, experiment_id=experiment_id,
                                                     repeat_id=seed, output_dir=folder_name)
                federated_model.initialize_clients_data(num_vars=num_vars, graph_type=graph_type,
                                                        obs_data_size=obs_data_size,
                                                        int_data_size=int_data_size,
                                                        seed=seed)
                if aggregation_method == "naive":
                    federated_model.execute_simulation(aggregation_method=aggregation_method)

    logger.info(f'Ending the experiment sequence for process {process}\n')


def parallel_experiments_balanced_int_rnd():
    """ A method to handle parallel MPI cluster experiments.
    """
    process = PROCESS_ID
    logger.info(f'Starting the experiment sequence for process {process}\n')

    # Id
    experiment_id = process
    repeat_count = 5

    # Federated
    num_rounds = 10
    num_clients = [1, 2, 0]

    # Graph
    num_vars = 20
    edge_probs = [0.1, 0.2, 0.4, 0.6, 0.8]
    specifiers = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    # Dataset
    int_sample_sizes = [2, 3, 4, 5, 6]
    obs_sample_sizes = [5000, 5000, 7000, 10000, 15000]
    aggregation_method = "naive"

    num_client = num_clients[experiment_id]
    data_weight = num_client

    if not num_client:
        num_client = 1
        data_weight = 2

    interventions_dict = {cid: [v for v in range(num_vars)] for cid in range(num_client)}

    graph_type = "random"
    for specifier in specifiers:
        for idx, edge_prob in enumerate(edge_probs):
            obs_data_size = obs_sample_sizes[idx] * data_weight
            int_data_size = int_sample_sizes[idx] * data_weight * specifier * num_vars
            folder_name = f'BalancedSetup-{edge_prob}-{num_vars}-{specifier}'

            for seed in range(repeat_count):
                federated_model = FederatedSimulator(interventions_dict, num_clients=num_client,
                                                     num_rounds=num_rounds, experiment_id=experiment_id,
                                                     repeat_id=seed, output_dir=folder_name)
                federated_model.initialize_clients_data(num_vars=num_vars, graph_type=graph_type, edge_prob=edge_prob,
                                                        obs_data_size=obs_data_size,
                                                        int_data_size=int_data_size,
                                                        seed=seed)
                if aggregation_method == "naive":
                    federated_model.execute_simulation(aggregation_method=aggregation_method)

    logger.info(f'Ending the experiment sequence for process {process}\n')


def parallel_experiments_unbalanced_int_str():
    """ A method to handle parallel MPI cluster experiments.
    """
    process = PROCESS_ID
    logger.info(f'Starting the experiment sequence for process {process}\n')

    # Id
    experiment_id = process

    # Graph
    graph_types = ["jungle", "collider", "chain", "full", "bidiag"]
    num_vars = 20

    # Federated
    num_rounds = 10
    num_clients = [1, 1, 2]
    repeat = 10

    accessible_percentages_list = ([30, 70], [20, 80], [50, 50])
    for accessible_percentages in accessible_percentages_list:
        specifier = f'aps-{accessible_percentages[0]}-{accessible_percentages[1]}'

        for graph_type in graph_types:
            obs_data_size, int_data_size = get_datasets_size_locality(graph_type, num_clients[experiment_id],
                                                                      num_vars)
            for seed in range(repeat):
                folder_name = f'ToySetup-{graph_type}-{num_vars}-{specifier}'

                splits = split_variables_set(num_vars, accessible_percentages, seed)
                interventions_dict = [{0: splits[0]}, {0: splits[1]}, # Single client setup
                                    {0: splits[0], 1: splits[1]}] # Federated collaboration

                federated_model = FederatedSimulator(interventions_dict[experiment_id],
                                                    num_clients=num_clients[experiment_id],
                                                    num_rounds=num_rounds, experiment_id=experiment_id,
                                                    repeat_id=seed, output_dir=folder_name)

                federated_model.initialize_clients_data(num_vars=num_vars, graph_type=graph_type,
                                                        obs_data_size=obs_data_size,
                                                        int_data_size=int_data_size, seed=seed)

                federated_model.execute_simulation(aggregation_method="locality",
                                                initial_mass=np.array([16, 16]),
                                                alpha=1, beta=0.3, min_mass=1)

    logger.info(f'Ending the experiment sequence for process {process}\n')


def parallel_experiments_unbalanced_int_rnd():
    """ A method to handle parallel MPI cluster experiments.
    """
    process = PROCESS_ID
    logger.info(f'Starting the experiment sequence for process {process}\n')

    # Id
    experiment_id = process

    # Graph
    graph_type = "random"
    edge_probs = [0.1, 0.2, 0.4, 0.6, 0.8, 1.0]
    num_vars = 20

    # Federated
    num_rounds = 10
    num_clients = [1, 1, 2]
    repeat = 10

    accessible_percentages_list = [[30, 70], [20, 80], [50, 50]]
    for accessible_percentages in accessible_percentages_list:
        specifier = f'aps-{accessible_percentages[0]}-{accessible_percentages[1]}'

        for edge_prob in edge_probs:
            obs_data_size, int_data_size = get_datasets_size_locality(graph_type, num_clients[experiment_id],
                                                                    num_vars, edge_prob)
            for seed in range(repeat):
                folder_name = f'ToySetup-{edge_prob}-{num_vars}-{specifier}'

                splits = split_variables_set(num_vars, accessible_percentages, seed)
                interventions_dict = [{0: splits[0]}, {0: splits[1]}, # Single client setup
                                    {0: splits[0], 1: splits[1]}] # Federated collaboration

                federated_model = FederatedSimulator(interventions_dict[experiment_id],
                                                    num_clients=num_clients[experiment_id],
                                                    num_rounds=num_rounds, experiment_id=experiment_id,
                                                    repeat_id=seed, output_dir=folder_name)

                federated_model.initialize_clients_data(num_vars=num_vars, graph_type=graph_type,
                                                        obs_data_size=obs_data_size,
                                                        int_data_size=int_data_size,
                                                        edge_prob=edge_prob, seed=seed)

                federated_model.execute_simulation(aggregation_method="locality",
                                                initial_mass=np.array([16, 16]),
                                                alpha=1, beta=0.3, min_mass=1)

    logger.info(f'Ending the experiment sequence for process {process}\n')


def parallel_experiments_compare_aggregations(graph_size: int = 50, network_size: int = 10):
    """ A method to handle parallel MPI cluster experiments.
    """
    process = PROCESS_ID
    logger.info(f'Starting the experiment sequence for process {process}\n')

    # Id
    experiment_id = process
    specifiers = [6, 12, 24, 48, 96, 144, 192, 240]


    # Graph
    graph_type = 'random'
    edge_probs = [0.1, 0.2, 0.4, 0.6, 0.8]
    num_vars = graph_size


    # Federated
    num_rounds = 10
    num_clients = network_size
    agg_methods = ["locality", "naive"]
    alpha = 0.5
    repeat = 5
    initial_mass = 1

    for n_acc_vars in [2]:
        percentage = int((n_acc_vars / num_vars) * 100)
        accessible_percentages = [percentage] * int(100 / percentage)

        for edge_prob in edge_probs:
            for agg_method in agg_methods:
                obs_data_size, _ = get_datasets_size_locality(graph_type, num_clients, num_vars, edge_prob)
                folder_name = f'AggComparison-{edge_prob}-{num_vars}-{agg_method}-{alpha}-{n_acc_vars}'

                for seed in range(repeat):
                    splits = split_variables_set(num_vars, accessible_percentages, seed)
                    logger.info(f'The interventional variables split is {splits}.')
                    interventions_dict = {client_idx: splits[client_idx] for client_idx in range(num_clients)}

                    federated_model = FederatedSimulator(interventions_dict, num_clients=num_clients,
                                                        num_rounds=num_rounds, experiment_id=experiment_id,
                                                        repeat_id=seed, output_dir=folder_name)

                    federated_model.initialize_clients_data(num_vars=num_vars, graph_type=graph_type,
                                                            obs_data_size=obs_data_size,
                                                            int_data_size=specifiers[experiment_id] * num_vars * num_clients,
                                                            edge_prob=edge_prob, seed=seed)

                    federated_model.execute_simulation(aggregation_method=agg_method,
                                                    initial_mass=np.array([initial_mass for _ in range(num_clients)]),
                                                    alpha=alpha, beta=0.3, min_mass=0.00001)

    logger.info(f'Ending the experiment sequence for process {process}\n')


def get_datasets_size_locality(graph_type: str, num_clients: int, num_vars: int, edge_prob: float = 0.0):

    """ Chain, Jungle, Collider, and Bidiag graphs sample sizes """
    if graph_type == 'chain' or graph_type == 'jungle' or graph_type == 'collider' or graph_type == 'bidiag':
        obs_data_sizes = 5000 * num_clients
        int_data_sizes = 200 * num_vars * num_clients

    """ Full graph sample sizes """
    if graph_type == 'full':
        obs_data_sizes = 20000 * num_clients
        int_data_sizes = 400 * num_vars * num_clients

    """ Random graphs sample sizes """
    if graph_type == 'random':
        obs_data_sizes = edge_prob * 20000 * num_clients
        int_data_sizes = 200 * num_vars * num_clients

    return obs_data_sizes, int_data_sizes


def parallel_experiments_entropy_test_str():
    """ A method to handle parallel MPI cluster experiments.
    """
    process = PROCESS_ID
    logger.info(f'Starting the experiment sequence for process {process}\n')

    # Id
    experiment_id = process
    repeat_count = 5

    # Federated
    num_rounds = 10

    # Graph
    num_vars = 20
    graph_types = ["jungle", "collider", "chain", "full", "bidiag"]

    # Dataset
    int_sample_sizes = [2, 2, 2, 4, 2]
    obs_sample_sizes = [10000, 5000, 5000, 20000, 5000]
    aggregation_method = "naive"

    num_client = 10
    data_weight = num_client

    interventions_dict = {cid: [v for v in range(num_vars)] for cid in range(num_client)}

    for idx, graph_type in enumerate(graph_types):
        obs_data_size = obs_sample_sizes[idx] * data_weight
        int_data_size = int_sample_sizes[idx] * data_weight * num_vars
        folder_name = f'EntropyTest-{graph_type}-{num_vars}'

        for seed in range(repeat_count):
            federated_model = FederatedSimulator(interventions_dict, num_clients=num_client,
                                                 num_rounds=num_rounds, experiment_id=experiment_id,
                                                 repeat_id=seed, output_dir=folder_name)
            federated_model.initialize_clients_data(num_vars=num_vars, graph_type=graph_type,
                                                    obs_data_size=obs_data_size,
                                                    int_data_size=int_data_size,
                                                    seed=seed)
            if aggregation_method == "naive":
                federated_model.execute_simulation(aggregation_method=aggregation_method)

    logger.info(f'Ending the experiment sequence for process {process}\n')


def parallel_experiments_entropy_test_rnd():
    """ A method to handle parallel MPI cluster experiments.
    """
    process = PROCESS_ID
    logger.info(f'Starting the experiment sequence for process {process}\n')

    # Id
    experiment_id = process
    repeat_count = 5

    # Federated
    num_rounds = 10

    # Graph
    num_vars = 20
    graph_types = [0.1, 0.2, 0.4, 0.6, 0.8]

    # Dataset
    obs_sample_size = 15000
    int_sample_size = 10
    aggregation_method = "naive"

    num_client = 10
    data_weight = num_client

    interventions_dict = {cid: [v for v in range(num_vars)] for cid in range(num_client)}

    for idx, graph_type in enumerate(graph_types):
        obs_data_size = int(obs_sample_size * graph_type) * data_weight
        int_data_size = int(int_sample_size * graph_type) * data_weight * num_vars
        folder_name = f'EntropyTest-{graph_type}-{num_vars}'

        for seed in range(repeat_count):
            federated_model = FederatedSimulator(interventions_dict, num_clients=num_client,
                                                 num_rounds=num_rounds, experiment_id=experiment_id,
                                                 repeat_id=seed, output_dir=folder_name)
            federated_model.initialize_clients_data(num_vars=num_vars, graph_type=graph_type,
                                                    obs_data_size=obs_data_size,
                                                    int_data_size=int_data_size,
                                                    seed=seed)
            if aggregation_method == "naive":
                federated_model.execute_simulation(aggregation_method=aggregation_method)

    logger.info(f'Ending the experiment sequence for process {process}\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Federated causal inference experiments on Tuebingen cluster. '
    'Note that there is an option for running the experiments on a local machine but is not recommended due '
    'to computational complexity of the experiments.')

    parser.add_argument("-et", "--exp-type", default="balanced_interventions", type=str,
        help='Type of experiment from: client_sweep, balanced_interventions, compare_aggregations, '
        'unbalanced_interventions, and entropy_test.')

    parser.add_argument("-gt", "--graph-type", default="random", type=str,
        help="Graph type for the experiments. Could be either str (structured) or rnd (random) graphs.")
    parser.add_argument("-eid", "--experiment-id", default=0, type=int,
        help="Experiment id passed by cluster scripts (create_job.py) or manually by the user.")
    parser.add_argument("-at", "--aggregation-type", default="naive", type=str,
        help="Type of aggregation: either naive or locality.")

    parser.add_argument("-gs", "--graph-size", default=20, type=int,
        help="Size of the graph for underlying data generation process.")
    parser.add_argument("-nc", "--num-clients", default=2, type=int,
        help="Number of clients in the federated setup.")
    parser.add_argument("-nr", "--num-rounds", default=10, type=int,
        help="Total number of federated rounds, we recommend running for 10 or less.")

    parser.add_argument("-lic", "--less-informed-clients", default=2, type=int,
        help="Number of clients with access to only 10 percent of intervened variables. Can only be used with the compare_aggregations experiments.")

    args = parser.parse_args()

    PROCESS_ID = args.experiment_id

    if args.exp_type == "balanced_interventions":
        if args.graph_type == "str":
            parallel_experiments_balanced_int_str()
        elif args.graph_type == "rnd":
            parallel_experiments_balanced_int_rnd()

    elif args.exp_type == "unbalanced_interventions":
        if args.graph_type == "str":
            parallel_experiments_unbalanced_int_str()
        elif args.graph_type == "rnd":
            parallel_experiments_unbalanced_int_rnd()

    elif args.exp_type == "compare_aggregations":
        parallel_experiments_compare_aggregations(args.graph_size, args.num_clients)

    elif args.exp_type == "client_sweep_nodiv":
        if args.graph_type == "str":
            parallel_experiments_sweep_clients_str(nodiv=True)
        elif args.graph_type == "rnd":
            parallel_experiments_sweep_clients_rnd(nodiv=True)

    elif args.exp_type == "client_sweep_div":
        if args.graph_type == "str":
            parallel_experiments_sweep_clients_str(nodiv=False)
        elif args.graph_type == "rnd":
            parallel_experiments_sweep_clients_rnd(nodiv=False)

    elif args.exp_type == "entropy_test":
        if args.graph_type == "str":
            parallel_experiments_entropy_test_str()
        elif args.graph_type == "rnd":
            parallel_experiments_entropy_test_rnd()


