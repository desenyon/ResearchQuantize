from pathlib import Path

from setuptools import find_packages, setup

ROOT = Path(__file__).parent
README = (ROOT / "README.md").read_text(encoding="utf-8")

setup(
    name="ResearchQuantize",
    version="2.0.0",
    author="Desenyon",
    author_email="Desenyon@gmail.com",
    description="Aggregate and search research papers from ArXiv, PubMed, and Semantic Scholar.",
    long_description=README,
    long_description_content_type="text/markdown",
    url="https://github.com/desenyon/ResearchQuantize",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    py_modules=["cli"],
    include_package_data=True,
    install_requires=[
        "requests>=2.31.0",
        "rich>=13.7.0",
        "python-dotenv>=1.0.1",
    ],
    entry_points={
        "console_scripts": [
            "researchquantize=cli:main",
        ],
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.9",
)
