"""
Setup script for the claim verification system.
"""

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="claim-verification",
    version="0.1.0",
    author="HackMIT 2025 Team",
    description="A parallel agent-based system for real-time political claim verification",
    long_description=long_description,
    long_description_content_type="text/markdown",
    packages=find_packages(),
    python_requires=">=3.9",
    install_requires=[
        "langchain>=0.3.0",
        "langchain-anthropic>=0.2.0",
        "langgraph>=0.2.0",
        "composio-langchain>=0.6.0",
        "crawl4ai>=0.4.0",
        "pydantic>=2.0",
        "python-dotenv>=1.0.0",
        "asyncio",
        "aiohttp",
        "typing-extensions>=4.0.0",
    ],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
)
