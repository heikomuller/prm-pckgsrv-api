"""prm Package Web Service API - Implements the API methods that are called
by the Web server.

The API module separates the implementation from the specifics of the Web server
(e.g., Flask or Tornado).
"""

import datetime as dt
import os
import yaml

import prmpckgsrv.const as const
from prmpckgsrv.hateoas import UrlFactory, reference, self_reference


"""Frequently used serialization element labels."""
JSON_REFERENCES = 'links'


"""HATEOAS relation identifier."""
REL_APIDOC = 'doc';
REL_PACKAGES = 'packages'
REL_SERVICE = 'home'


class ModuleSpecification(object):
    """Specification of a package module. Expects a dictionary containing the
    module specification.

    Attributes
    ----------
    identifier: string
        Full module path containing the module folder and name
    """
    def __init__(self, obj):
        """Initialize from dict.

        Parameters
        ----------
        obj: dict
        """
        self.obj = obj
        self.identifier = self.obj['folder']
        if self.identifier == '':
            self.identifier = self.obj['name']
        else:
            self.identifier = self.identifier + '.' + self.obj['name']


    def matches(self, query):
        path = self.identifier.split('.')
        if len(path) >= len(query):
            for i in range(len(query)):
                if path[i] != query[i]:
                    return False
            return True
        return False

    def to_dict(self):
        return self.obj


class PackageDescriptor(object):
    """Descriptor for a package that is available on the server.

    Attributes
    ----------
    name: string
        Unique package name
    description: string, optional
        Optional package description
    version: string
        Package version information
    timestamp: datetime
        Timestamp of package creation
    file: string
        Path to package file
    """
    def __init__(self, name, file, version, timestamp, description=None):
        """Initialize package descriptor.

        Parameters
        ----------
        name: string
            Unique package name
        file: string
            Path to package file
        version: string
            Package version information
        timestamp: datetime
            Timestamp of package creation
        description: string, optional
            Optional package description
        """
        self.name = name
        self.file = file
        self.timestamp = timestamp
        self.version = version
        self.description = description


class PrmPackageServer(object):
    """The Web Service API implements the methods that correspond to the Http
    requests that are handled by the Web server.

    Package information is managed in a Yaml file that is expected to be of
    the following format:
    - packages:
      - name         : Unique package name
      - file         : Absolute path to package definition file
    """
    def __init__(self, config):
        """Initialize the API from a configuration dictionary. Expects the
        following keys to be present in the dictionary:
        - APP_NAME : Application (short) name for the service description
        - API_DOC : Url for API documentation
        - DOWNLOAD_URLPREFIX: Url prefix for module download tasks.
        - PACKAGE_INDEXFILE: Index file for package information
        - SERVER_APP_PATH : Application path part of the Url to access the app
        - SERVER_URL : Base Url of the server where the app is running
        - SERVER_PORT : Port the server is running on

        Raises ValueError if (1) the configuration file misses required
        parameters, (2) the package index file does not exist, or (3) the
        package index file is not in the expected format.

        Parameters
        ----------
        config : dict
            Dictionary with configuration parametera
        """
        self.index_file = os.path.abspath(config[const.PACKAGE_INDEXFILE])
        if not os.path.isfile(self.index_file):
            raise ValueError('unknown file \'' + self.index_file + '\'')
        # Read index file to ensure that it is valid
        read_index_file(self.index_file)
        # Initialize the download Url prefix
        self.download_prefix = config[const.DOWNLOAD_URLPREFIX]
        while self.download_prefix.endswith('/'):
            self.downoad_prefix = self.download_prefix[:-1]
        # Initialize the factory for API resource Urls
        self.urls = UrlFactory(config)
        # Initialize the service description dictionary
        self.service_descriptor = {
            'name' : config[const.APP_NAME],
            JSON_REFERENCES : [
                self_reference(self.urls.service_url()),
                reference(REL_PACKAGES, self.urls.packages_url()),
                reference(REL_APIDOC, config[const.API_DOC])
            ]
        }

    # --------------------------------------------------------------------------
    # Service
    # --------------------------------------------------------------------------
    def service_overview(self):
        """Returns a dictionary containing essential information about the web
        service including HATEOAS links to access resources and interact with
        the service.

        Returns
        -------
        dict
        """
        return self.service_descriptor

    # --------------------------------------------------------------------------
    # Packages
    # --------------------------------------------------------------------------
    def get_package_modules(self, package_query):
        """Get descriptors for all modules that match the given package query.
        Queries are path expressions (using '.' as path delimiter) starting with
        a package name.

        Parameters
        ----------
        package_query: string
            Path expression (using '.' as delimiter) referencing a package or a
            package folder.

        Returns
        -------
        dict
        """
        packages = read_index_file(self.index_file)
        query = package_query.split('.')
        package_name = query[0]
        if not package_name in packages:
            return None
        modules = list()
        package = packages[package_name]
        for module in read_modules(package.file, self.download_prefix):
            if module.matches(query[1:]):
                m = module.to_dict()
                m[JSON_REFERENCES] = [
                    self_reference(
                        self.urls.module_url(
                            package_name + '.' + module.identifier
                        )
                    )
                ]
                modules.append(m)
        return {
            'modules' : modules,
            JSON_REFERENCES : [
                self_reference(self.urls.module_url(package_query)),
                reference(
                    REL_PACKAGES,
                    self.urls.packages_url()
                ),
                reference(
                    REL_SERVICE,
                    self.urls.service_url()
                )
            ]
        }

    def list_packages(self):
        """Get list of packages that are  currently available from the server.

        Returns
        -------
        dict
        """
        packages = read_index_file(self.index_file)
        return {
            'packages': [
                self.serialize_package_descriptor(packages[p])
                    for p in packages
            ],
            JSON_REFERENCES : [
                self_reference(self.urls.packages_url()),
                reference(
                    REL_SERVICE,
                    self.urls.service_url()
                )
            ]
        }

    def serialize_package_descriptor(self, package):
        """Create dictionary serialization for dataset instance.

        Parameters
        ----------
        f_handle : database.fileserver.FileHandle
            Handle for file server resource

        Returns
        -------
        dict
        """
        self_ref = self.urls.module_url(package.name)
        obj = {
            'name' : package.name,
            'version' : package.version,
            'timestamp': package.timestamp.isoformat(),
            JSON_REFERENCES : [
                self_reference(self_ref),
                reference(
                    REL_PACKAGES,
                    self.urls.packages_url()
                )
            ]
        }
        if not package.description is None:
            obj['description'] = package.description
        return obj


# ------------------------------------------------------------------------------
# Helper Methods
# ------------------------------------------------------------------------------

def read_index_file(filename):
    """Read the package index file. Ensures that the file contains an array of
    package descriptiors with the following elements: name, and file.

    From each referenced file the (optional) description, timestamps and
    version information is extracted and added to the package descriptor.

    Returns a dictionary of package descriptors keyed by the package name.

    Raises ValueError if the index file is not valid or if it contains duplicate
    package descriptors.

    Parameters
    ----------
    filename: string
        Path to the Yaml file (expected to be in Yaml format)

    Returns
    -------
    dict(PackageDescriptor)
    """
    packages = dict()
    with open(filename, 'r') as f:
        try:
            doc = yaml.load(f.read())
        except yaml.YAMLError as ex:
            raise ValueError(str(ex))
    if not 'packages' in doc:
        raise ValueError('index file is missing element \'packages\'')
    for obj in doc['packages']:
        for key in ['name', 'file']:
            if not key in obj:
                raise ValueError('package descriptor is missing element \'' + key + '\'')
        name = obj['name']
        if name in packages:
            raise ValueError('duplicate package descriptor \'' + name + '\'')
        package_file = os.path.abspath(obj['file'])
        if not os.path.isfile(package_file):
            raise ValueError('package file \'' + package_file + '\' does not exist')
        try:
            with open(package_file, 'r') as f:
                pckg = yaml.load(f.read())
        except yaml.YAMLError as ex:
            raise ValueError(str(ex))
        for key in ['timestamp', 'version']:
            if not key in pckg:
                raise ValueError('package descriptor is missing element \'' + key + '\'')
        version = pckg['version']
        timestamp = dt.datetime.strptime(pckg['timestamp'], '%Y-%m-%dT%H:%M:%S')
        if 'description' in pckg:
            description = pckg['description']
        else:
            description = None
        packages[name] = PackageDescriptor(
            name,
            package_file,
            version,
            timestamp,
            description=description
        )
    return packages


def read_modules(filename, download_prefix):
    """Get list of module descriptors in a package file.

    Parameters
    ----------
    filename: string
        Path to package definoition file
    download_prefix: string
        Url prefix for download sources

    Returns
    -------
    list(ModuleSpecification)
    """
    modules = list()
    with open(filename, 'r') as f:
        try:
            doc = yaml.load(f.read())
        except yaml.YAMLError as ex:
            raise ValueError(str(ex))
    if 'modules' in doc:
        for obj in doc['modules']:
            if 'install' in obj:
                for task in obj['install']['tasks']:
                    if task['type'] == 'DOWNLOAD':
                        for prop in task['properties']:
                            if prop['name'] == 'source':
                                prop['value'] = download_prefix + '/' + prop['value']
            modules.append(ModuleSpecification(obj))
    return modules
