import setuptools

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()
    
setuptools.setup(
    name='xmlorm',
    version='0.0.3',
    author='Alexander Goryunov',
    author_email='alex.goryunov@gmail.com',
    description='A basic XML to SQL converter',
    long_description=long_description,
    long_description_content_type="text/markdown",
    url='https://github.com/agoryuno/xml_orm',
    license='MIT',
    packages=['xmlorm'])
