from setuptools import setup, find_packages

setup(
    name="yaif",
    version="0.1.0",
    package_dir={"": "."},
    packages=find_packages(),
    py_modules=[],
    install_requires=[],
    entry_points={
        "console_scripts": [
            "yaif=yaif.__main__:main",
        ],
    },
    author="SamTechAV",
    description="Yet Another Interface File - a lightweight schema language and multi-target code generator",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/SamTechAV/Yet-Another-Interface-File",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Software Development :: Libraries",
    ],
    python_requires=">=3.10",
    include_package_data=True,
)
