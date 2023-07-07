import logging
from statistics import mean, stdev

import matplotlib.pyplot as plt
import numpy as np
from joblib import Parallel, delayed, wrap_non_picklable_objects
from numpy.random import randint

from .network import Network


class ErrorAnalyzer:
    @staticmethod
    # @delayed
    # @wrap_non_picklable_objects
    def _analyse(network: Network, i: int = 0):
        err_list = np.zeros(len(network._bin_msgs[0]))
        lk_list = np.zeros(len(network._bin_msgs[0]))
        print(network._bin_msgs, network._strings)
        for bin_msg, string in zip(network._bin_msgs, network._strings[::-1]):
            err_list += np.array([int(m) ^ int(s) for m, s in zip(bin_msg, string)])
            lk_list += np.array(
                [
                    int(m) ^ int(lk)
                    for m, lk in zip(
                        bin_msg,
                        network._lk_msg if hasattr(network, "_lk_msgs") else bin_msg,
                    )
                ]
            )
        err_list /= len(network._bin_msgs)
        lk_list /= len(network._bin_msgs)
        err_prct = mean(err_list) * 100
        err_sd = stdev(err_list)
        info_lk = mean(lk_list) * 100
        logging.info(f"Avg. err. for iteration {i}: {err_prct}%")
        logging.info(f"Deviation in err. for iteration {i}: {err_sd}")
        logging.info(f"Fidelity of the message retained: {100-err_prct}%")
        logging.info(f"{info_lk}% info leaked to the attacker.")

        return err_list, lk_list, err_prct, err_sd, info_lk, 100 - err_prct

    from .protocol import ProtocolPipeline

    @classmethod
    def analyse(cls, protocol: ProtocolPipeline):
        """Analyse the networks present in protocol

        Args:
            protocol (Protocol): <Protocol> object

        Returns:
            _type_: _description_
        """
        return list(
            zip(*[cls._analyse(network, i=i) for i, network in enumerate(protocol, 1)])
        )
        # return Parallel(n_jobs=-1, prefer='threads') (cls._analyse(i, network) for i, network in enumerate(protocol, 1))

    @staticmethod
    def run_full_analysis(type_: int, num_iterations: int, message_length: int, **kwds):
        """Runs full analysis over the network

        Args:
            type_ (int): The type of protocol. QSDC is 0
            num_iterations (int): Total number of iterations to run through
            message_length (int): The length of the message
        """
        from .protocol import ProtocolPipeline

        messages_list = [
            {
                i: "".join(str(ele) for ele in randint(2, size=message_length))
                for i in range(type_)
            }
            for _ in range(num_iterations)
        ]
        protocol = ProtocolPipeline(**kwds, messages_list=messages_list)
        protocol(**kwds)
        attack = kwds.get("attack", "no")
        print(f"Error analysis for {attack} attack")
        bit_error = sum(protocol.full_err_list)
        bit_lk = sum(protocol.full_lk_list)
        plt.figure("Error per bit", figsize=(20, 5))
        plt.bar(range(len(bit_error)), bit_error)
        plt.xlabel("Bits")
        plt.ylabel(f"Error per bit for {num_iterations} iterations")
        plt.show()
        plt.figure("Info. leakage per bit", figsize=(20, 5))
        plt.bar(range(len(bit_lk)), bit_lk)
        plt.xlabel("Bits")
        plt.ylabel(f"Info. leak per bit for {num_iterations} iterations")
        plt.show()
        plt.figure("Error per iteration", figsize=(20, 5))
        plt.plot(range(len(protocol.mean_list)), protocol.mean_list)
        plt.xlabel("Number of iterations")
        plt.ylabel("Mean error per iteration")
        plt.show()
        plt.figure("Deviation in error per iteration", figsize=(20, 5))
        plt.plot(range(len(protocol.sd_list)), protocol.sd_list)
        plt.xlabel("Number of iterations")
        plt.ylabel("Mean deviation in error per iteration")
        plt.show()
        plt.figure("Info. leakege per iteration", figsize=(20, 5))
        plt.plot(range(len(protocol.lk_list)), protocol.lk_list)
        plt.xlabel("Number of iterations")
        plt.ylabel("Mean info. leakage per iteration")
        plt.show()
        plt.figure("Fidelity of message per iteration", figsize=(20, 5))
        plt.plot(range(len(protocol.fid_list)), protocol.fid_list)
        plt.xlabel("Number of iterations")
        plt.ylabel("Mean fidelity per iteration")
        plt.show()
        print(
            f"Avg. error over all the bits for {num_iterations} iterations: {mean(bit_error)}"
        )
        print(
            f"Avg. info. leakage over all the bits for {num_iterations} iterations: {mean(bit_lk)}"
        )
        print(
            f"Avg. mean error over all the {num_iterations} iterations: {mean(protocol.mean_list)}"
        )
        print(
            f"Avg. error deviation over all the {num_iterations} iterations: {mean(protocol.sd_list)}"
        )
        print(
            f"Avg. info. leakage over all the {num_iterations} iterations: {mean(protocol.lk_list)}"
        )
        print(
            f"Avg. fidelity over all the {num_iterations} iterations: {mean(protocol.fid_list)}"
        )
