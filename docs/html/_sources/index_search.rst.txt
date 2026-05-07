Index and search
================

**Haystack**

The `Haystack <https://haystacksearch.org>`_ software enables the Django framework to run third party search engines such as Elasticsearch and Solr. Even though you can use any search engine supported by Haystack, machado was tested using `Elasticsearch <https://www.elastic.co/products/elasticsearch>`_.

Install Elasticsearch
---------------------

Elasticsearch 7.x is required. Install Java first:

.. code-block:: bash

    sudo apt install openjdk-11-jdk

Then install Elasticsearch:

.. code-block:: bash

    wget https://artifacts.elastic.co/downloads/elasticsearch/elasticsearch-7.17.26-amd64.deb
    sudo dpkg -i elasticsearch-7.17.26-amd64.deb
    sudo systemctl daemon-reload
    sudo systemctl enable elasticsearch.service
    sudo systemctl start elasticsearch.service

Install the Python client inside your virtualenv:

.. code-block:: bash

    pip install 'elasticsearch>=7,<8'

Enable search in machado
------------------------

Uncomment the Elasticsearch settings in your ``.env`` file:

.. code-block:: bash

    ELASTICSEARCH_URL=http://127.0.0.1:9200/
    HAYSTACK_INDEX_NAME=haystack

When ``ELASTICSEARCH_URL`` is set, machado automatically adds ``haystack`` to
``INSTALLED_APPS`` and configures ``HAYSTACK_CONNECTIONS`` — no manual editing
of ``settings.py`` is needed.

You can also configure which feature types are indexed:

.. code-block:: bash

    MACHADO_VALID_TYPES=gene,mRNA,polypeptide

If ``MACHADO_VALID_TYPES`` is not set, the default is ``gene,mRNA,polypeptide``.

Indexing the data
-----------------

After loading data into the database, build the search index:

.. code-block:: bash

    python manage.py rebuild_index

.. note::

    It is necessary to run ``rebuild_index`` whenever additional data is
    loaded into the database or when search-related settings change.

Rebuilding the index can be faster if you increase the number of workers:

.. code-block:: bash

    python manage.py rebuild_index -k 4

Increasing the results limit
-----------------------------

The Elasticsearch server has a 10,000 results limit by default. In most cases it will not affect the results since they are paginated. The links to export .tsv or .fasta files might be truncated because of this limit. You can increase it with:

.. code-block:: bash

    curl -XPUT "http://localhost:9200/haystack/_settings" \
         -d '{ "index" : { "max_result_window" : 500000 } }' \
         -H "Content-Type: application/json"
