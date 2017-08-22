'''
Copyright 2017 John Torakis

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

 http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
'''

import imp
import sys
import logging

from contextlib import contextmanager
try :
    from urllib2 import urlopen
except :
    from urllib.request import urlopen

__author__ = 'John Torakis - operatorequals'
__version__ = '0.1.0'


FORMAT = "%(message)s"
logging.basicConfig(format=FORMAT)

logger = logging.getLogger(__name__)
logger.setLevel(logging.WARN)


class HttpImporter(object):
 
    def __init__(self, modules, base_url):
        self.module_names = modules
        self.base_url = base_url+'/'


    def find_module(self, fullname, path=None):
        logger.debug("FINDER=================")
        logger.debug("[!] Searching %s" % fullname)
        logger.debug("[!] Path is %s" % path)
        logger.info("[@]Checking if in domain >")
        if fullname.split('.')[0] not in self.module_names : return None

        logger.info("[@]Checking if built-in >")
        try :
            loader = imp.find_module( fullname, path )
            if loader : return None
        except ImportError:
            pass
        logger.info("[@]Checking if it is name repetition >")
        if fullname.split('.').count(fullname.split('.')[-1]) > 1 : return None


        logger.info("[*]Module/Package '%s' can be loaded!" % fullname)
        return self
 

    def load_module(self, name):
        imp.acquire_lock()
        logger.debug("LOADER=================")
        logger.debug( "[+] Loading %s" % name )
        if name in sys.modules:
            logger.info( '[+] Module "%s" already loaded!' % name )
            imp.release_lock()
            return sys.modules[name]

        if name.split('.')[-1] in sys.modules:
            imp.release_lock()
            logger.info('[+] Module "%s" loaded as a top level module!' % name)
            return sys.modules[name.split('.')[-1]]

        module_url = self.base_url + '%s.py'  % name.replace('.','/')
        package_url = self.base_url + '%s/__init__.py'  % name.replace('.','/')
        final_url = None
        final_src = None

        try :
            logger.debug("[+] Trying to import as package from: '%s'" % package_url)
            package_src = urlopen(package_url).read()
            final_src = package_src
            final_url = package_url
        except IOError as e:
            package_src = None
            logger.info( "[-] '%s' is not a package:" % name )

        if final_src == None :
            try :
                logger.debug("[+] Trying to import as module from: '%s'" % module_url)
                module_src = urlopen(module_url).read()
                final_src = module_src
                final_url = module_url
            except IOError as e:
                module_src = None
                logger.info( "[-] '%s' is not a module:" % name )
                logger.warn( "[!] '%s' not found in HTTP repository. Moving to next Finder." % name )
                imp.release_lock()
                return None

        logger.debug("[+] Importing '%s'" % name)
        mod = imp.new_module(name)
        mod.__loader__ = self
        mod.__file__ = final_url
        if not package_src :
            mod.__package__ = name
        else :
            mod.__package__ = name.split('.')[0]

        mod.__path__ = ['/'.join(mod.__file__.split('/')[:-1])+'/']
        logger.debug( "[+] Ready to execute '%s' code" % name )
        sys.modules[name] = mod
        exec(final_src, mod.__dict__)    
        logger.info("[+] '%s' imported succesfully!" % name)
        imp.release_lock()
        return mod
 


@contextmanager
def remote_repo( modules, base_url = 'http://localhost:8000/' ):    # Default 'python -m SimpleHTTPServer' URL
    importer = addRemoteRepo( modules, base_url )
    yield
    removeRemoteRepo(base_url)


def addRemoteRepo( modules, base_url = 'http://localhost:8000/' ) :    # Default 'python -m SimpleHTTPServer' URL
    importer = HttpImporter( modules, base_url )
    sys.meta_path.append( importer )
    return importer


def removeRemoteRepo( base_url ) :
    for importer in sys.meta_path :
        try :
            if importer.base_url[:-1] == base_url : # an extra '/' is always added
                sys.meta_path.remove( importer )
                return True
        except Exception as e :
                return False


__all__ = ['remote_repo', 'addRemoteRepo', 'removeRemoteRepo', 'HttpImporter']