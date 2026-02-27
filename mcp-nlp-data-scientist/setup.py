from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setup(
    name="mcp-standard-server",
    version="1.0.0",
    author="Qwen Team",
    author_email="",
    description="A standard-compliant Model Context Protocol (MCP) server implementation",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.104.1",
        "uvicorn>=0.24.0",
        "sse-starlette>=1.8.2",
        "psycopg2-binary>=2.9.7",
        "requests>=2.31.0",
    ],
    entry_points={
        "console_scripts": [
            "mcp-standard-server=mcp_std_server.server:main",
        ],
    },
)