import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'trishul_bringup'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*launch.[pxy][yma]*')),
        (os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')),
        (os.path.join('share', package_name, 'web'),
            glob('web/*.*')),
        (os.path.join('share', package_name, 'web', 'css'),
            glob('web/css/*.*')),
        (os.path.join('share', package_name, 'web', 'js'),
            glob('web/js/*.*')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Trishul Integration Team',
    maintainer_email='integration@trishul.dev',
    description='Trishul UGV Unified Demo Bringup & System Integration',
    license='Apache-2.0',
    extras_require={'test': ['pytest']},
    entry_points={
        'console_scripts': [
            'dashboard_server = trishul_bringup.dashboard_server:main',
            'system_coordinator = trishul_bringup.system_coordinator:main',
        ],
    },
)
