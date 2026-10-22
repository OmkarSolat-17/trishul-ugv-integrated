from glob import glob
import os

from setuptools import find_packages, setup

package_name = 'trishul_navigation'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'),
            glob('launch/*launch.[pxy][yma]*')),
        (os.path.join('share', package_name, 'config'),
            glob('config/*.yaml')),
        (os.path.join('share', package_name, 'rviz'),
            glob('rviz/*.rviz')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='kshitij',
    maintainer_email='munikshitij@gmail.com',
    description='Trishul UGV autonomous navigation and active safety package',
    license='Apache-2.0',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    entry_points={
        'console_scripts': [
            'status_node = trishul_navigation.status_node:main',
            'sensor_monitor = trishul_navigation.sensor_monitor:main',
            'mission_navigator = trishul_navigation.mission_navigator:main',
        ],
    },
)
