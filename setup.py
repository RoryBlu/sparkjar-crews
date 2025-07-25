"""
Setup configuration for sparkjar-crews package.

This package contains CrewAI crew implementations for the SparkJAR platform.
"""

from setuptools import setup, find_packages

# Read README for long description
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="sparkjar-crews",
    version="0.1.0",
    author="SparkJAR",
    author_email="admin@sparkjar.com",
    description="CrewAI crew implementations for SparkJAR platform",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/sparkjar/sparkjar-crews",
    packages=find_packages(exclude=["tests*", "test_*", "*.py"]),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.11",
    install_requires=[
        "sparkjar-shared>=0.1.0",
        "crewai>=0.63.6",
        "crewai-tools>=0.8.3",
        "langchain>=0.1.16",
        "langchain-openai>=0.1.7",
        "python-dotenv>=1.0.1",
        "pydantic>=2.0.0",
        "httpx>=0.24.0",
        "chromadb>=0.5.7",
        "sqlalchemy>=2.0.0",
        "psycopg2-binary>=2.9.9",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=23.0.0",
            "isort>=5.12.0",
            "mypy>=1.0.0",
        ]
    },
)