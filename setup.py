from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="ResearchQuantize",
    version="1.1",
    author="Desenyon",
    author_email="Desenyon@gmail.com",
    description="A command-line tool to aggregate and search research papers from multiple sources.",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/desenyon/ResearchQuantize",
    packages=find_packages(where="src"),  # Find packages in the `src` directory
    package_dir={"": "src"},  # Specify that packages are under `src`
    include_package_data=True,
    install_requires=[
        "requests>=2.28.1",
        "rich>=12.6.0",
        "lxml>=4.9.2",
        "beautifulsoup4>=4.11.1",
        "scholarly>=1.5.0",
        "python-dotenv>=0.21.0",
    ],
    entry_points={
        "console_scripts": [
            "paperengine=cli:main",  # Correct entry point
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
)
