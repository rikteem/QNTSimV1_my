from setuptools import setup

setup(
    name="qntsim",
    version="0.1.1",
    author="Qulabs Software India Pvt Ltd",
    description="Quantum Network Simulator for quick prototyping and developement of protocols and applications",
    # packages = find_packages('src'),
    packages=['qntsim',
              'qntsim.communication',
              'qntsim.components',
              'qntsim.entanglement_management',
              'qntsim.kernel',
              'qntsim.network_management',
              'qntsim.resource_management',
              'qntsim.topology',
              'qntsim.transport_layer' ,
              'qntsim.utils'],
    package_dir={'qntsim': 'src'},
    package_data={"qntsim":["logging.ini"]},
    install_requires=[
        'numpy',
	'matplotlib',
        'json5',
        'pandas',
        'qutip'
    ],
)
