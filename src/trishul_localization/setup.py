import os
from glob import glob
from setuptools import setup
package_name = 'trishul_localization'
setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'config'), glob('config/*.yaml')),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='omkar',
    description='TRISHUL Localization and Mapping',
    license='MIT',
    entry_points={
        'console_scripts': [
            'visual_odometry = trishul_localization.visual_odometry_node:main',
            'depth_to_laserscan = trishul_localization.depth_to_laserscan_node:main',
            'frame_broadcaster = trishul_localization.frame_broadcaster_node:main',
        ],
    },
)
