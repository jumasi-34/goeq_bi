from setuptools import setup, find_packages

setup(
    name="cqms_query",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy",
        "sqlalchemy",
    ],
    author="Your Name",
    author_email="your.email@example.com",
    description="CQMS Quality Issue Query Management Package",
    long_description=open("README.md").read() if open("README.md").readable() else "",
    long_description_content_type="text/markdown",
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
    ],
)
