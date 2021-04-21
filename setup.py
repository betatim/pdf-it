import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pdfit",
    version="0.0.1",
    author="Tim Head",
    author_email="betatim@gmail.com",
    description="A simple webserver to convert documents to PDFs",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/betatim/pdf-it",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
        "Topic :: Communications :: Email",
        "Topic :: Communications :: Email :: Mail Transport Agents",
    ],
    python_requires=">=3.9",
    install_requires=["tornado"],
    entry_points={
        "console_scripts": [
            "pdfitapp = pdfit.app:main",
        ],
    },
)
