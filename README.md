### Project description

**This application allows you to save/get/modify/delete documents with related text pieces entities in PostgreSQL database 
and index/search that saved document's text pieces in ElasticSearch.**


### Prerequisites

* Make sure that you have installed the latest versions of `python` and `pip` on your computer. 
  Also, you have to install [Docker](https://www.docker.com/) and [Docker Compose](https://docs.docker.com/compose/).


* This project by default uses [poetry](https://python-poetry.org/) for dependency and virtual environment management.
  Make sure to install it too.


* Make sure to provide all required environment variables (via `.env` file, `export` command, secrets, etc.) before running application.


### Development tools

1) For managing pre-commit hooks this project uses [pre-commit](https://pre-commit.com/).


2) For import sorting this project uses [isort](https://pycqa.github.io/isort/).


3) For code format checking this project uses [black](https://github.com/psf/black).


4) For code linting this project uses [flake8](https://flake8.pycqa.org/en/latest/) and [pylint](https://pypi.org/project/pylint/).


5) For type checking his project uses [mypy](https://github.com/python/mypy)


6) For create commits and lint commit messages this project uses [commitizen](https://commitizen-tools.github.io/commitizen/).
   Run `make commit` to use commitizen during commits.


### CI/CD

This project involves [github actions](https://docs.github.com/en/actions) to run all checks and unit-tests on `push` to remote repository.


### Make commands

There are lots of useful commands in `Makefile` included into this project's repo. Use `make <some_command>` syntax to run each of them. 
If your system doesn't support make commands - you may copy commands from `Makefile` directly into terminal.


### Database migrations

For managing migrations this project uses [alembic](https://alembic.sqlalchemy.org/en/latest/).

* Dockerfile already includes `alembic upgrade head` command to run all revision migrations, required by current version of application.


* Run `make upgrade` to manually upgrade database tables state. You could also manually upgrade to specific revision with `.py` script 
  (from `alembic/versions/`) by running:

  `alembic upgrade <revision id number>`


* You could also downgrade one revision down with `make downgrade` command, to specific revision - by running 
  `alembic downgrade <revision id number>`, or make full downgrade 
  to initial database state with:
  
  `make downgrade_full`


### Installation

1) To install all the required dependencies and set up a virtual environment run in the cloned repository directory use:

   `poetry install`

   You can also install project dependencies using `pip install -r requirements.txt`.


2) To config pre-commit hooks for code linting, code format checking and linting commit messages run in the cloned directory:

   `poetry run pre-commit install`


3) Build app image using

   `make build`


4) Run Docker containers using

   `make up`
    
   *Notes:`docker-compose.yml` specifies containers creation considering `healthchecks` in the following order:*
   
   **elasticsearch -> postgresql -> web.**


5) Stop and remove Docker containers using

    `make down`

    If you also want to remove log volume use `make down_volume`


### Running app

1) By default, web application will be accessible at http://localhost:8080, database available at http://localhost:5432 host 
   and elasticsearch available at http://localhost:9200. 


2) You can try all endpoints with SWAGGER documentation at http://localhost:8080/docs


4) Use resources with `/documents` prefix to create, read, update and delete data in `documents` database table. 
   ![/documents/all](https://user-images.githubusercontent.com/79688463/167624953-53c9b057-164d-400e-945e-ed5377a1eb8f.png)


6) To create document you should provide values for "document_name" (must be unique) and "author". Document entity also 
   has "document_id" - Primary key for database table, that returns as part of successful response. There will be also 
   ElasticSearch index created (if not exists) for which "index_name" equals to created "document_id".
   ![/documents/add](https://user-images.githubusercontent.com/79688463/167624959-bde64ca6-aed9-4a60-859b-656b358e47ea.png)


7) Use resources with `/text_pieces` prefix to create, read, update and delete data in `text_pieces` database table.
   ![/text_pieces/all](https://user-images.githubusercontent.com/79688463/167625084-a83784f9-3419-471d-945d-44987b162201.png)


8) Each request to create new text_piece should be provided with following data in request body:
   - `text` - required field with text data, 
   - `type` - required, either `title` or `paragraph`, 
   - `page` - required, integer number of page in document, which text piece belongs, 
   - `document_name` - required - link to document, which text piece belongs. Non-nullable ForeignKey to document, saved in `documents` table,
   - `meta_data` - optional field with JSON object as value, containing some metadata info about text piece.
   
   In succesfull response you will also get:
   - `piece_id` - Primary Key of new text piece in database table,
   - `indexed` - boolean value that show whether text piece was already indexed or not,
   - `size` - calculated length of `text` field of text piece.
   - `created_at` - timestamp for text piece object entity creation time in database. datetime.datetime() object.
   ![/text_pieces/add](https://user-images.githubusercontent.com/79688463/167624969-87eecad2-2d6d-41a8-bcd9-972280e1c0a0.png)  


9) Use resources with `/index` prefix to index and search for text pieces in Elasticsearch indices.
   ![/index/all](https://user-images.githubusercontent.com/79688463/167625090-542bf165-9d45-45f1-b420-d1fd8f623833.png)  


10) Request to `/index/{index_name}/index` resource will check that index with name (`document_id`) exists in ElasticSearch.
    If exists - all already saved text pieces in index will be removed and after that all text_pieces from PostgreSQL table, 
    associated with `document_id` will be indexed. For all text pieces to be indexed - `indexed` field's value in database table 
    will be updated and set to `true`.


11) Request to `/index/{index_name}/search` resource will search for text pieces in ElasticSearch index with name (`document_id`) if exists.
    Support pagination (`page_num` and `page_size`). If no pagination parameters specified - returns first 15 results. 
    In `filters` field you should specify list of filters, consists of `field`, `operator` and `values`. 
    Available text fields for search are:
    - `text` - support `match` operator that calculates score of relative matching and `eq` that finds exact match of requested string,
    - `document_name` - support `match` operator that calculates score of relative matching and `eq` that finds exact match of requested string,
    - `meta_data` - searches `eq` for values, 
    - `type` - has `eq` operator that accepts only existing text pieces types (`title` or `paragraph`, 
    - `indexed` - has `eq` and accepts only `true` or `false` values. 
    
    Available countable fields for search are:
    - `page`,
    - `size`, 
    - `created_at`. 

    This fields are compatible with operators: `eq`, `in` (array of possible values - will return result if at least one value matches) 
    and comparations: `gt` (greater than), `gte` (greater than or equals), `lt` (lower than), `lte` (lower than or equals).
    
    If no filters provided - returns all documents in index with `index_name`. 

    *Note: Order results by descending `score` value (if `match` is used) and then by `created_at` timestamp in ascending
    order.*
   
    Returns pagination parameters (including `page_num`, `page_size` and `total` - with total number of text pieces
    matching query) and `data` field with list of matching text pieces in response body.
   ![/index/search](https://user-images.githubusercontent.com/79688463/167624973-a27528c5-c0fb-4e1b-acb1-f828e97bb1a7.png)  


### Running tests.

* Use `make test` to locally run pytest checks during development.

* After all tests [coverage report](https://pytest-cov.readthedocs.io/en/latest/) will be also shown.

* Staged changes will be checked during commits via pre-commit hook.

* All checks and tests will run on code push to remote repository as part of github actions.
