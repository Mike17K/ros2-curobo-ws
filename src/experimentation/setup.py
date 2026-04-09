from setuptools import find_packages, setup

package_name = "experimentation"

setup(
    name=package_name,
    version="0.0.0",
    packages=find_packages(exclude=["test"]),
    data_files=[
        ("share/ament_index/resource_index/packages", ["resource/" + package_name]),
        ("share/" + package_name, ["package.xml"]),
    ],
    install_requires=[
        "setuptools",
        "shared_utils",
        "matplotlib",
        "scipy",
        "numpy",
    ],
    zip_safe=True,
    maintainer="root",
    maintainer_email="root@todo.todo",
    description="TODO: Package description",
    license="TODO: License declaration",
    extras_require={},
    entry_points={
        "console_scripts": [
            "lqr_test = experimentation.lqr_test:main",
            "pole_placement_test = experimentation.pole_placement_test:main",
            "kalman_filter_test = experimentation.kalman_filter_test:main",
            "tvlqr_test = experimentation.tvlqr_test:main",
            "ilqr_test = experimentation.ilqr_test:main",
            "mpc_test = experimentation.mpc_test:main",
        ],
    },
)
