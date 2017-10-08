"""prm Package Web Service API -  Factory for Web API resource Urls following
Hypermedia As The Engine of Application State constraints.

The Web API attempts to follow the Hypermedia As The Engine of Application State
(HATEOAS) constraint. Thus, every serialized resource contains a list of
references for clients to interact with the API.

The URLFactory class in this module contains all methods to generate HATEOAS
references for resources that are accessible via the prm Package Server Web API.
"""

import prmpckgsrv.const as const


class UrlFactory:
    """Factory for API resource Urls. Contains the definitions of Url's for any
    resource that is accessible through the Web API in a single class.

    Attributes
    ----------
    base_url : string
        Prefix for all resource Url's
    """
    def __init__(self, config):
        """Intialize the common Url prefix for all API resources. Expectes a
        dictioary that contains the following keys:

        - SERVER_APP_PATH : Application path part of the Url to access the app
        - SERVER_URL : Base Url of the server where the app is running
        - SERVER_PORT : Port the server is running on

        Parameters
        ----------
        config : dict
            Dictionary for configuration parameter
        """
        # Construct base Url from server url, port, and application path.
        self.base_url = config[const.SERVER_URL]
        if config[const.SERVER_PORT] != 80:
            self.base_url += ':' + str(config[const.SERVER_PORT])
        self.base_url += config[const.SERVER_APP_PATH]
        # Ensure that base_url does not end with a slash
        while len(self.base_url) > 0:
            if self.base_url[-1] == '/':
                self.base_url = self.base_url[:-1]
            else:
                break

    def packages_url(self):
        """Url to retrieve package listing.

        Returns
        -------
        string
        """
        return self.service_url() + '/packages'

    def module_url(self, module_id):
        """Url to retrieve module descriptor.

        Returns
        -------
        string
        """
        return self.packages_url() + '/' + module_id

    def service_url(self):
        """Base Url for the Web API server.

        Returns
        -------
        string
        """
        return self.base_url


# ------------------------------------------------------------------------------
#
# Helper Methods
#
# ------------------------------------------------------------------------------

def reference(rel, href):
    """Get HATEOAS reference object containing the Url 'href' and the link
    relation 'rel' that defines the type of the link.

    Parameters
    ----------
    rel : string
        Descriptive attribute defining the link relation
    href : string
        Http Url

    Returns
    -------
    dict
        Dictionary containing elements 'rel' and 'href'
    """
    return {'rel' : rel, 'href' : href}


def self_reference(url):
    """Get HATEOAS self reference for a API resources.

    Parameters
    ----------
    url : string
        Url to resource

    Returns
    -------
    dict
        Dictionary containing elements 'rel' and 'href'
    """
    return reference('self', url)
