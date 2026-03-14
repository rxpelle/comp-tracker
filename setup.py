from setuptools import setup, find_packages

setup(
    name='comp-tracker',
    version='0.1.0',
    description='Track comp title BSR over time and detect declining relevance',
    long_description=open('README.md').read(),
    long_description_content_type='text/markdown',
    author='Randy Pellegrini',
    license='MIT',
    packages=find_packages(),
    python_requires='>=3.9',
    install_requires=[
        'click>=8.0',
        'rich>=13.0',
        'pyyaml>=6.0',
    ],
    extras_require={
        'dev': [
            'pytest',
            'pytest-cov',
        ],
    },
    entry_points={
        'console_scripts': [
            'comp-tracker=comp_tracker.cli:main',
        ],
    },
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Intended Audience :: End Users/Desktop',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
)
