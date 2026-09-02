from setuptools import setup

setup(
    name="airadb",
    version="1.0.0",
    description="Cross-Device Wireless Android Debugging Assistant",
    py_modules=["server", "adb_manager", "cli"],
    packages=["public"],
    package_data={"public": ["*.*"]},
    include_package_data=True,
    entry_points={
        "console_scripts": [
            "airadb=server:main",
        ],
    },
)
