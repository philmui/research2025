# Evolutionary Games with Multi-Agents

__Sat May  3 16:26:53 PDT 2025__
__Theodore Mui <theodoremui@gmail.com>

A number of key folders:

- data : this is where all game config & outputs go
- instance : this is the sqlite database storage
- tests : pytest for testing developing


## Initialization of project

To setup the project with all requisite libraries, type the following at the project toplevel:

```
uv sync
```


## Running the Evolutionary Games

Once the libraries are installed, type at the project toplevel:

```
./run.sh
```

If that has issues, type the following:

```
gunicorn --bind 0.0.0.0:8000 --reuse-port --reload main:app
```

If that creates problem, change the port from `8000` to `8001` (or any other port that is not being used by other processes).

If that fails, try this with the proper unused port: (in this case: 8000)

```
flask run --port=8000
```


## Test driven development

Before each checkin, run the following to ensure that all unit test passes

```
pytest
```
