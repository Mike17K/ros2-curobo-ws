from glob import glob

from setuptools import find_packages, setup
from setuptools.command.develop import develop


class DevelopWithEditable(develop):
    user_options = develop.user_options + [
        ("editable", None, "Ignored for colcon symlink install"),
        ("build-directory=", None, "Ignored for colcon symlink install"),
        ("no-deps", None, "Ignored for colcon symlink install"),
        ("script-dir=", None, "Script install directory"),
    ]

    def initialize_options(self):
        super().initialize_options()
        self.editable = None
        self.build_directory = None
        self.no_deps = False
        self.script_dir = None

    def finalize_options(self):
        super().finalize_options()

package_name = 'image_to_depth_generation'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (f'lib/{package_name}', ['scripts/depth_anything_v2_node']),
        ('share/image_to_depth_generation/launch', glob('launch/*.py')),

    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='kaipis',
    maintainer_email='kaipismike1@gmail.com',
    description='TODO: Package description',
    license='TODO: License declaration',
    extras_require={
        'test': [
            'pytest',
        ],
    },
    cmdclass={
        "develop": DevelopWithEditable,
    },
    entry_points={
        "console_scripts": [
            "depth_anything_v2_node = image_to_depth_generation.depth_anything_v2_node:main",
            "depth_analyzer_node = image_to_depth_generation.depth_analyzer_node:main",
        ],
    },
)
