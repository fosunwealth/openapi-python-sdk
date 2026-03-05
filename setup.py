from setuptools import setup, find_packages

setup(
    name="fsopenapi",
    version="0.1.0",
    description="Fosun Wealth OpenAPI Python SDK",
    python_requires=">=3.8",
    packages=find_packages(include=["fsopenapi*"]),
    install_requires=[
        "requests>=2.28.0",
        "cryptography>=41.0.0",
    ],
)
