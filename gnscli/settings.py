from pkg_resources import resource_stream
import yaml

GNS_REPOS = yaml.load(resource_stream(__name__, 'config.yaml')).get('GNS_GIT_NODES')
# print(GNS_REPOS)
