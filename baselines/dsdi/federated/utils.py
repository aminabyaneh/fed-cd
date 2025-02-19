"""
    File name: utils.py
    Author: Amin Abyaneh
    Email: aminabyaneh@gmail.com
    Date created: 25/04/2021
    Python Version: 3.8
    Description: Methods and classes required for the project.
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

import glob
import os.path
import random
from typing import List, Dict

import numpy as np
import pandas as pd
from cdt.metrics import SHD

from logging_settings import logger

DEFAULT_OBSERVATION_SIZE = 5000


# TODO: Remove all the str values around and turn them into Enums.


def generate_sample_dataset(assignment_type: str, verbose: bool = True):
    """
    Generation of sample dataset for causal learning algorithms.

    Args:
        assignment_type(str): This option can be either 'variable_assignment' or 'observation_assignment'.
        verbose (bool): Set False if less logs are required. Defaults to True.

    Returns:
        Pandas.DataFrame: The generated dataset for experimental purposes.
    """

    # The adjacency matrix of actual causal graph
    adj = np.array([[0.0, 0.0, 0.0, 3.0, 0.0, 0.0],
                    [3.0, 0.0, 2.0, 0.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 6.0, 0.0, 0.0],
                    [0.0, 0.0, 0.0, 0.0, 0.0, 0.0],
                    [8.0, 0.0, -1.0, 0.0, 0.0, 0.0],
                    [4.0, 0.0, 0.0, 0.0, 0.0, 0.0]])

    # Causal ordering is important for automation purposes
    ordering = [3, 0, 2, 1, 4, 5]

    assignment = dict()
    if assignment_type == 'variable_assignment':

        # Variable assignment dictionary
        assignment = {1: ['X0', 'X1', 'X2'], 2: ['X1', 'X2', 'X3', 'X4']}

    elif assignment_type == 'observation_assignment':

        # Observation assignment percentages dictionary
        assignment = {0: 30, 1: 10, 2: 5, 3: 7, 4: 8, 5: 20}

    # Build and return the dataset
    df = build_experimental_dataset(adjacency_matrix=adj, causal_order=ordering,
                                    assignment=assignment, verbose=verbose)
    return df


def build_experimental_dataset(adjacency_matrix: np.ndarray, causal_order: List,
                               assignment: Dict[int, List[str]] or Dict[int, float],
                               assignment_type: str = 'observation_assignment',
                               file_name: str = 'experimental_data',
                               noise_distribution: str = 'uniform',
                               observation_size: int = DEFAULT_OBSERVATION_SIZE,
                               verbose: bool = False):
    """
    Build an experimental dataset to be used in inference techniques and
    local clients of distributed network.

    TODO: Support more noise distributions.

    Args:
        adjacency_matrix (np.ndarray): The adjacency matrix of the data.
        assignment (Dict[int: List[str]] or Dict[int, float]): Provides the data assignment dictionary.
        assignment_type (str): This option can be either 'variable_assignment' or 'observation_assignment'.
        causal_order (List[int]): The causal order of variables in the adjacency matrix.
        file_name (str): The name of the data when saved as a file.
        noise_distribution (str): The noise distribution, defaults to 'uniform'.
        observation_size (int): The total number of observations to be generated.
        verbose (bool): Show details about dataset after build or not. Defaults to False.
    """

    # Create an array to store generated data
    data = np.zeros((len(causal_order), observation_size))

    # Determine the noise distribution
    n_dist = None
    if noise_distribution == 'uniform':
        n_dist = np.random.uniform
    elif noise_distribution == 'gaussian':
        pass

    for variable_index in causal_order:

        # Additive noise based on noise distribution
        if n_dist is not None:
            data[variable_index] += n_dist(size=observation_size)

        for element in causal_order[:causal_order.index(variable_index)]:
            data[variable_index] += adjacency_matrix[variable_index][element] * data[element]

    data_frame = pd.DataFrame(data=data.transpose(),
                              index=range(observation_size),
                              columns=['X' + str(i) for i in range(len(causal_order))])

    # Save the data frame as csv file
    data_frame.to_csv(path_or_buf=os.path.join(os.pardir, 'data', file_name + '_dataset.csv'), index=False)

    # Save the adjacency matrix with numpy
    save_data_object(adjacency_matrix, file_name + '_adjacency_matrix', 'data')

    # Save the assignment dictionary
    save_data_object(assignment, file_name + f'_{assignment_type}', 'data')

    # Show details of dataset
    if verbose:
        logger.info(f'Dataset generated: \n Name: {file_name} \t Size: {data_frame.shape} '
                    f'\t Additive Noise: {noise_distribution}\n')
    # Return  the dataframe
    return data_frame


def generate_accessible_percentages(number_of_clients: int,
                                    minimum_accessible_percentage: float,
                                    maximum_accessible_percentage: float,
                                    is_randomized: bool = False) -> Dict[int, float]:
    """
    This generates randomized accessible percentages for a fixed number of clients. The results can only
    be used in 'observation_assignment' mode of the datasets.

    Args:
        number_of_clients (int): The total number of clients who want to have access.
        minimum_accessible_percentage (float): Maximum possible access percentage.
        maximum_accessible_percentage (float): Minimum possible access percentage.
        is_randomized (bool): If set true, the percentages would be randomized, otherwise
        a sweep between minimum and maximum is provided.

    Returns:
        Dict[int, float]: The percentages associated with clients.
    """

    assignment_dictionary: Dict[int, float] = dict()

    if not is_randomized:
        access_values_list = \
            np.linspace(minimum_accessible_percentage,
                        maximum_accessible_percentage, num=number_of_clients)

        assignment_dictionary = \
            {client_id + 1: accessible_percentage
             for client_id, accessible_percentage in enumerate(access_values_list)}

    else:
        for client_id in range(1, number_of_clients + 1):
            assignment_dictionary[client_id] = random.uniform(minimum_accessible_percentage,
                                                              maximum_accessible_percentage)

    return assignment_dictionary


def evaluate_inferred_matrix(true_matrix: np.ndarray, predicted_matrix: np.ndarray,
                             sdh_double_for_anticausal: bool = False) -> Dict[str, float]:
    """
    Perform evaluation of results with various integrated metrics.

    Note: For SHD and SID, their values tends to zero as the graphs get more identical.

    Args:
        true_matrix (numpy.ndarray): The original and correct (known) adjacency matrix.
        predicted_matrix (numpy.ndarray): The predicted adjacency matrix, inferred by a
        DAG structure learning algorithm.

        sdh_double_for_anticausal (bool): In SDH method, count the wrong arrows as 2
        errors instead of 1. Defaults to False.

    Returns:
        Dict[str: float]: The evaluation result dictionary.
    """

    # Convert a weighted matrix to (binary) adjacency matrix
    true_structure = weighted_matrix_to_binary(true_matrix)
    predicted_structure = weighted_matrix_to_binary(predicted_matrix)

    # Create the evaluation dictionary
    evaluation_dict: Dict[str, float] = dict()

    # Structural Hamming Distance metric
    evaluation_dict['SHD'] = SHD(true_structure,
                                 predicted_structure)

    # Euclidean distance of two matrix
    evaluation_dict['ED'] = np.linalg.norm(true_matrix - predicted_matrix)

    return evaluation_dict


def weighted_matrix_to_binary(matrix: np.ndarray) -> np.ndarray:
    """
    Convert an adjacency matrix which is organized for a weighted graph into a
    binary one, usually to use scoring techniques.

    Args:
        matrix (np.ndarray): The input weighted adjacency matrix.

    Returns:
        matrix (np.ndarray): Binary adjacency matrix.
    """

    binary_matrix: np.ndarray = matrix > 0.5
    return binary_matrix.astype(int)


def save_data_object(input_object, file_name: str, save_directory: str):
    """
    Save the passed dictionary.

    Args:
        input_object: Dictionary to be stored.
        file_name (str): Name of the file to be stored.
        save_directory (str): Directory of the stored file relative to the main project folder.
        Defaults to Output folder.
    """

    np.save(os.path.join(save_directory, file_name + '.npy'), input_object)


def load_data_object(file_name: str, save_directory: str):
    """
    Save the passed dictionary.

    Args:
        file_name (str): Name of the file to be loaded.
        save_directory (str): Directory of the loaded file relative to the main project folder.

    Returns:
        Object: The loaded object from a given directory and file.
    """

    return np.load(os.path.join(save_directory, file_name + '.npy'), allow_pickle=True)


def retrieve_dsdi_stored_data(dir: str, experiment_id: int, round_id: int):
    """
    Load all the information stored by DSDI clients in the work directory of
    the DSDI sub-module.

    Args:
        experiment_id (int): The id of experiment folder.
        round_id (int): Identifier determining the round number for which the data must be retrieved.

    Returns:
        np.ndarray: An array containing adjacency matrix and accessible percentage.
    """

    load_dir = f'{dir}/experiment_{experiment_id}/Gamma_Data_{round_id}_*'
    
    for filename in glob.glob(load_dir):
        yield np.load(filename, allow_pickle=True)


def resume_dsdi_experiments(basename: str = 'experiment_') -> int:

    # Check whether a re-start job has occurred in the cluster
    load_dir = 'work/'

    existing_experiments_ids = list()
    for filename in glob.glob(f'{load_dir}{basename}*'):
        id_str = filename.replace(f'{load_dir}{basename}', '')
        existing_experiments_ids.append(int(id_str))

    # Redo the last and perhaps unfinished experiment
    start_from = 0

    if len(existing_experiments_ids) != 0:
        logger.info(f'Found the following experiments: {existing_experiments_ids}')
        start_from = max(existing_experiments_ids)

    return start_from
