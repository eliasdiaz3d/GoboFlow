from setuptools import setup, find_packages

setup(
    name="goboflow",
    version="0.1.0",
    description="Node-based procedural gobo design tool",
    author="GoboFlow Team",
    packages=find_packages(),
    install_requires=[
        "PySide6>=6.5.0",
        "numpy>=1.21.0",
        "Pillow>=9.0.0",
        "scipy>=1.7.0",
        "shapely>=1.8.0",
        "noise>=1.2.2",
    ],
    entry_points={
        "console_scripts": [
            "goboflow=main:main",
        ],
    },
    python_requires=">=3.8",
)
