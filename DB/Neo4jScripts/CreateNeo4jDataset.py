# Import libraries
from neo4j import GraphDatabase
import configparser
import sys

# Import functions
from PublicationsNodes import create_publications_nodes
from ToolRelatedNodes import create_tools_nodes
from CitationsEdges import citations_edges
from DataScience import add_clusters_pageRank_Database

from DataWebpage import CreateToolsTopicsList

config_path = sys.argv[1]


def readIni(config_path):
    config = configparser.ConfigParser()
    config.read(config_path)
    dict_config = {}
    for section in config.sections():
        for key in config[section]:
            dict_config[key] = config[section][key]
    return dict_config


def main():
    dict_config = readIni(config_path)
    
    # URL of the Neo4j Server
    uri = dict_config['url_neo4j_server']
    # Driver to connect to the Server with the author and the password
    # To be able to use it, you need to open your neo4j server before
    driver = GraphDatabase.driver(uri, auth=(dict_config['user'], dict_config['password']))

    create_publications_nodes(driver, dict_config["publication_nodes"])
    create_tools_nodes(driver, dict_config)
    citations_edges(driver, dict_config["metaoccur_edges"])
    add_clusters_pageRank_Database(driver, dict_config["tool_nodes"])
    CreateToolsTopicsList(driver)


if __name__ == '__main__':
    main()
