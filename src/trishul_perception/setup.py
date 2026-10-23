import os
from glob import glob
from setuptools import find_packages, setup

package_name = 'trishul_perception'

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
        (os.path.join('share', package_name, 'models'),
            glob('models/*.pt')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='Trishul Integration Team',
    maintainer_email='integration@trishul.dev',
    description='Trishul UGV YOLO Perception & Camera Processing',
    license='Apache-2.0',
    extras_require={'test': ['pytest']},
    entry_points={
        'console_scripts': [
            'image_processor = trishul_perception.image_processor:main',
            'keyboard_teleop = trishul_perception.keyboard_teleop:main',
            'safety_controller = trishul_perception.safety_controller:main',
        ],
    },
)
